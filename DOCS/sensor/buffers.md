# buffers.py

## Resumo

`BufferSensores` é a janela circular em memória do pipeline: recebe amostras de [[coletor]], retém no máximo 10.000 por padrão e fornece dados recentes à [[janela]] e [[statistics]]. O histórico persistente pertence a [[gravador]] e [[gravador_worker]].

## Dependências, entrada e saída

Importa `Lock` de `threading` e `numpy as np`. A entrada de `adicionar(...)` são nove valores na ordem declarada pela constante:

```python
COLUNAS = [
    "tempo_arduino_us", "timestamp", "contador",
    "ax", "ay", "az", "gx", "gy", "gz"
]
```

`snapshot()` devolve um dicionário com essas nove chaves e arrays cronológicos; as propriedades devolvem cada coluna individualmente.

## Estrutura e estratégia

`__init__(tamanho=10000)` aloca `np.zeros((tamanho, 9), dtype=np.float64)`, `_index`, `_count` e um único mutex. `_index` é a próxima posição física; `_count` informa quantas amostras são logicamente válidas. Uma matriz contínua limita memória e evita um objeto Python por coluna/amostra.

> [!warning]
> Todos os campos, inclusive contador e tempos, são armazenados como `float64`; consumidores devem tratá-los como números, não como inteiros Python preservados literalmente.

## Métodos e propriedades

### `adicionar(...)`

Sob lock, grava uma linha e avança circularmente:

```python
self._dados[self._index] = [
    tempo_arduino_us, timestamp, contador,
    ax, ay, az, gx, gy, gz
]
self._index = (self._index + 1) % self.tamanho_maximo
```

`_count` cresce somente até a capacidade; depois disso, uma nova escrita substitui a mais antiga.

### `vazio()`, `tamanho_atual()` e `limpar()`

Os dois primeiros consultam `_count` sob lock. `limpar()` apenas reinicia `_index` e `_count`; a matriz é reutilizada e seus bytes antigos deixam de ser visíveis logicamente.

### `snapshot(quantidade=None)`

É a API indicada para UI e leitores concorrentes. Limita a solicitação a `_count`, copia os arrays e entrega ordem antigo → novo. Antes de encher, a faixa é contínua. Após o wrap-around, calcula o início a partir de `_index` e, quando atravessa o fim, usa:

```python
dados_cronologicos = np.concatenate([
    self._dados[inicio:, :],
    self._dados[:fim - self.tamanho_maximo, :]
])
```

> [!idea]
> Copiar sob lock e renderizar fora dele é um padrão reutilizável: a interface vê uma fotografia coerente sem manter o produtor bloqueado durante desenho.

> [!warning]
> O método não valida quantidade negativa. O contrato seguro é `None` ou inteiro não negativo.

### `_get_coluna_slice()` e propriedades de compatibilidade

`tempo_arduino_us`, `timestamp`, `contador`, `ax`, `ay`, `az`, `gx`, `gy` e `gz` chamam `_get_coluna_slice()`. Ele retorna coluna em ordem cronológica — fatia direta antes de encher e concatenação de `_index:` com `:_index` depois.

> [!warning]
> As propriedades podem retornar *views* do array interno; o lock já foi liberado quando elas são usadas. Para isolamento em concorrência, prefira `snapshot()`.

## Fluxo e decisões

`[[serial_reader]] → [[coletor]].buffer.adicionar(...) → snapshot → [[janela]] / [[statistics]]`. O buffer e a fila de CSV são independentes: uma amostra pode estar na tela mesmo se não coube na fila de persistência.

## Código explicado, na ordem do arquivo

### Imports e constante de colunas

```python
from threading import Lock
import numpy as np
```

`Lock` serializa acesso ao estado compartilhado; NumPy armazena todas as amostras em bloco. Logo após, a constante de classe `BufferSensores.COLUNAS` fixa os nove nomes que tanto `snapshot()` quanto os consumidores usam para indexar dados. Não é uma enumeração decorativa: sua ordem precisa coincidir com as nove posições atribuídas em `adicionar()`.

### Classe e construtor

```python
class BufferSensores:
    def __init__(self, tamanho=10000):
        self.tamanho_maximo = tamanho
        self._lock = Lock()
        self._dados = np.zeros((tamanho, 9), dtype=np.float64)
        self._index = 0
        self._count = 0
```

O construtor recebe a capacidade e não retorna valor. Ele prepara estado suficiente para uma escrita circular: `_index` diz onde a próxima linha irá, e `_count` diferencia posições escritas de posições ainda vazias. O tamanho padrão é usado por [[coletor]] sem argumento.

### Escrita e consultas simples

```python
with self._lock:
    self._dados[self._index] = [...]
    self._index = (self._index + 1) % self.tamanho_maximo
    if self._count < self.tamanho_maximo:
        self._count += 1
```

Esse é todo o fluxo de `adicionar()`: recebe nove argumentos, não retorna valor, grava uma linha e só aumenta a contagem enquanto ainda há capacidade. `vazio()` retorna `self._count == 0`; `tamanho_atual()` retorna `_count`. Ambos fazem isso dentro de `with self._lock`, evitando observar contador enquanto o produtor o altera.

### `snapshot()` e os ramos de ordenação

```python
if quantidade is None:
    quantidade = self._count
quantidade = min(quantidade, self._count)
if quantidade == 0:
    return {coluna: self._dados[0:0, i].copy()
            for i, coluna in enumerate(self.COLUNAS)}
```

O método recebe uma janela opcional e retorna dicionário de cópias, inclusive vazio com todas as chaves. Se `_count < tamanho_maximo`, `inicio = self._count - quantidade` e a fatia contínua `inicio:self._count` já está cronológica. Se cheio, começa em `(self._index - quantidade) % self.tamanho_maximo`; `fim <= tamanho_maximo` permite uma fatia única, caso contrário `np.concatenate` recompõe os dois lados do wrap. O `with self._lock` cobre cálculo e cópia.

### Limpeza, helper e propriedades

```python
def limpar(self):
    with self._lock:
        self._index = 0
        self._count = 0
```

`limpar()` não devolve valor e somente descarta a visão lógica. `_get_coluna_slice(coluna_idx)` recebe o índice da coluna e devolve vazio, fatia direta ou concatenação conforme vazio/não-cheio/cheio. Finalmente, cada `@property` como `ax` apenas executa `return self._get_coluna_slice(3)`. Essas propriedades existem para compatibilidade com acessos diretos de interface; não acrescentam cálculo de sensor.

## Insights para outros projetos

- Separe capacidade física e quantidade válida com ponteiro + contador.
- Trate explicitamente a ordem temporal depois do wrap-around.
- Ofereça snapshot copiado quando produtor e consumidor usam threads distintas.

## Resumo mental

É uma fita de 10.000 linhas: o coletor escreve continuamente, a cabeça volta ao início e `snapshot()` reorganiza a leitura em passado → presente.
#PROJETO_SENSOR_VIBRAÇÃO
