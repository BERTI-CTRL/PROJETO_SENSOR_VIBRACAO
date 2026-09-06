# `sensor/manager.py`

`SensorManager` coordena uma sessão de aquisição completa: [[coletor]] produz as linhas, [[gravador_worker]] as persiste e `buffer` expõe o histórico circular à interface. A instância global `manager = SensorManager()` é um singleton prático: módulos como [[janela]] e [[teste_manager]] importam o mesmo objeto, mas a classe continua podendo ser instanciada em testes.

## Início

`iniciar()` não faz nada quando `self.thread` existe e ainda está viva, prevenindo um início duplicado da mesma sessão. Caso contrário, ele cria `Queue(maxsize=50_000)`, injeta essa fila no coletor, cria/inicia `GravadorWorker` e só então cria/inicia a thread daemon `coletor-serial` que chama `coletor.executar`.

A ordem importa: o consumidor já está bloqueado em `Queue.get()` antes de o produtor poder enfileirar a primeira amostra. A capacidade de 50.000 itens absorve picos de disco; se esgotar, [[coletor]] contabiliza as linhas que não foram enfileiradas sem bloquear a serial, como descrito em [[tempo-frequencia-e-perdas]].

## Parada e retorno

`parar()` retorna `False` quando não há thread do coletor, isto é, não havia sessão para encerrar. Com sessão ativa, retorna `True` após seguir esta ordem:

1. chama `coletor.parar()` para abaixar a flag cooperativa;
2. faz `join()` na thread do coletor, impedindo novas inserções após a sentinela;
3. coloca `None` na fila de gravação;
4. faz `join()` no gravador para esperar consumo, flush e `close()`;
5. limpa `thread`, `gravador_thread` e `fila_gravacao` com `None`.

A limpeza das referências permite uma nova chamada de `iniciar()`. Os detalhes dos três contextos de execução e a sequência visual estão em [[threads-e-encerramento]].

## Interface

```python
manager.iniciar()       # inicia se não houver coletor vivo
encerrou = manager.parar()  # True se uma sessão foi encerrada
buffer = manager.buffer
```

`buffer` apenas encaminha `coletor.buffer`; ele não cria uma cópia. Consulte [[buffers]] para retenção, snapshots e sincronização do histórico em memória.
