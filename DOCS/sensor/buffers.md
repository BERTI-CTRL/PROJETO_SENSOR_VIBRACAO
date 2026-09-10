O arquivo [`sensor/buffers.py`](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\sensor\buffers.py) é a memória de curto prazo do sistema. Ele recebe as amostras que o `Coletor` acabou de ler e mantém somente as mais recentes para a interface mostrar gráficos e calcular estatísticas.

Ele não lê a porta serial, não calcula frequência e não grava arquivos. Sua única responsabilidade é guardar amostras em memória de forma rápida e segura enquanto mais de uma parte do programa trabalha ao mesmo tempo.

```text
Arduino → serial_reader.py → coletor.py → BufferSensores
                                              │
                           ┌──────────────────┴──────────────────┐
                           ↓                                     ↓
                    realtime/janela.py                    estatísticas
                     mostra gráficos                    média, RMS etc.
```

Imagine uma fita com 10.000 espaços. Cada leitura ocupa um espaço. Quando chega ao último, a próxima leitura volta ao primeiro espaço e substitui a leitura mais antiga. Esse é um **buffer circular**: a memória tem tamanho fixo, mas sempre contém os dados mais recentes.

Os termos mais importantes:

| Termo | Significado simples |
|---|---|
| **amostra** | Uma leitura completa: dois tempos, contador e seis eixos do sensor. |
| **array/matriz** | Uma tabela numérica. Aqui, cada linha é uma amostra e cada coluna é um tipo de valor. |
| **NumPy** | Biblioteca Python para trabalhar com grandes conjuntos de números com eficiência. |
| **buffer circular** | Memória que volta ao começo quando chega ao fim, substituindo os dados antigos. |
| **índice** | Número que identifica uma posição. Python começa em zero. |
| **thread** | Parte do programa que pode executar ao mesmo tempo que outra. |
| **Lock** | Uma trava: enquanto alguém escreve, outra thread espera antes de ler a estrutura interna. |
| **snapshot** | Uma cópia consistente dos dados em um instante, como uma fotografia. |
| **view** | Uma visualização que ainda compartilha memória com o array original. |
| **cópia** | Um novo array, independente do original. |
| **wrap-around** | A volta do fim físico do array para a posição zero. |

Cada amostra tem nove valores, sempre nesta ordem:

```python
[
    tempo_arduino_us,
    timestamp,
    contador,
    ax, ay, az,
    gx, gy, gz,
]
```

- `tempo_arduino_us`: tempo do Arduino, em microssegundos;
- `timestamp`: instante em que o PC recebeu a linha;
- `contador`: número sequencial enviado pelo firmware;
- `ax`, `ay`, `az`: acelerações nos três eixos;
- `gx`, `gy`, `gz`: velocidades angulares nos três eixos.

## Linhas 1 a 4: importações

```python
from threading import Lock
import numpy as np
```

`import` traz recursos de outras bibliotecas.

```python
from threading import Lock
```

Importa `Lock`, a trava usada para coordenar acesso entre threads. Enquanto o coletor grava uma amostra, a interface não deve ler a mesma estrutura no meio da escrita.

```python
import numpy as np
```

Importa a biblioteca NumPy e dá a ela o apelido `np`. Assim, o código escreve `np.zeros(...)` e `np.concatenate(...)` em vez de `numpy.zeros(...)`.

## Linhas 7 a 21: classe e nomes das colunas

```python
class BufferSensores:
```

Cria a classe que representa o buffer. Um objeto é criado assim:

```python
buffer = BufferSensores()
```

A documentação entre aspas triplas explica a intenção da classe:

```python
"""Buffer circular thread-safe usando um único array 2D do NumPy.

Otimizado para alta performance em aquisição de dados do MPU6050.
- Usa um único array 2D para armazenar todos os dados
- Operações de snapshot são extremamente rápidas (cópia de arrays NumPy)
- Thread-safe com Lock para sincronizar acesso
- Mantém 100% compatibilidade com código existente (atributos ax, ay, az, etc.)
"""
```

`thread-safe` significa que as operações internas importantes usam uma trava. O arquivo guarda os dados em um único array de duas dimensões: linhas são amostras; colunas são valores daquela amostra.

```python
COLUNAS = [
    "tempo_arduino_us", "timestamp", "contador",
    "ax", "ay", "az", "gx", "gy", "gz"
]
```

`COLUNAS` pertence à classe, por isso é o mesmo contrato para todos os buffers. A posição de cada nome é importante:

```text
índice  0                  1            2          3   4   5   6   7   8
nome    tempo_arduino_us   timestamp    contador   ax  ay  az  gx  gy  gz
```

Essa mesma ordem é usada por `adicionar(...)`, por `snapshot()` e pelas propriedades como `buffer.ax`. Se a ordem fosse modificada só em uma dessas partes, os dados poderiam ser trocados silenciosamente.

## Linhas 23 a 36: criação do buffer

```python
def __init__(self, tamanho=10000):
```

`__init__` roda automaticamente ao criar `BufferSensores()`. O valor padrão é 10.000:

```python
buffer = BufferSensores()             # capacidade para 10.000 amostras
buffer_pequeno = BufferSensores(500)  # capacidade para 500 amostras
```

```python
self.tamanho_maximo = tamanho
```

Guarda a capacidade escolhida. Esse valor não é a quantidade atual de amostras; é o limite máximo.

```python
self._lock = Lock()
```

Cria uma trava. O prefixo `_` indica que é um detalhe interno: código externo deve usar métodos como `snapshot()`, e não manipular a trava diretamente.

```python
self._dados = np.zeros((tamanho, 9), dtype=np.float64)
```

Cria a matriz principal.

```python
np.zeros((tamanho, 9), dtype=np.float64)
```

Significa:

- `tamanho` linhas, uma para cada amostra guardada;
- `9` colunas, uma para cada valor da amostra;
- `zeros` no começo, apenas para reservar memória;
- `float64`, número de ponto flutuante de 64 bits.

Os zeros iniciais não são leituras reais. O atributo `_count` é quem informa quantas linhas já foram preenchidas por amostras válidas.

```python
self._index = 0
self._count = 0
```

`_index` aponta para a posição física da próxima escrita. `_count` informa quantas posições já contêm dados válidos.

No começo:

```text
_index = 0     próxima escrita será na primeira linha
_count = 0     nenhuma leitura válida foi armazenada
```

Depois de três amostras em um buffer de cinco posições:

```text
posição física:  0   1   2   3   4
conteúdo:        A   B   C   -   -
_index = 3
_count = 3
```

## Linhas 38 a 50: adicionar uma amostra

```python
def adicionar(self, tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz):
```

Este método recebe uma amostra completa. O `Coletor` o chama uma vez para cada linha válida recebida da serial:

```python
self.buffer.adicionar(
    tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz
)
```

```python
with self._lock:
```

`with` adquire a trava ao entrar no bloco e a libera automaticamente ao sair. Assim, as linhas internas são tratadas como uma operação única do ponto de vista das outras threads.

```python
self._dados[self._index] = [
    tempo_arduino_us, timestamp, contador,
    ax, ay, az, gx, gy, gz
]
```

Seleciona a linha apontada por `_index` e preenche suas nove colunas. Por exemplo, se `_index == 3`, a quarta linha física receberá a nova amostra.

```python
self._index = (self._index + 1) % self.tamanho_maximo
```

Depois de gravar, move o ponteiro para a próxima posição. O símbolo `%` calcula o resto da divisão e faz a volta ao início.

Para capacidade cinco:

```python
(3 + 1) % 5  # 4
(4 + 1) % 5  # 0
```

Assim, depois de escrever na última posição, a próxima escrita ocorre na primeira.

```python
if self._count < self.tamanho_maximo:
    self._count += 1
```

Enquanto o buffer ainda não está cheio, aumenta a quantidade de amostras válidas. Depois de chegar ao limite, `_count` para de crescer. O buffer continua recebendo dados, mas cada nova amostra substitui a mais antiga.

Com capacidade cinco:

```text
após A, B, C, D, E: _count = 5
após F:             _count = 5, mas A foi substituída
após G:             _count = 5, mas B foi substituída
```

## Linhas 52 a 62: consultas rápidas

```python
def vazio(self):
    with self._lock:
        return self._count == 0
```

`vazio()` responde `True` se nenhuma amostra válida foi adicionada e `False` em qualquer outro caso. O operador `==` compara valores.

```python
def tamanho_atual(self):
    with self._lock:
        return self._count
```

`tamanho_atual()` devolve quantas amostras o buffer mantém agora: de zero até `tamanho_maximo`. Após encher, ele permanece no máximo; não indica o total histórico de leituras desde o começo do ensaio.

## Linhas 64 a 109: snapshot, a forma recomendada de ler dados

```python
def snapshot(self, quantidade=None):
```

Um snapshot é a forma mais segura de pedir dados à interface. Ele devolve um dicionário: cada chave é uma coluna e cada valor é um array independente, em ordem cronológica, do mais antigo para o mais novo.

```python
dados = buffer.snapshot(150)
eixo_x = dados["ax"]
contadores = dados["contador"]
```

```python
if quantidade is None:
    quantidade = self._count
```

`None` significa que não foi definido limite. Nesse caso, retorna todas as amostras que ainda estão no buffer.

```python
quantidade = min(quantidade, self._count)
```

Impede o pedido de mais pontos que os existentes. Se o buffer contém 20 amostras:

```python
buffer.snapshot(150)  # devolve 20, não 150
```

```python
if quantidade == 0:
    return {
        coluna: self._dados[0:0, i].copy()
        for i, coluna in enumerate(self.COLUNAS)
    }
```

Mesmo vazio, o método devolve as nove chaves. `enumerate(self.COLUNAS)` gera pares como:

```python
(0, "tempo_arduino_us")
(3, "ax")
(8, "gz")
```

`self._dados[0:0, i]` é uma fatia vazia da coluna `i`. `.copy()` cria um array independente. Assim, a interface pode acessar `dados["ax"]` sem falhar apenas porque a coleta ainda não começou.

### Buffer ainda não cheio

```python
if self._count < self.tamanho_maximo:
    inicio = self._count - quantidade
    return {
        coluna: self._dados[inicio:self._count, i].copy()
        for i, coluna in enumerate(self.COLUNAS)
    }
```

Antes da primeira volta, as amostras estão organizadas fisicamente em ordem temporal. Se existem 80 leituras e foram pedidas 20:

```python
inicio = 80 - 20  # 60
```

A fatia `60:80` devolve as 20 últimas. Em Python, o limite final da fatia não é incluído.

Cada valor recebe `.copy()`. Isso é essencial: uma fatia NumPy pode ser uma view, isto é, continuar apontando para a memória interna. A cópia permite que a interface desenhe com tranquilidade depois que o coletor voltar a escrever no buffer.

### Buffer cheio: reconstruir a ordem temporal

```python
inicio = (self._index - quantidade) % self.tamanho_maximo
fim = inicio + quantidade
```

Quando o buffer está cheio, a ordem física não é mais a ordem temporal. `_index` aponta para onde a próxima amostra será gravada, portanto para a posição da amostra mais antiga que ainda existe.

Exemplo: capacidade cinco, após receber `A, B, C, D, E, F, G`:

```text
posição física:  0   1   2   3   4
conteúdo:        F   G   C   D   E
_index = 2
ordem temporal:  C → D → E → F → G
```

```python
if fim <= self.tamanho_maximo:
    dados_cronologicos = self._dados[inicio:fim, :]
```

Se o recorte não ultrapassa o fim físico do array, uma única fatia resolve. O segundo `:` significa “todas as nove colunas”.

```python
else:
    dados_cronologicos = np.concatenate([
        self._dados[inicio:, :],
        self._dados[:fim - self.tamanho_maximo, :]
    ])
```

Se o recorte atravessa o fim, ele é dividido em dois pedaços:

1. de `inicio` até a última linha física;
2. da primeira linha física até o restante pedido.

`np.concatenate(...)` une os dois na ordem correta.

```python
return {
    coluna: dados_cronologicos[:, i].copy()
    for i, coluna in enumerate(self.COLUNAS)
}
```

`dados_cronologicos[:, i]` significa “todas as linhas da coluna `i`”. O retorno final preserva a ordem cronológica e devolve cópias independentes.

## Linhas 111 a 117: limpeza lógica

```python
def limpar(self):
    with self._lock:
        self._index = 0
        self._count = 0
```

`limpar()` faz o buffer parecer vazio imediatamente.

```python
self._index = 0
```

Faz a próxima escrita voltar para a primeira posição física.

```python
self._count = 0
```

Marca que não existe nenhuma amostra válida para a API. O código não preenche a matriz inteira com zeros novamente; por isso a limpeza é rápida. Os bytes antigos podem continuar na memória, mas `snapshot()` deixa de expô-los.

Essa limpeza não altera CSVs que já foram gravados. Ela só apaga o histórico visual em memória.

## Linhas 123 a 145: auxiliar para ler uma coluna

```python
def _get_coluna_slice(self, coluna_idx):
```

É um método interno. Recebe o índice de uma coluna e devolve todos os valores daquela coluna em ordem cronológica.

```python
if self._count == 0:
    return self._dados[0:0, coluna_idx]
```

Se não há histórico, devolve uma fatia vazia da coluna solicitada.

```python
if self._count < self.tamanho_maximo:
    return self._dados[:self._count, coluna_idx]
```

Antes de encher, as linhas válidas ficam juntas desde a posição zero. A fatia já sai em ordem cronológica.

```python
return np.concatenate([
    self._dados[self._index:, coluna_idx],
    self._dados[:self._index, coluna_idx]
])
```

Depois de encher, junta os dois trechos da coluna para reconstruir a sequência temporal.

Há uma diferença importante em relação a `snapshot()`: quando o buffer ainda não encheu, esse método devolve uma view, não uma cópia. Após a trava ser liberada, o coletor pode alterar a memória compartilhada. Por isso, para gráficos, estatísticas e outras leituras concorrentes, prefira:

```python
dados = buffer.snapshot(150)
```

## Linhas 151 a 194: propriedades públicas

```python
@property
def tempo_arduino_us(self):
    return self._get_coluna_slice(0)

@property
def timestamp(self):
    return self._get_coluna_slice(1)

@property
def contador(self):
    return self._get_coluna_slice(2)
```

`@property` permite acessar um método como se fosse atributo:

```python
tempos = buffer.tempo_arduino_us
ids = buffer.contador
```

Internamente, essas propriedades chamam o auxiliar usando os índices 0, 1 e 2.

```python
@property
def ax(self):
    return self._get_coluna_slice(3)

@property
def ay(self):
    return self._get_coluna_slice(4)

@property
def az(self):
    return self._get_coluna_slice(5)
```

Essas propriedades expõem os eixos de aceleração:

```python
aceleracao_x = buffer.ax
aceleracao_y = buffer.ay
aceleracao_z = buffer.az
```

```python
@property
def gx(self):
    return self._get_coluna_slice(6)

@property
def gy(self):
    return self._get_coluna_slice(7)

@property
def gz(self):
    return self._get_coluna_slice(8)
```

As três últimas propriedades expõem as velocidades angulares dos eixos X, Y e Z.

As propriedades existem para compatibilidade com código já escrito, como `buffer.ax`. Quando for necessário ler várias séries juntas, um único `snapshot()` é mais eficiente e mais seguro do que chamar uma propriedade para cada eixo.

## Como o BufferSensores se relaciona com os outros scripts

```python
# sensor/coletor.py
self.buffer.adicionar(
    tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz
)
```

O coletor é o produtor: ele coloca cada leitura no buffer.

```python
# realtime/janela.py, ideia de uso
dados = manager.buffer.snapshot(150)
```

A interface é consumidora: ela pede somente uma janela pequena e recente para não redesenhar milhares de pontos a cada atualização.

```python
# sensor/manager.py
@property
def buffer(self):
    return self.coletor.buffer
```

O manager apenas expõe o mesmo buffer que pertence ao coletor. Ele não cria uma cópia nem um segundo buffer.

O CSV segue por outro caminho:

```text
coletor.py → fila de gravação → gravador_worker.py → gravador.py → dados/*.csv
```

Assim, a interface pode continuar recebendo dados recentes mesmo que a gravação esteja lenta ou desativada.

## Resumo mental

`BufferSensores` é uma tabela circular com nove colunas. `_index` aponta para a próxima escrita e `_count` informa quantas amostras ainda são válidas. Quando o array enche, a leitura mais antiga é substituída. `snapshot()` reorganiza um recorte em ordem passado → presente e devolve cópias seguras para a interface e as estatísticas.
