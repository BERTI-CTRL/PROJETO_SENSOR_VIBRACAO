# gravador.py

## Resumo

`GravadorCSV` é a camada de escrita do histórico da sessão. Recebe listas de nove valores de [[coletor]], acumula lotes em memória e produz CSV. O fluxo normal o usa exclusivamente por [[gravador_worker]].

## Dependências, entrada e saída

Importa `csv`, `Path` e `datetime`. `salvar(linha)` recebe a ordem de nove campos da aquisição e escreve arquivo em `dados/`, no esquema descrito por [[esquema-csv]].

## `__init__()`: destino e cabeçalho

Sua interface declarada é:

```python
GravadorCSV(arquivo="dados/dados_aceleracao_giro.csv", tamanho_buffer=10000)
```

Mas o caminho efetivo é sempre montado pelo relógio:

```python
data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
self.arquivo = Path(f'dados/dados_aceleracao_giro-{data_hora}.csv')
```

Abre com modo `"a"`, `newline=""` e UTF-8. Se o arquivo não existia, escreve cabeçalho com `tempo_arduino_us`, `tempo_relogio_pc`, `contador`, `ax`, `ay`, `az`, `gx`, `gy`, `gz`.

> [!warning]
> O parâmetro `arquivo` é aceito mas ignorado. O diretório `dados/` também não é criado por este módulo e precisa existir no diretório de trabalho.

> [!warning]
> O sufixo temporal tem precisão de segundos; sessões iniciadas no mesmo segundo podem fazer append ao mesmo caminho.

## `salvar(linha)` e `fechar()`

`salvar()` adiciona à lista e descarrega ao atingir o tamanho de lote:

```python
if len(self.buffer) >= self.tamanho_buffer:
    self.writer.writerows(self.buffer)
    self.buffer.clear()
```

Isto reduz operações de disco. O default da classe é 10.000, enquanto [[gravador_worker]] normalmente passa 1.000. `fechar()` escreve o lote parcial restante, limpa a lista e fecha o descritor; é chamado no `finally` do worker após a sentinela enviada por [[manager]].

## Decisão arquitetural

Não possui lock porque o desenho dá ao worker a propriedade exclusiva do arquivo. Desacoplar escrita serial evita que I/O lento interfira na taxa de [[coletor]].

## Código explicado, na ordem do arquivo

### Imports, classe e construtor

```python
import csv
from pathlib import Path
from datetime import datetime
```

`csv` serializa linhas, `Path` representa o destino e `datetime` gera o sufixo temporal. `GravadorCSV.__init__()` recebe um parâmetro histórico `arquivo` e tamanho de buffer, não retorna valor e cria `self.buffer = []`, `self.tamanho_buffer` e o destino.

```python
arquivo_existe = self.arquivo.exists()
self.f = open(self.arquivo, mode="a", newline="", encoding="utf-8")
self.writer = csv.writer(self.f)
if not arquivo_existe:
    self.writer.writerow([...])
```

`exists()` define se cabeçalho será escrito. O modo append preserva conteúdo e `newline=""` evita linhas extras no Windows. A lista de cabeçalho é a saída contratual para ferramentas como [[plotar_csv]].

### `salvar(linha)`

Recebe uma linha de nove valores e não retorna valor. Primeiro a retém; somente no limiar escreve e libera:

```python
self.buffer.append(linha)
if len(self.buffer) >= self.tamanho_buffer:
    self.writer.writerows(self.buffer)
    self.buffer.clear()
```

`writerows` aceita o lote inteiro, que chega da fila controlada por [[gravador_worker]].

### `fechar()`

```python
if self.buffer:
    self.writer.writerows(self.buffer)
    self.buffer.clear()
self.f.close()
```

Não recebe nem retorna valores. O `if` trata o lote que não alcançou o limiar; o fechamento ocorre mesmo se não havia linha pendente. No fluxo normal o `finally` do worker chama esse método.

## Insights para outros projetos

- Escrita em lote reduz overhead, mas torna flush no encerramento obrigatório.
- Cabeçalho condicionado à existência combina com append.
- Ao tornar um destino configurável, documente caminho, diretório e colisões de nome.

## Resumo mental

É uma caixa de lote: junta amostras, grava de uma vez e, ao fechar, descarrega inclusive o lote incompleto.
#PROJETO_SENSOR_VIBRAÇÃO
