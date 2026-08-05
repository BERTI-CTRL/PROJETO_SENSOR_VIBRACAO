# `sensor/teste_manager.py`

**Responsabilidade:** teste simples de aquisição sem interface gráfica.

> O nome histórico deste documento é `testar_dados.md`, mas o script existente no projeto é `sensor/teste_manager.py`. Ele não valida um CSV pronto; ele abre a serial por meio do `manager` e mostra se a coleta está viva.

## Quando usar

Use antes de abrir a janela PyQt quando quiser responder apenas a estas perguntas:

- a porta serial abre?
- o Arduino está enviando amostras?
- o contador aumenta?
- o buffer recebe dados?

Não use este script para medir desempenho da interface, pois ele não desenha gráficos.

## Execução

```powershell
python -m sensor.teste_manager
```

O terminal imprime aproximadamente uma linha por segundo:

```text
Contador: 1250 | Amostras: 1250
```

`contador` vem do Arduino. `Amostras` é a quantidade atualmente mantida no buffer, que para de crescer ao chegar em 10.000.

Para encerrar, pressione `Ctrl+C`. O bloco `finally` chama `manager.parar()`, que fecha o coletor e descarrega o último lote do CSV.

## Relação com os outros arquivos

```text
teste_manager.py → sensor.manager.manager
                         ↓
                  Coletor + GravadorWorker
                         ↓
                  Buffer e CSV normais
```

O script usa exatamente o mesmo pipeline da janela principal. A diferença é que ele não cria `realtime/janela.py` nem abre Plotly ao terminar.

## Referências

- [[manager]] — ciclo de vida das threads.
- [[coletor]] — contador, Hz e buffer.
- [[serial_reader]] — leitura da porta.
