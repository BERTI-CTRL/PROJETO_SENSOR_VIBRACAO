# `sensor/gravador_worker.py`

`GravadorWorker` herda de `threading.Thread` e é o consumidor da fila de persistência. Ele recebe as linhas de nove valores que [[coletor]] produz e delega o arquivo a [[gravador]]. Assim, uma escrita lenta não bloqueia a leitura serial.

## Execução da thread

O construtor registra a thread com nome `gravador-csv` e `daemon=True`. O atributo daemon evita que uma thread remanescente mantenha o processo vivo, mas não é a garantia de integridade do arquivo: o [[manager]] usa `join()` no encerramento normal para aguardar o flush e o fechamento.

Em `run()`, `fila.get()` bloqueia de modo seguro até haver trabalho, sem loop de espera ativa. Cada item retirado é confirmado por `fila.task_done()` no `finally` interno, inclusive quando `salvar()` falha ou quando o item é a sentinela. Isso mantém a contabilidade da `Queue` consistente para um eventual `Queue.join()`.

`None` é a sentinela enviada por [[manager]] depois que a thread do coletor termina. Ela não é uma linha CSV válida; ao recebê-la, o loop termina. A ordem completa está em [[threads-e-encerramento]].

## Erros e recursos

Exceções durante a abertura, o consumo ou a gravação são guardadas em `worker.erro` e também impressas. O `finally` externo tenta `gravador.fechar()` sempre que a instância foi criada. Se o fechamento também falhar, a primeira exceção é preservada em `erro`, sem ocultar o problema original.

Logo, o caminho normal assegura a chamada de fechamento; em cenários de falha, o trabalhador ainda tenta descarregar o buffer residual e fechar o descritor. A fila é thread-safe; `GravadorCSV` é acessado somente por esta thread.

## Interface

```python
GravadorWorker(fila, tamanho_buffer=1000)
worker.start()
# produtor insere linhas de nove valores e, ao terminar, None
worker.join()
erro = worker.erro
```
