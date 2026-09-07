# serial_reader.py

## Resumo

`ler_dados()` é a fronteira entre serial e aplicação: abre a porta, filtra texto inválido, converte o protocolo de oito campos e produz as nove posições consumidas por [[coletor]].

## Dependências e efeitos externos

Importa `time`, PySerial (`serial`) e `random` (somente para o gerador fake). Abrir `serial.Serial(...)` acessa hardware. O módulo também executa `print("INICIOU O SERIAL_READER")` no momento da importação.

> [!warning]
> Importar [[manager]] acaba importando este módulo e produz essa mensagem no console.

## Interface, protocolo e saída

```python
def ler_dados(porta, baudrate=230400, timeout=0.1, deve_continuar=None)
```

Espera texto `contador,tempo_arduino_us,ax,ay,az,gx,gy,gz`. A linha passa somente se `split(",")` produzir oito campos e `map(float, campos)` funcionar. A tupla gerada é:

```python
yield (
    tempo_arduino_us, timestamp, contador,
    ax, ay, az, gx, gy, gz
)
```

`timestamp = time.perf_counter()` é capturado **antes** de `arduino.readline()`: representa o início da tentativa local de leitura, não necessariamente o instante em que a linha chegou ou foi recebida pelo PC. `tempo_arduino_us` é a base de cálculo de Hz em [[coletor]]. Consulte [[protocolo-serial]] e [[esquema-csv]] para os dois formatos CSV.

## Fluxo de `ler_dados()`

1. `continuar()` encapsula o callback: sem callback continua; com callback para quando retornar `False`.
2. `with serial.Serial(porta, baudrate, timeout=timeout)` garante fechamento ao fim do gerador.
3. Aguarda até dois segundos com `time.monotonic()` e `sleep(0.05)`, ainda permitindo parada, então chama `arduino.reset_input_buffer()`.
4. Lê uma linha, aplica `decode('utf-8', errors='ignore').strip()` e ignora timeout/linha vazia.
5. Valida contagem, converte os oito campos e faz `yield`; `ValueError` é logado e o loop continua.

O timeout de 0,1 s limita a espera usual para parar durante `readline()`.

> [!warning]
> `linhas_invalidas` é incrementado para campo incorreto ou conversão falha, mas não é retornado, impresso nem exposto ao [[coletor]].

> [!warning]
> Exceções de abertura/leitura da porta não são capturadas aqui; o tratamento explícito cobre apenas `ValueError`.

## `ler_dados_fake()` e execução direta

O fake gera aleatoriamente aceleração `[-2, 2]`, giro `[-250, 250]` e espera 0,01 s. Ele emite somente oito valores:

```python
yield timestamp, contador, ax, ay, az, gx, gy, gz
```

> [!warning]
> A forma não contém `tempo_arduino_us`, não encaixa no desempacotamento de nove campos de [[coletor]] e não aceita callback de parada.

No `__main__`, usa `COM4` a `115200`, divergindo do default de `230400` usado pela função e por [[coletor]]. Compare a configuração com [[arduino_mpu6050]].

## Código explicado, na ordem do arquivo

### Efeito de importação e imports

```python
print("INICIOU O SERIAL_READER")
import time
import serial
import random
```

O `print` vem antes das importações e ocorre simplesmente ao carregar o módulo. `time` fornece relógios/espera, `serial` abre a porta e `random` serve exclusivamente ao gerador de teste.

### Assinatura e callback local

```python
def ler_dados(porta, baudrate=230400, timeout=0.1, deve_continuar=None):
    def continuar():
        return deve_continuar is None or deve_continuar()
```

Recebe porta obrigatória, configuração serial e callback opcional; retorna um gerador, pois possui `yield`. A função interna não recebe argumentos e concentra a regra: sem callback significa aquisição contínua, callback falso encerra loops de espera e leitura.

### Context manager, estabilização e leitura

```python
with serial.Serial(porta, baudrate, timeout=timeout) as arduino:
    limite_espera = time.monotonic() + 2
    while time.monotonic() < limite_espera:
        if not continuar():
            return
        time.sleep(0.05)
    arduino.reset_input_buffer()
```

O context manager recebe porta/baud/timeout e fecha a serial ao terminar por parada, retorno ou exceção. O primeiro `while` espera possível reset da placa sem deixar de consultar o cancelamento. Depois, o buffer de entrada é descartado para não analisar texto de inicialização.

```python
while continuar():
    timestamp = time.perf_counter()
    dados_linha = arduino.readline().decode('utf-8', errors='ignore').strip()
    if not dados_linha:
        continue
```

O segundo loop produz amostras enquanto autorizado. `readline()` pode retornar vazio no timeout; `continue` ignora esse caso e volta a testar a parada. O timestamp é capturado antes da tentativa de leitura e integra a saída, mas não equivale necessariamente ao momento de chegada/recepção; ele não mede a frequência do Arduino.

### Validação, conversão e `yield`

```python
campos = dados_linha.split(",")
if len(campos) != 8:
    linhas_invalidas += 1
    continue
try:
    contador,tempo_arduino_us,ax,ay,az,gx,gy,gz = map(float,campos)
    yield (tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz)
except ValueError:
    linhas_invalidas += 1
    print(f"[Serial] Linha inválida: {repr(dados_linha)}")
    continue
```

O primeiro `if` filtra protocolo incompleto; o `try` transforma todos os campos de uma vez. Em sucesso, `yield` pausa a função e entrega nove valores a [[coletor]]; retomada a iteração, volta ao loop. `ValueError` não encerra aquisição, apenas registra a linha e segue.

### `ler_dados_fake()` e `__main__`

`ler_dados_fake()` inicia `contador = 0`, entra em `while True`, usa `random.uniform`, faz `yield` da tupla de oito itens e espera 0,01 s. Não recebe parâmetro nem retorna normalmente. Já o bloco:

```python
if __name__ == "__main__":
    for tempo_arduino_us,timestamp,contador,ax,ay,az,gx,gy,gz in ler_dados(porta="COM4",baudrate=115200):
```

só ocorre em execução direta: o `for` desempacota explicitamente os nove valores devolvidos por `ler_dados()` — incluindo `tempo_arduino_us` e `timestamp` — e imprime `contador` e os três valores de aceleração em cada iteração. É um loop de diagnóstico manual, sem callback de parada próprio; não é usado pelo pipeline de [[manager]].

## Insights para outros projetos

- Valide protocolo na fronteira de I/O antes de atualizar estado compartilhado.
- Combine timeout finito e callback cooperativo para cancelar leituras bloqueantes.
- Diferencie relógio do host de relógio do dispositivo.

## Resumo mental

É o tradutor serial: remove ruído, exige oito números, acrescenta o tempo do PC e entrega uma amostra pronta para o pipeline.
#PROJETO_SENSOR_VIBRAÇÃO
