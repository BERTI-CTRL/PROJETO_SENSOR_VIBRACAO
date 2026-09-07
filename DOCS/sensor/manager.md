# manager.py

## Resumo

`SensorManager` orquestra a sessão: cria fila, inicia [[gravador_worker]], inicia a thread de [[coletor]] e encerra ambos em ordem. `manager = SensorManager()` é o singleton usado por [[janela]], [[grafico]] e [[teste_manager]].

## Dependências e estado

Importa `Queue`, `Thread`, `Coletor` e `GravadorWorker`. `__init__()` constrói um único coletor reutilizável e mantém `thread`, `fila_gravacao` e `gravador_thread` como `None`. A propriedade `buffer` devolve diretamente `self.coletor.buffer`.

## `iniciar()`

Se `self.thread` existe e está viva, retorna sem iniciar outra sessão. Caso contrário, monta nesta ordem:

```python
self.fila_gravacao = Queue(maxsize=50_000)
self.coletor.configurar_fila_gravacao(self.fila_gravacao)
self.gravador_thread = GravadorWorker(self.fila_gravacao)
self.gravador_thread.start()
self.thread = Thread(target=self.coletor.executar, name="coletor-serial", daemon=True)
self.thread.start()
```

Iniciar o consumidor primeiro garante um destino para a primeira amostra. A fila absorve picos; ao lotar, o [[coletor]] preserva aquisição/UI e contabiliza a perda de CSV.

> [!warning]
> `iniciar()` não retorna confirmação nem captura falha de abertura serial. Se a thread morrer por erro, o chamador não recebe exceção por este método.

## `parar()`

Se nunca houve thread, retorna `False`. Com sessão, chama `coletor.parar()`, aguarda a thread produtora, envia sentinela, aguarda o worker e limpa referências, retornando `True`:

```python
self.thread.join()
self.fila_gravacao.put(None)
self.gravador_thread.join()
```

Essa ordem impede novas inserções após a sentinela e é detalhada em [[threads-e-encerramento]].

> [!warning]
> `fila_gravacao.put(None)` é bloqueante. Se o worker morreu e a fila ficou cheia, a parada pode bloquear nesse ponto.

## Fluxo e decisão arquitetural

`iniciar → Queue(50.000) → worker → thread coletor → buffer/UI + CSV`. Singleton simplifica consumidores de UI. [[statistics]] lê `manager.buffer.snapshot(...)` e [[janela]] também expõe métricas do coletor.

> [!warning]
> O mesmo coletor e [[buffers]] são reutilizados entre sessões. Métricas são reiniciadas, mas o buffer não é limpo automaticamente.

## Código explicado, na ordem do arquivo

### Imports, classe e construtor

```python
from queue import Queue
from threading import Thread
from sensor.coletor import Coletor
from sensor.gravador_worker import GravadorWorker
```

`Queue` fornece o canal sincronizado; `Thread` cria o produtor; os imports internos trazem as extremidades do pipeline. `SensorManager.__init__()` não recebe parâmetros nem retorna valor: cria `self.coletor = Coletor()` e inicia referências de thread/fila como `None`.

### `iniciar()`

```python
if self.thread is not None and self.thread.is_alive():
    return
```

Esse retorno precoce não devolve estado e impede sessão duplicada. No caminho normal, o método cria `Queue(maxsize=50_000)`, passa-a ao coletor, instancia/inicia worker e por último constrói `Thread(target=self.coletor.executar, name="coletor-serial", daemon=True)` e chama `start()`. O alvo não recebe argumentos: usa o estado já configurado no coletor.

### `parar()`

```python
if self.thread is None:
    return False
self.coletor.parar()
self.thread.join()
```

Sem sessão retorna `False`; com sessão solicita a flag cooperativa e aguarda produção. Depois testa fila/worker antes de enviar `None` e chamar o `join()` do worker. Por fim limpa as três referências e retorna `True`, valor usado pela [[janela]] para diferenciar ausência de sessão de encerramento solicitado.

### Propriedade e singleton

```python
@property
def buffer(self):
    return self.coletor.buffer

manager = SensorManager()
```

`buffer` não recebe argumento e devolve a mesma instância circular, não uma cópia. A última linha é executada ao importar este módulo: constrói o singleton, mas não abre serial até alguém chamar `manager.iniciar()`.

## Insights para outros projetos

- Inicie consumidores antes de produtores.
- Envie sentinela apenas depois de encerrar produtores.
- Diferencie “não havia sessão” de “sessão foi encerrada” no retorno de parada.

## Resumo mental

O manager é o maestro: prepara o canal, põe o gravador em espera, libera o coletor e, ao parar, silencia o produtor antes do último sinal ao consumidor.
#PROJETO_SENSOR_VIBRAÇÃO
