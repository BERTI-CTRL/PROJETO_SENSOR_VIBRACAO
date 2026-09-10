# gravador_worker.py — explicação completa, em ordem de linhas

O arquivo [sensor/gravador_worker.py](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\sensor\gravador_worker.py) cria a thread dedicada ao disco. Ela espera amostras na fila, passa cada uma para GravadorCSV e encerra somente depois de receber a sentinela None.

Separar essa thread do Coletor é importante: o disco pode ficar lento, mas a leitura serial deve continuar o mais livre possível.

```text
Coletor produz linha → Queue → GravadorWorker consome → GravadorCSV grava CSV
                                  ↑
                                None encerra
```

| Termo | Significado simples |
|---|---|
| worker | Thread que executa trabalho especializado em segundo plano. |
| Queue.get | Espera e retira o próximo item da fila. |
| FIFO | Primeiro item que entrou é o primeiro que sai. |
| sentinela | Valor especial usado para sinalizar fim; aqui é None. |
| task_done | Marca um item retirado da fila como concluído. |
| try/except/finally | Estrutura para tentar, tratar erro e sempre executar limpeza. |
| daemon | Thread que não impede sozinha o processo de terminar. |

## Linhas 1 a 15: docstring, import e classe

```python
"""Thread dedicada para persistir as amostras no CSV.

Esta thread nunca acessa a porta serial. Assim, uma escrita lenta no disco
nao interrompe a leitura feita pelo Coletor.
"""
from threading import Thread
from sensor.gravador import GravadorCSV

class GravadorWorker(Thread):
    """Consome linhas da fila e as grava em lotes no CSV."""
```

A docstring descreve o objetivo do módulo. Thread é a classe-base do Python para trabalho paralelo. GravadorCSV é a classe que abre, escreve e fecha o arquivo.

GravadorWorker(Thread) significa que GravadorWorker herda o comportamento de uma Thread. Por isso ele possui start e join. O código do trabalho fica no método run.

## Linhas 17 a 25: construtor

```python
def __init__(self, fila, tamanho_buffer=1000):
    super().__init__(name="gravador-csv", daemon=True)
    self.fila = fila
    self.tamanho_buffer = tamanho_buffer
    self.erro = None
```

fila é a Queue criada pelo manager e compartilhada com o Coletor. tamanho_buffer é a quantidade de linhas que GravadorCSV acumula antes de escrever um lote; aqui o padrão é 1.000.

super().__init__ chama o construtor da classe Thread:

```python
name="gravador-csv"
```

dá um nome legível à thread em diagnósticos.

```python
daemon=True
```

marca a thread como daemon. Mesmo assim o manager chama join no encerramento normal, pois join é o que garante esperar o flush final do CSV.

self.fila guarda a fila recebida. self.tamanho_buffer será passado ao GravadorCSV. self.erro começa como None e poderá guardar uma exceção ocorrida na thread.

## Linhas 27 a 33: começo de run

```python
def run(self):
    gravador = None
    try:
        gravador = GravadorCSV(
            tamanho_buffer=self.tamanho_buffer
        )
```

run é chamado automaticamente por start:

```python
worker = GravadorWorker(fila)
worker.start()  # start cria a thread e executa run dentro dela
```

gravador começa como None. Isso permite que o finally saiba se o CSV foi aberto com sucesso. Dentro do try, GravadorCSV cria o arquivo e escreve cabeçalho quando necessário.

## Linhas 35 a 47: esperar, salvar e reconhecer None

```python
while True:
    linha = self.fila.get()
```

while True cria um loop sem fim até break. fila.get bloqueia a thread de modo eficiente enquanto a fila está vazia. Não há polling nem sleep: a thread dorme até o Coletor inserir algo.

```python
try:
    if linha is None:
        break
    gravador.salvar(linha)
finally:
    self.fila.task_done()
```

Cada item retirado precisa receber task_done, inclusive None. finally garante isso mesmo se gravador.salvar falhar.

Se linha for None, break sai do while. None não é gravada como CSV: ela significa “não haverá mais linhas”.

Se linha for uma lista real de nove valores, salvar a coloca no buffer de lote do GravadorCSV. Quando o lote enche, GravadorCSV escreve várias linhas de uma vez.

A ordem FIFO garante o flush correto:

```text
amostras A, B, C entram na fila
None entra depois
worker salva A, B, C
worker lê None e encerra
finally fecha o lote parcial
```

O manager só envia None depois de esperar o Coletor terminar. Assim, o worker não encerra antes de a última amostra ser enfileirada.

## Linhas 49 a 53: erro do trabalho principal

```python
except Exception as erro:
    self.erro = erro
    print(f"[Gravador] Erro: {erro}")
```

Exception captura erros que acontecerem ao criar GravadorCSV, chamar get ou salvar uma linha. A exceção fica guardada em self.erro para inspeção externa e também aparece no terminal.

Sem esse bloco, uma exceção numa thread pode ser mais difícil de perceber, pois ela não volta automaticamente para o código que chamou start.

## Linhas 54 a 64: fechamento garantido

```python
finally:
    if gravador is not None:
        try:
            gravador.fechar()
        except Exception as erro:
            self.erro = self.erro or erro
            print(f"[Gravador] Erro ao fechar CSV: {erro}")
```

finally sempre roda ao sair do try principal: por None, erro ou fim inesperado.

O if evita chamar fechar se GravadorCSV não chegou a ser criado. Quando existe gravador, fechar grava o último lote incompleto e fecha o arquivo.

self.erro = self.erro or erro preserva o primeiro erro:

```python
self.erro or erro
```

se self.erro já contém uma exceção anterior, ela continua sendo usada. Se ainda é None, a falha do fechamento se torna o erro registrado.

## Como manager controla esta thread

```python
# manager.py
self.gravador_thread = GravadorWorker(self.fila_gravacao)
self.gravador_thread.start()

# durante a parada, após esperar o Coletor:
self.fila_gravacao.put(None)
self.gravador_thread.join()
```

start inicia o worker antes do produtor serial. put(None) envia a sentinela depois que o produtor parou. join bloqueia o manager até run terminar, inclusive o método gravador.fechar.

## Diferença entre GravadorWorker e GravadorCSV

| Arquivo | Responsabilidade |
|---|---|
| gravador_worker.py | Thread, Queue, sentinela, erro e coordenação de consumo. |
| gravador.py | Nome do arquivo, cabeçalho, buffer de lote, writerows e close. |

## Resumo mental

GravadorWorker é o funcionário da fila. Ele fica esperando trabalho, salva cada amostra no CSV sem acessar a serial, entende None como ordem de encerramento e tenta fechar o arquivo em todos os caminhos possíveis.
