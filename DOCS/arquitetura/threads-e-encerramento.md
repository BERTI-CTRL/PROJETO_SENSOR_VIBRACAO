# Threads e encerramento

Uma sessão envolve três contextos de execução:

| Contexto | Responsabilidade |
|---|---|
| event loop da GUI | responde a botões e atualiza a tela em [[janela]]; chama `manager.iniciar()` e `manager.parar()` |
| thread `coletor-serial` | executa [[coletor]], lê a serial e enfileira linhas de nove valores |
| thread `gravador-csv` | executa [[gravador_worker]], consome a fila e usa [[gravador]] para gravar o CSV |

## Sequência normal de parada

```text
parar flag -> join coletor -> put(None) -> join gravador -> flush/close
```

1. A GUI (ou [[teste_manager]]) chama `SensorManager.parar()`.
2. `coletor.parar()` muda a flag que o leitor serial consulta cooperativamente.
3. `join` aguarda `coletor-serial`, assegurando que ele não colocará mais linhas na fila.
4. `put(None)` entrega a sentinela ao `gravador-csv` depois de todas as linhas já produzidas.
5. `join` aguarda o trabalhador consumir a sentinela; seu `finally` chama `fechar()`, que grava o lote residual e fecha o arquivo.

A sentinela não é uma amostra. [[gravador_worker]] ainda chama `task_done()` para ela, pois cada `Queue.get()` precisa ser reconhecido mesmo na parada.

O uso de threads daemon não substitui essa sequência: ele apenas evita que uma thread remanescente impeça a saída do processo. O `join` explícito é o que dá ao caminho normal a chance de flush/close. A parada cooperativa durante a espera de abertura serial é relacionada a [[correcao-controles-parada-e-i2c]].
#PROJETO_SENSOR_VIBRAÇÃO
