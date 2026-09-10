# gravador.py — explicação completa, em ordem de linhas

O arquivo [sensor/gravador.py](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\sensor\gravador.py) é o responsável por escrever os dados da sessão em um arquivo CSV. Ele recebe amostras já prontas, junta várias em memória e grava um lote por vez.

Ele não lê a serial e não cria threads. GravadorWorker é quem o usa dentro de uma thread exclusiva de gravação.

```text
Coletor → Queue → GravadorWorker → GravadorCSV → dados/*.csv
```

| Termo | Significado simples |
|---|---|
| CSV | Arquivo de texto em tabela, com valores separados por vírgula. |
| cabeçalho | Primeira linha que informa o nome de cada coluna. |
| lote/batch | Grupo de várias amostras escritas em uma operação. |
| buffer | Lista temporária que junta o lote antes de salvar. |
| append | Modo de abertura que acrescenta conteúdo ao fim do arquivo. |
| flush final | Escrita das últimas linhas que ainda não formaram um lote completo. |
| Path | Objeto Python que representa um caminho de arquivo. |

Cada linha recebida deve ter nove valores nesta ordem:

```python
[
    tempo_arduino_us,
    timestamp,
    contador,
    ax, ay, az,
    gx, gy, gz,
]
```

## Linhas 3 a 8: imports

```python
import csv
from pathlib import Path
from datetime import datetime
```

csv é a biblioteca padrão que escreve valores com vírgulas e aspas quando necessário. Path representa o caminho do arquivo de uma forma que funciona em diferentes sistemas. datetime fornece data e hora para dar um nome diferente a cada sessão.

## Linhas 11 a 19: classe e assinatura do construtor

```python
class GravadorCSV:
    def __init__(
        self,
        arquivo="dados/dados_aceleracao_giro.csv",
        tamanho_buffer=10000
    ):
```

GravadorCSV é o molde do objeto que guarda estado de um CSV aberto.

arquivo aparece como parâmetro, mas a implementação atual não o usa como destino final. O destino é montado com data e hora algumas linhas depois.

tamanho_buffer define quantas linhas ficam na lista antes de writerows gravar um lote. O padrão da classe é 10.000; GravadorWorker normalmente passa 1.000 ao criar o objeto.

## Linhas 20 a 27: buffer e nome do arquivo

```python
self.buffer = []
self.tamanho_buffer = tamanho_buffer
```

self.buffer cria uma lista vazia. Ela não é o BufferSensores usado pela interface; é uma lista privada usada exclusivamente para preparar gravações em lote.

self.tamanho_buffer guarda o limite recebido, para ser consultado em salvar.

```python
data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
self.arquivo = Path(
    f"dados/dados_aceleracao_giro-{data_hora}.csv"
)
```

datetime.now obtém data e hora atuais. strftime transforma-as em texto. Por exemplo:

```text
2026-09-09_16-48-06
```

A f-string insere esse texto no nome. Path cria o caminho:

```text
dados/dados_aceleracao_giro-2026-09-09_16-48-06.csv
```

O parâmetro arquivo continua ignorado. A pasta dados também precisa existir antes da criação; este arquivo não chama mkdir para criá-la.

## Linhas 29 a 41: abrir o CSV

```python
arquivo_existe = self.arquivo.exists()
```

exists devolve True se já há um arquivo naquele caminho e False caso contrário. Essa informação decide se o cabeçalho precisa ser escrito.

```python
self.f = open(
    self.arquivo,
    mode="a",
    newline="",
    encoding="utf-8"
)
```

open abre o arquivo e o resultado é guardado em self.f.

- mode="a" significa append: acrescentar no fim, sem apagar conteúdo existente.
- newline="" é a configuração recomendada para csv no Windows, evitando linhas vazias extras.
- encoding="utf-8" define a codificação do texto.

Se duas sessões gerarem exatamente o mesmo nome no mesmo segundo, append pode juntar dados no mesmo arquivo. Normalmente os nomes são diferentes porque incluem data e hora.

```python
self.writer = csv.writer(self.f)
```

csv.writer cria o objeto capaz de transformar listas Python em linhas CSV dentro do arquivo aberto.

## Linhas 43 a 56: cabeçalho

```python
if not arquivo_existe:
    self.writer.writerow([
        "tempo_arduino_us",
        "tempo_relogio_pc",
        "contador",
        "ax",
        "ay",
        "az",
        "gx",
        "gy",
        "gz"
    ])
```

not inverte a condição. Se arquivo_existe é False, not arquivo_existe é True e o cabeçalho é escrito.

writerow escreve uma linha. A lista declara as nove colunas:

| Coluna | Origem |
|---|---|
| tempo_arduino_us | micros do Arduino; usado para análise temporal. |
| tempo_relogio_pc | perf_counter registrado pelo leitor serial. |
| contador | número sequencial do firmware. |
| ax, ay, az | aceleração nos três eixos. |
| gx, gy, gz | velocidade angular nos três eixos. |

O cabeçalho deve manter a mesma ordem da lista criada em coletor.py. Ferramentas como plotar_csv identificam colunas por esses nomes.

## Linhas 58 a 68: salvar uma amostra

```python
def salvar(self, linha):
    self.buffer.append(linha)
```

salvar recebe uma lista de nove valores e adiciona essa lista ao buffer de escrita. append não grava disco imediatamente.

```python
if len(self.buffer) >= self.tamanho_buffer:
    self.writer.writerows(self.buffer)
    self.buffer.clear()
```

len conta quantas linhas estão esperando. Quando há pelo menos tamanho_buffer:

1. writerows escreve todas as listas do buffer em sequência;
2. clear remove as referências da lista já salva.

Exemplo com tamanho_buffer igual a 3:

```text
salvar(A) → buffer: [A]
salvar(B) → buffer: [A, B]
salvar(C) → writerows([A, B, C]) → buffer: []
```

Gravar em lote reduz chamadas ao sistema de arquivos. Isso é mais eficiente que escrever a cada amostra e ajuda a não atrapalhar a aquisição serial.

## Linhas 70 a 80: fechar corretamente

```python
def fechar(self):
    if self.buffer:
        self.writer.writerows(self.buffer)
        self.buffer.clear()
    self.f.close()
```

fechar precisa ser chamado ao fim da sessão. A condição:

```python
if self.buffer:
```

é verdadeira quando a lista não está vazia. Ela cuida do último lote parcial.

Exemplo: se o lote precisa de 1.000 linhas e a sessão termina após 1.234:

```text
1.000 linhas → gravadas por salvar()
234 linhas   → ainda estão no buffer
fechar()     → grava as 234 restantes
```

Depois, self.f.close fecha o descritor do arquivo. Isso libera o arquivo e garante que a escrita do Python seja finalizada.

No fluxo normal, GravadorWorker chama fechar dentro de seu bloco finally. Portanto a chamada acontece tanto quando recebe a sentinela None quanto se ocorrer uma falha no worker depois de o arquivo ter sido aberto.

## Como este arquivo se relaciona com os outros

```python
# gravador_worker.py, ideia central
gravador = GravadorCSV(tamanho_buffer=1000)
gravador.salvar(linha)
# ...
gravador.fechar()
```

GravadorWorker é o único consumidor normal de GravadorCSV. Ele recebe as listas do Coletor pela Queue e chama salvar para cada uma.

```text
manager.py          cria Queue e inicia worker
coletor.py          tenta enfileirar uma cópia de cada amostra
gravador_worker.py  consome Queue e usa GravadorCSV
gravador.py          escreve o arquivo e seu cabeçalho
plotar_csv.py        lê o arquivo pronto para análise
```

GravadorCSV não usa Lock porque somente a thread do worker deve acessar a instância e seu arquivo. A Queue protege a troca de dados entre a thread do coletor e a thread de gravação.

## Resumo mental

GravadorCSV é uma caixa de lote para o CSV. Ele cria um nome com data e hora, abre o arquivo, escreve cabeçalho quando necessário, junta amostras temporariamente, grava quando o lote enche e grava o resto antes de fechar.
