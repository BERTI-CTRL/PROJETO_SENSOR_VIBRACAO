# serial_reader.py — explicação completa, em ordem de linhas

O arquivo [sensor/serial_reader.py](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\sensor\serial_reader.py) é a porta de entrada dos dados no Python. Ele abre a comunicação USB/serial com o Arduino, lê texto, verifica se a linha tem o formato esperado e entrega uma amostra pronta ao Coletor.

Ele não desenha gráficos, não calcula Hz e não grava CSV. Seu papel termina quando entrega uma tupla válida.

```text
MPU6050 → Arduino envia texto → serial_reader.py → coletor.py
                                                   ├→ buffer → interface
                                                   └→ fila → CSV
```

Os termos mais importantes:

| Termo | Significado simples |
|---|---|
| serial | Comunicação por uma porta como COM4, normalmente através do cabo USB. |
| baudrate | Velocidade configurada para comunicação serial. Arduino e Python precisam usar o mesmo valor. |
| bytes | Dados brutos recebidos pela serial, antes de virar texto. |
| decode | Conversão de bytes para texto. |
| linha | Texto terminado por quebra de linha, enviado por Serial.println no Arduino. |
| protocolo | Regra sobre quantos campos existem e em que ordem aparecem. |
| generator | Função com yield; entrega um resultado por vez, sem guardar todos na memória. |
| callback | Função pequena que outro código chama para consultar uma decisão. |
| timeout | Tempo máximo de espera por uma linha antes de readline devolver vazio. |
| ValueError | Erro ocorrido quando um texto não pode virar número. |

O Arduino envia oito campos:

```text
contador,tempo_arduino_us,ax,ay,az,gx,gy,gz
```

O leitor reorganiza e acrescenta o instante local do PC, entregando nove valores:

```python
(
    tempo_arduino_us,
    timestamp,
    contador,
    ax, ay, az,
    gx, gy, gz,
)
```

## Linhas 1 a 9: efeito de importação e bibliotecas

```python
print("INICIOU O SERIAL_READER")
import time
import serial
import random
from sensor.config import BAUD_RATE, PORTA_SERIAL
```

A primeira linha imprime a mensagem assim que Python importa o módulo. Por exemplo, importar manager também importa coletor, que importa serial_reader; por isso a mensagem aparece mesmo sem iniciar a coleta.

time fornece relógios e pausas. serial é a biblioteca PySerial que abre a conexão e lê bytes. random é usado somente pelo gerador falso de teste. A porta e o baud rate vêm de `sensor/config.py`.

## Linhas 12 a 19: função principal e regra de parada

```python
def ler_dados(porta=PORTA_SERIAL, baudrate=BAUD_RATE, timeout=0.1, deve_continuar=None):
    """Lê linhas da serial enquanto a aquisição estiver ativa."""
```

porta e baudrate usam por padrão `PORTA_SERIAL` e `BAUD_RATE`, definidos em `sensor/config.py`. Eles ainda podem ser substituídos explicitamente em testes ou usos especiais. timeout é 0.1 segundo. deve_continuar é opcional; se fornecido, deve ser uma função que devolve True ou False.

A função é um generator porque contém yield mais adiante. Portanto ela não inicia tudo no instante da chamada: ela começa a trabalhar quando alguém a percorre com for.

```python
def continuar():
    return deve_continuar is None or deve_continuar()
```

continuar é uma função dentro de ler_dados. A expressão usa or:

```python
deve_continuar is None
```

significa que não há callback, então o leitor pode continuar indefinidamente.

```python
deve_continuar()
```

só é chamado se existir callback. No uso normal, Coletor envia algo equivalente a:

```python
lambda: self.rodando
```

Assim, quando Coletor.parar muda rodando para False, continuar também devolve False.

## Linhas 21 a 42: abrir a porta e esperar o Arduino estabilizar

```python
with serial.Serial(porta, baudrate, timeout=timeout) as arduino:
```

serial.Serial abre a porta física com os parâmetros recebidos. with cria um contexto: quando o bloco termina, seja por return, fim normal ou erro, a porta é fechada automaticamente.

```python
limite_espera = time.monotonic() + 2
```

time.monotonic é um relógio crescente apropriado para medir duração. Ele não volta para trás se o relógio civil do computador for ajustado. A linha calcula “agora mais dois segundos”.

```python
while time.monotonic() < limite_espera:
    if not continuar():
        return
    time.sleep(0.05)
```

Abrir a serial pode reiniciar algumas placas Arduino. Esse loop espera até dois segundos antes de consumir dados. Em cada volta, verifica pedido de parada. return encerra o generator e também sai do with, fechando a porta. sleep de 0.05 evita gastar CPU consultando a condição milhares de vezes por segundo.

```python
arduino.reset_input_buffer()
```

Descarta bytes que chegaram durante o reset. Isso ajuda a iniciar a leitura na próxima linha completa do protocolo, em vez de analisar restos de inicialização.

## Linhas 46 a 65: loop de leitura e transformação em texto

```python
linhas_invalidas = 0
while continuar():
    timestamp = time.perf_counter()
```

linhas_invalidas começa em zero e aumenta quando a linha não tem formato válido. Neste código ela não é mostrada nem retornada; serve somente como contagem interna.

while continua enquanto o callback permite. perf_counter registra um relógio de alta resolução do computador. Ele é guardado na amostra como referência local, mas o Coletor usa tempo_arduino_us para calcular frequência física.

```python
dados_linha = arduino.readline().decode(
    "utf-8",
    errors="ignore"
).strip()
```

readline espera uma quebra de linha ou até timeout. O retorno é bytes. decode transforma bytes em texto UTF-8. errors="ignore" descarta bytes que não formam texto UTF-8 válido, evitando uma exceção por corrupção isolada. strip remove espaços, quebra de linha e retorno de carro das pontas.

```python
if not dados_linha:
    continue
```

Uma string vazia é considerada falsa em Python. Isso acontece, por exemplo, quando timeout ocorre. continue pula o restante da volta e reinicia o loop; o reader não encerra apenas porque uma leitura demorou.

## Linhas 69 a 86: validar a forma e converter números

```python
campos = dados_linha.split(",")
if len(campos) != 8:
    linhas_invalidas += 1
    continue
```

split separa a linha nas vírgulas. A exigência é exatamente oito campos. Uma mensagem como Erro MPU, uma linha parcial ou uma mensagem de depuração do Arduino não entra no Coletor. linhas_invalidas aumenta e continue volta a esperar a próxima linha.

```python
try:
    contador, tempo_arduino_us, ax, ay, az, gx, gy, gz = map(float, campos)
```

map(float, campos) tenta converter os oito textos em float. A atribuição também exige que existam exatamente oito resultados, condição já validada antes. A ordem aqui precisa corresponder exatamente à ordem que o firmware envia.

```python
if contador % 1000 == 0:
    print(f"[Serial] : {contador}")
```

% calcula o resto de divisão. Contadores múltiplos de mil geram uma mensagem de progresso. O contador é float por causa de map(float), mas representa uma sequência inteira enviada pelo firmware.

## Linhas 89 a 121: yield e tratamento de conversão inválida

O texto entre aspas triplas que contém um print é uma string isolada e não é executado. Ele preserva um antigo diagnóstico detalhado.

```python
yield (
    tempo_arduino_us,
    timestamp,
    contador,
    ax,
    ay,
    az,
    gx,
    gy,
    gz,
)
```

yield é diferente de return. Ele pausa ler_dados e entrega uma única tupla ao for do Coletor. Quando o Coletor pede outra amostra, o generator retoma logo após yield e volta ao while.

Note que a ordem foi reorganizada. Arduino envia contador primeiro, mas Coletor recebe tempo_arduino_us primeiro. timestamp não veio do Arduino; foi criado no PC.

```python
except ValueError:
    linhas_invalidas += 1
    print(f"[Serial] Linha inválida: {repr(dados_linha)}")
    continue
```

ValueError acontece se o número de campos é oito, mas algum texto não vira float, por exemplo abc. repr mostra a representação técnica da string, incluindo caracteres especiais que um print comum poderia esconder. A exceção é tratada sem derrubar a aquisição: o leitor registra e segue para a próxima linha.

Exceções como porta inexistente, porta ocupada ou falha do sistema serial não são tratadas neste arquivo; elas podem interromper a função ao abrir ou ler a porta.

## Linhas 125 a 156: gerador artificial

```python
def ler_dados_fake():
    contador = 0
    while True:
        timestamp = time.perf_counter()
        contador += 1
```

Esta função é para teste sem hardware. Ela não recebe argumentos. while True produz valores sem fim, até o consumidor interromper a iteração.

```python
ax = random.uniform(-2, 2)
ay = random.uniform(-2, 2)
az = random.uniform(-2, 2)
```

random.uniform(a, b) sorteia um float entre a e b. Estas três linhas criam acelerações artificiais.

```python
gx = random.uniform(-250, 250)
gy = random.uniform(-250, 250)
gz = random.uniform(-250, 250)
```

As três linhas criam valores artificiais de velocidade angular.

```python
yield timestamp, contador, ax, ay, az, gx, gy, gz
time.sleep(0.01)
```

O yield fake contém oito itens, e não nove: não existe tempo_arduino_us. sleep de 0.01 s tenta aproximar 100 amostras por segundo.

Por isso o fake não pode substituir diretamente ler_dados no Coletor atual: Coletor espera nove valores, nessa ordem:

```python
tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz
```

## Linhas 159 a 182: execução direta para diagnóstico

```python
if __name__ == "__main__":
    print("Entrou no main")
```

Este bloco só roda se o arquivo for chamado diretamente:

```powershell
python -m sensor.serial_reader
```

Ele não roda quando Coletor importa ler_dados.

```python
for tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz in ler_dados():
    print("contador:", contador)
    print(
        f"Aceleração em x:{ax} | "
        f"Aceleração em y:{ay} | "
        f"Aceleração em z:{az}"
    )
```

O `for` exige os nove valores reais gerados por `ler_dados`. Neste modo, a porta e o baud rate também vêm de `sensor/config.py`, evitando uma configuração diferente do restante do projeto.

As linhas de giro e o loop fake no final estão comentados ou colocados em uma string multilinha. Portanto não executam.

## Relação com os outros arquivos

```python
# sensor/coletor.py
for tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz in ler_dados(...):
    ...
```

Coletor é o consumidor imediato desta função. Ele usa contador para detectar perdas, tempo_arduino_us para calcular Hz, buffer para interface e fila para o CSV.

```text
serial_reader.py: valida e traduz texto
coletor.py: mede e distribui a amostra
buffers.py: preserva dados recentes
gravador_worker.py: grava sem travar a serial
```

## Resumo mental

serial_reader é o tradutor entre cabo e Python. Ele abre a porta, espera o possível reset, remove bytes antigos, lê uma linha, exige oito campos numéricos e entrega nove valores ao Coletor. Linhas vazias, incompletas ou não numéricas são ignoradas sem encerrar a sessão.
