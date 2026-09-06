# `sensor/serial_reader.py`

`ler_dados` é a fronteira entre o CSV do firmware e a aquisição Python. Para o formato da linha, veja [[protocolo-serial]]; para o processamento posterior, veja [[coletor]].

## Interface

```python
def ler_dados(porta, baudrate=230400, timeout=0.1, deve_continuar=None)
```

É um gerador. Cada linha válida gera, nesta ordem, a tupla de nove valores:

```text
(tempo_arduino_us, timestamp_pc, contador, ax, ay, az, gx, gy, gz)
```

O leitor abre a porta em um context manager, portanto o fechamento ocorre ao terminar a iteração. A abertura pode reiniciar a placa; por isso o módulo espera dois segundos, consultando `deve_continuar()` a cada 50 ms, e em seguida chama `reset_input_buffer()` para descartar bytes de inicialização.

## Parada e timeout

`deve_continuar` é opcional. Sem callback, a leitura continua; com callback, o laço termina quando ele retorna `False`. Como `readline()` pode estar bloqueado, o `timeout=0.1` também limita a espera por uma linha e, consequentemente, a latência usual da parada durante leitura. Quando ocorre timeout, a linha decodificada fica vazia e é ignorada; a porta não é reaberta.

`decode('utf-8', errors='ignore').strip()` tolera bytes inválidos e remove terminadores. A linha só passa se `split(',')` produzir exatamente oito campos e todos puderem ser convertidos por `float`; caso contrário, `linhas_invalidas` é incrementado. Esse contador é diagnóstico interno: não é retornado nem exposto como métrica do `Coletor`.

## Tempos e ordem

`timestamp_pc` vem de `time.perf_counter()` imediatamente antes da tentativa de leitura. Ele informa quando o PC tentou receber a linha, mas não é a base da frequência do sensor. `tempo_arduino_us`, vindo de `micros()`, é o primeiro item retornado porque [[coletor]] o usa para calcular Hz. A diferença é detalhada em [[tempo-frequencia-e-perdas]].

Há também `ler_dados_fake()`, um gerador manual de dados sintéticos. Ele preserva sua tupla histórica de oito valores e não é intercambiável com a tupla de nove valores de `ler_dados()`.

## Inconsistência de baud rate preservada

O parâmetro padrão atual de `ler_dados` é **230400**, mas o bloco `if __name__ == '__main__'` chama `ler_dados(porta="COM4", baudrate=115200)`. Além disso, o firmware em [[arduino_mpu6050]] contém `Serial.begin(115200)`. Essa divergência é documentada aqui porque uma taxa incompatível impede a leitura correta; nenhum valor foi alterado nesta tarefa.

## Relações

- [[arduino_mpu6050]] produz a linha de oito campos.
- [[coletor]] passa porta, baud rate e callback de parada, então recebe a tupla de nove valores.
- [[correcao-pulos-amostras-serial]] registra o cuidado de manter `readline()` para não cortar linhas.
- [[protocolo-serial]] separa o CSV de transporte do CSV persistido.
