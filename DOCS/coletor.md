# `sensor/coletor.py`

`Coletor` coordena uma sessão de aquisição: consome as nove posições de [[serial_reader]], calcula métricas, grava uma cópia em [[buffers]] e tenta entregar outra à fila do gravador. Ele não escreve em disco diretamente.

## Interface e estado

```python
Coletor(porta="COM4", baudrate=230400, fila_gravacao=None)
configurar_fila_gravacao(fila_gravacao)
executar()
parar()
```

`executar()` marca `rodando=True` e reinicializa a sessão: contadores, referências de tempo, perdas, três métricas de Hz e o `deque(maxlen=100)`. Depois chama `ler_dados` com `deve_continuar=lambda: self.rodando`; `parar()` muda esse sinal para falso. A fila pode ser configurada no construtor ou posteriormente pelo [[manager]].

## Processamento por amostra

Para cada tupla `(tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz)`, o coletor:

1. incrementa `numero_amostras` e compara o contador atual com o anterior;
2. calcula Hz com `tempo_arduino_us` depois da primeira amostra;
3. chama `buffer.adicionar(...)` com os nove valores;
4. chama `_enfileirar_gravacao(...)` com a mesma sequência em uma lista.

`_registrar_salto` conta um salto apenas se `contador > contador_anterior + 1`. Para uma transição de 1000 para 1005, soma um salto e quatro `amostras_perdidas`. Isso mede lacuna no que chegou pela serial; não detecta repetição, retrocesso ou overflow do contador. Veja [[tempo-frequencia-e-perdas]].

`_enfileirar_gravacao` usa `put_nowait`. Se a fila estiver cheia, incrementa `amostras_nao_enfileiradas` e segue adquirindo, emitindo log na primeira perda e depois a cada mil. Essa perda de persistência no CSV é independente das perdas inferidas pelo contador.

## Métricas

| Atributo | Cálculo | Significado |
|---|---|---|
| `hz_medio` | `(numero_amostras - 1) / dt_total` | frequência desde a primeira amostra |
| `hz_inst` | `1 / dt_inst` | frequência entre as duas últimas amostras |
| `hz_inst_suavizado` | média dos últimos até 100 `hz_inst` | estabiliza a exibição |

Os dois intervalos usam `micros()` do Arduino, convertidos de µs para segundos. `timestamp` do PC é preservado para registro, não para essas fórmulas. [[tempo-frequencia-e-perdas]] explica a escolha.

## Integração

- [[serial_reader]] entrega amostras válidas e executa a parada cooperativa.
- [[buffers]] mantém apenas a janela recente usada por [[janela]] e [[statistics]].
- A fila é consumida pelo trabalhador documentado em [[gravador_worker]] para formar o histórico completo no [[esquema-csv]].
- [[manager]] cria e inicia a thread que chama `executar()`.

## Inconsistência de configuração preservada

O valor padrão atual do `Coletor` é `baudrate=230400`; ele é repassado sem conversão ao leitor. O firmware de [[arduino_mpu6050]] declara 115200 e o modo direto de [[serial_reader]] também usa 115200. A divergência é registrada, mas não foi alterada nesta tarefa.
