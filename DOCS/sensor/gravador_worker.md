# gravador_worker.py

## Resumo

`GravadorWorker` é a thread que consome a fila de persistência e delega arquivo a [[gravador]]. Separá-la de [[coletor]] evita que uma escrita lenta bloqueie a porta serial.

## Dependências, entrada e saída

Herda de `threading.Thread` e importa `GravadorCSV`. Entrada: fila com listas de nove campos ou `None`. Saída: CSV e atributo público `erro` com exceção capturada.

```python
GravadorWorker(fila, tamanho_buffer=1000)
```

O construtor cria thread `gravador-csv`, `daemon=True`, guarda fila/lote e inicia `erro=None`.

> [!idea]
> Daemon impede uma thread esquecida de manter o processo vivo, mas não assegura integridade de arquivo. O `join()` de [[manager]] é que assegura o caminho normal de flush.

## `run()` em ordem

O gravador nasce dentro da thread:

```python
gravador = GravadorCSV(tamanho_buffer=self.tamanho_buffer)
```

Depois a thread bloqueia sem polling em `fila.get()`. O bloco central é:

```python
linha = self.fila.get()
try:
    if linha is None:
        break
    gravador.salvar(linha)
finally:
    self.fila.task_done()
```

`None` é sentinela, não linha CSV. O `finally` externo chama `gravador.fechar()` sempre que o gravador chegou a ser construído, descarregando o lote parcial.

## Erros e relação com o encerramento

Erros de abertura/consumo/gravação ficam em `self.erro` e vão ao console. Se fechar também falha, `self.erro = self.erro or erro` preserva a primeira causa. [[manager]] interrompe [[coletor]], espera sua thread, envia a sentinela e espera este worker; veja [[threads-e-encerramento]].

> [!warning]
> [[manager]] não consulta `gravador_thread.erro`. Uma falha pode ficar somente no console/atributo; o coletor continuará tentando enfileirar até a fila saturar.

> [!warning]
> Cada item recebe `task_done()`, mas o manager não chama `Queue.join()`; a espera efetiva é `join()` da thread após a sentinela.

## Código explicado, na ordem do arquivo

### Imports, classe e construtor

```python
from threading import Thread
from sensor.gravador import GravadorCSV
```

`GravadorWorker(Thread)` recebe `fila` e `tamanho_buffer=1000`. O construtor chama a base com nome e daemon:

```python
super().__init__(name="gravador-csv", daemon=True)
self.fila = fila
self.tamanho_buffer = tamanho_buffer
self.erro = None
```

Não retorna valor. Guarda a Queue já criada por [[manager]], o lote que será encaminhado a `GravadorCSV` e espaço para diagnóstico externo.

### `run()`: criação e consumo

```python
def run(self):
    gravador = None
    try:
        gravador = GravadorCSV(tamanho_buffer=self.tamanho_buffer)
        while True:
            linha = self.fila.get()
```

`run()` é chamado por `start()` e não pelo chamador diretamente. `gravador = None` permite ao `finally` saber se abriu o arquivo. `get()` bloqueia até haver trabalho, sem sleep/polling.

### Sentinela, persistência e contabilidade

```python
try:
    if linha is None:
        break
    gravador.salvar(linha)
finally:
    self.fila.task_done()
```

Toda linha retirada, inclusive a sentinela `None`, recebe `task_done()`. `break` deixa o `while`; linhas reais são passadas ao gravador. Essa ordem preserva FIFO: como [[manager]] só envia `None` depois de aguardar o produtor, ela fica atrás de todas as linhas já enfileiradas.

### Exceções e fechamento

```python
except Exception as erro:
    self.erro = erro
    print(f"[Gravador] Erro: {erro}")
finally:
    if gravador is not None:
        try:
            gravador.fechar()
        except Exception as erro:
            self.erro = self.erro or erro
```

O `except` captura falha do bloco principal, preserva-a e a expõe. O `finally` tenta fechar apenas se existe gravador; seu `except` não apaga a falha inicial. `run()` não retorna dado ao chamador; resultado observável é arquivo/`erro`.

## Insights para outros projetos

- Dê a um único consumidor a propriedade do arquivo.
- Use sentinela FIFO após encerrar os produtores.
- Preserve exceções de thread em estado observável.

## Resumo mental

É o funcionário do disco: espera trabalho, grava linhas reais, encerra no bilhete `None` e tenta guardar o diagnóstico de sua própria falha.
#PROJETO_SENSOR_VIBRAÇÃO
