# manager.py — explicação completa, em ordem de linhas

O arquivo [sensor/manager.py](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\sensor\manager.py) é o coordenador do ciclo de vida da coleta. Ele não lê linhas seriais e não escreve CSV diretamente. Ele cria as estruturas necessárias, inicia as threads na ordem certa e encerra tudo sem perder o último lote de dados.

```text
Janela ou teste
      ↓
manager.iniciar()
      ↓
cria Queue → inicia GravadorWorker → inicia Coletor em thread
      ↓
manager.parar()
      ↓
para Coletor → espera thread → envia None → espera GravadorWorker
```

| Termo | Significado simples |
|---|---|
| manager | Objeto que coordena outras partes do programa. |
| sessão | Período entre iniciar e parar uma coleta. |
| thread | Linha de execução paralela. |
| Queue | Fila segura entre quem produz amostras e quem grava CSV. |
| produtor | Quem coloca itens na fila: o Coletor. |
| consumidor | Quem retira itens da fila: o GravadorWorker. |
| sentinela | Valor especial, aqui None, usado para pedir fim ao consumidor. |
| join | Espera uma thread terminar. |
| singleton | Uma única instância global compartilhada pelo projeto. |

## Linhas 1 a 9: imports

```python
from queue import Queue
from threading import Thread
from sensor.coletor import Coletor
from sensor.gravador_worker import GravadorWorker
```

Queue é a fila limitada usada para separar aquisição serial de gravação em disco. Thread cria a execução paralela do Coletor.

Coletor é o produtor de amostras: lê por meio de serial_reader, calcula métricas, atualiza o buffer e coloca linhas na fila. GravadorWorker é o consumidor: retira linhas da fila e as envia ao gravador CSV.

## Linhas 12 a 23: classe e estado inicial

```python
class SensorManager:
    def __init__(self):
        self.coletor = Coletor()
        self.thread = None
        self.fila_gravacao = None
        self.gravador_thread = None
```

SensorManager é o molde do coordenador. __init__ roda quando uma instância é criada.

```python
self.coletor = Coletor()
```

Cria um Coletor que será reutilizado entre sessões. Criar o objeto não abre a porta serial: a porta só é aberta quando executar roda dentro da thread.

```python
self.thread = None
self.fila_gravacao = None
self.gravador_thread = None
```

None significa que ainda não existe uma sessão ativa.

- thread guardará a thread que executa coletor.executar.
- fila_gravacao guardará a Queue da sessão.
- gravador_thread guardará a thread que consome e persiste as amostras.

## Linhas 25 a 28: impedir início duplicado

```python
def iniciar(self):
    if self.thread is not None and self.thread.is_alive():
        return
```

iniciar não recebe parâmetros. A condição tem duas partes:

```python
self.thread is not None
```

verifica se alguma thread já foi criada.

```python
self.thread.is_alive()
```

verifica se ela ainda está executando. and exige que ambas sejam verdadeiras. Nesse caso return encerra iniciar sem criar fila, worker ou segunda thread.

Isso evita dois coletores lendo a mesma porta COM ao mesmo tempo e dois CSVs consumindo a mesma sessão.

## Linhas 30 a 44: criar uma sessão e iniciar na ordem certa

```python
self.fila_gravacao = Queue(maxsize=50_000)
```

Cria uma fila com no máximo 50.000 amostras aguardando o disco. O underscore em 50_000 é apenas uma forma visual de escrever 50000 em Python.

A fila absorve uma diferença temporária de velocidade: o coletor pode receber dados mais depressa do que o arquivo é escrito durante alguns instantes.

```python
self.coletor.configurar_fila_gravacao(self.fila_gravacao)
```

Entrega a fila recém-criada ao Coletor. Dessa forma, quando uma amostra chegar, ele saberá para onde enviar sua cópia destinada ao CSV.

```python
self.gravador_thread = GravadorWorker(self.fila_gravacao)
self.gravador_thread.start()
```

A primeira linha cria o worker, mas ainda não o executa. A segunda inicia a thread. O worker abre o CSV e espera em fila.get até receber uma amostra.

Ele começa antes do Coletor porque é o consumidor. Assim, a primeira amostra produzida já terá uma fila e um consumidor disponíveis.

```python
self.thread = Thread(
    target=self.coletor.executar,
    name="coletor-serial",
    daemon=True,
)
self.thread.start()
```

Thread cria a execução paralela do produtor.

- target informa qual função deve rodar: coletor.executar.
- name dá um nome legível para diagnóstico.
- daemon=True informa que essa thread não deve, por si só, impedir o fim do processo.
- start realmente começa a execução; sem start a thread só existiria como objeto parado.

A ordem completa importa:

```text
1. criar fila
2. informar fila ao Coletor
3. criar e iniciar GravadorWorker
4. criar e iniciar thread do Coletor
```

## Linhas 46 a 71: encerrar uma sessão

```python
def parar(self):
    if self.thread is None:
        return False
```

parar devolve um valor booleano. Se não há thread, não havia sessão ativa para encerrar. False informa isso à interface.

```python
self.coletor.parar()
```

Não mata a thread à força. Coletor.parar muda sua flag rodando para False. serial_reader consulta essa flag por callback e encerra a leitura de forma cooperativa.

```python
if self.thread is not None:
    self.thread.join()
```

join espera a thread coletora terminar. Esta espera é fundamental: o Coletor pode ainda estar processando uma última amostra ou enfileirando uma linha. A sentinela não pode entrar antes de o produtor parar, pois o worker poderia sair e deixar uma amostra posterior sem consumidor.

```python
if self.fila_gravacao is not None:
    self.fila_gravacao.put(None)
```

Depois que não haverá novas linhas, None entra no fim da fila. Ele é a sentinela. GravadorWorker interpreta:

```python
if linha is None:
    break
```

Portanto, ele primeiro consome todas as amostras que estavam antes de None, depois sai do loop, descarrega o último lote e fecha o CSV.

```python
if self.gravador_thread is not None:
    self.gravador_thread.join()
```

O segundo join espera o worker terminar a gravação e o fechamento do arquivo. Quando esta linha termina, o CSV da sessão já recebeu o flush final.

```python
self.thread = None
self.gravador_thread = None
self.fila_gravacao = None
return True
```

As três referências são removidas para marcar a sessão como encerrada e permitir um novo iniciar. return True informa que uma sessão realmente foi encerrada.

O fluxo de parada é:

```text
Coletor.parar()
      ↓
thread do Coletor termina
      ↓
Queue recebe None
      ↓
GravadorWorker consome o restante e fecha CSV
      ↓
manager limpa referências e devolve True
```

## Linhas 73 a 76: propriedade buffer

```python
@property
def buffer(self):
    return self.coletor.buffer
```

@property permite usar o método como atributo:

```python
dados = manager.buffer.snapshot(150)
```

buffer não cria uma cópia nem cria outro BufferSensores. Ele devolve exatamente o buffer pertencente ao Coletor. A interface pode então pedir snapshots dele.

## Linhas 79 e 80: singleton global

```python
manager = SensorManager()
```

Essa linha cria uma instância global ao importar manager.py. Outros módulos usam:

```python
from sensor.manager import manager
```

Assim Janela, teste_manager e outros pontos de entrada falam com o mesmo coletor e o mesmo estado de sessão. A importação cria objetos, mas não inicia a serial: isso só ocorre após manager.iniciar().

## Relação com outros scripts

```text
realtime/janela.py  → chama manager.iniciar() e manager.parar()
sensor/teste_manager.py → chama os mesmos métodos no terminal
manager.py          → cria fila e threads
coletor.py          → produz amostras
gravador_worker.py  → consome amostras
gravador.py          → escreve CSV
buffers.py           → mantém dados recentes para a interface
```

## Situações importantes

Se iniciar for chamado enquanto a coleta já está ativa:

```python
if self.thread is not None and self.thread.is_alive():
    return
```

nada novo é criado. Isso protege contra cliques repetidos em Iniciar.

Se parar for chamado sem ter iniciado:

```python
if self.thread is None:
    return False
```

a interface pode perceber que não havia sessão, em vez de tentar abrir CSV antigo.

O Coletor é reutilizado, assim como seu buffer. As métricas da sessão são reiniciadas em coletor.executar, mas o buffer não é limpo automaticamente pelo manager. Por isso valores antigos podem permanecer visíveis até novas amostras os sobrescreverem ou até a interface chamar buffer.limpar().

## Resumo mental

SensorManager é o maestro. No início ele prepara a fila, acorda o gravador e só então libera o coletor. No fim ele silencia o coletor, espera a última amostra, manda None ao gravador e só termina quando o CSV foi fechado.
