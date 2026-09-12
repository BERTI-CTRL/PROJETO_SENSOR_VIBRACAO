O arquivo [`sensor/coletor.py`](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\sensor\coletor.py) é o **coordenador da coleta**. Ele não conversa diretamente com o MPU6050 e não escreve o CSV no disco. Seu trabalho é receber cada leitura já interpretada, calcular métricas, guardar dados recentes para a interface e encaminhar uma cópia para gravação.

```text
MPU6050 → Arduino → porta serial → serial_reader.py
                                      ↓
                                 coletor.py
                         ┌────────────┴─────────────┐
                         ↓                          ↓
                 BufferSensores                 Queue
                  (gráfico/UI)                    ↓
                                           GravadorWorker
                                                 ↓
                                                CSV
```

Os termos mais importantes:

| Termo | Significado simples |
|---|---|
| **amostra** | Uma leitura completa do sensor: tempos, contador, `ax`, `ay`, `az`, `gx`, `gy`, `gz`. |
| **classe** | Um molde para criar objetos. `Coletor` é o molde. |
| **objeto/instância** | Um coletor real criado a partir da classe, por exemplo `Coletor()`. |
| **`self`** | O próprio objeto atual. `self.buffer` é o buffer pertencente àquele coletor. |
| **método** | Uma função dentro de uma classe, como `executar()` ou `parar()`. |
| **thread** | Uma linha de execução paralela. A coleta serial roda separada da interface e da gravação. |
| **fila (`Queue`)** | Uma área de espera: o coletor deposita amostras e o gravador as retira. |
| **buffer circular** | Memória que mantém apenas as amostras mais recentes; quando enche, sobrescreve as antigas. |
| **Hz (hertz)** | Quantidade de amostras por segundo. 200 Hz significa aproximadamente 200 leituras a cada segundo. |
| **microssegundo (`us`)** | Um milionésimo de segundo. `1_000_000 us = 1 s`. |
| **exceção** | Um evento de erro controlável, como a fila estar cheia. |
| **sentinela** | Um valor especial, aqui `None`, usado para avisar que o gravador deve terminar. |

A relação com os demais arquivos é esta:

- `arduino/mpu-6050/mpu-6050.ino` lê o MPU6050 e envia oito números por linha.
- `sensor/serial_reader.py` abre a porta serial, valida a linha e a transforma em nove valores Python: os oito vindos do Arduino mais o instante de chegada no computador.
- `sensor/coletor.py` é o arquivo explicado abaixo.
- `sensor/buffers.py` armazena até 10.000 amostras recentes para os gráficos.
- `sensor/gravador_worker.py` retira amostras da fila em uma thread dedicada.
- `sensor/gravador.py` grava essas amostras em CSV.
- `sensor/manager.py` cria as threads, inicia e encerra tudo na ordem correta.
- `realtime/janela.py` consulta o buffer para atualizar os gráficos.

O Arduino envia uma linha parecida com esta:

```text
contador,tempo_arduino_us,ax,ay,az,gx,gy,gz
125,640100,0.01,-0.02,0.99,1.22,-0.31,0.08
```

O leitor serial acrescenta um timestamp do PC e entrega ao coletor:

```python
(
    tempo_arduino_us,
    timestamp,
    contador,
    ax, ay, az,
    gx, gy, gz,
)
```

## Linhas 1 a 9: importações

```python
from sensor.buffers import BufferSensores
from collections import deque
from queue import Full
from sensor.serial_reader import ler_dados
```

`import` traz recursos de outros arquivos ou bibliotecas.

```python
from sensor.buffers import BufferSensores
```

Importa a classe responsável pelo histórico de amostras. O coletor usará esse buffer para que a interface consiga desenhar os gráficos sem precisar acessar a porta serial.

```python
from collections import deque
```

`deque` é uma fila eficiente nas duas extremidades. Aqui ela será usada como uma lista limitada das últimas frequências instantâneas.

```python
from queue import Full
```

`Full` é a exceção lançada quando se tenta colocar algo em uma `Queue` que já está cheia.

```python
from sensor.serial_reader import ler_dados
```

Importa a função geradora que abre a porta serial, recebe linhas do Arduino e entrega as amostras já convertidas para números.

As linhas iniciadas com `#` são comentários. Elas servem para pessoas lendo o código; Python não as executa.

## Linhas 12 e 13: definição da classe e construtor

```python
class Coletor:
```

Cria a classe chamada `Coletor`. Ela define quais informações e ações todo coletor terá.

```python
def __init__(self, porta=PORTA_SERIAL, baudrate=BAUD_RATE, fila_gravacao=None):
```

`__init__` é executado automaticamente quando alguém cria o objeto:

```python
coletor = Coletor()
```

Os parâmetros são:

```python
porta=PORTA_SERIAL
```

A porta serial padrão vem de `sensor/config.py`. Para alterá-la para todo o projeto, edite:

```python
PORTA_SERIAL = "COM5"
```

```python
baudrate=BAUD_RATE
```

O baud rate também vem de `sensor/config.py` e precisa ser igual ao configurado no Arduino:

```cpp
Serial.begin(230400);
```

```python
fila_gravacao=None
```

A fila para o CSV é opcional. `None` significa “nenhuma fila foi fornecida”. Isso permite usar o coletor apenas para visualizar dados, sem gravá-los.

## Linhas 15 a 51: estado inicial do coletor

```python
self.rodando = False
```

Cria uma “chave” de funcionamento. Inicialmente, ela vale `False`, ou seja, o coletor ainda está parado.

Quando `executar()` começa, ela muda para:

```python
self.rodando = True
```

Quando `parar()` é chamado, volta a ser:

```python
self.rodando = False
```

```python
self.porta = porta
self.baudrate = baudrate
```

Guarda os valores recebidos no construtor dentro do objeto.

- `self.porta`: por exemplo, `"COM4"`.
- `self.baudrate`: por exemplo, `230400`.

Mais tarde, esses valores são enviados para `ler_dados()`.

```python
self.buffer = BufferSensores()
```

Cria o buffer circular. Ele receberá todas as amostras recentes para a interface em tempo real.

O buffer tem nove colunas, nesta ordem:

```python
[
    "tempo_arduino_us",
    "timestamp",
    "contador",
    "ax", "ay", "az",
    "gx", "gy", "gz",
]
```

```python
self.fila_gravacao = fila_gravacao
```

Guarda a fila que levará amostras até o gravador CSV. Se não houver fila, o valor continua `None`.

```python
self.numero_amostras = 0
```

Conta quantas amostras válidas chegaram durante a sessão atual.

```python
self.contador_anterior = None
```

Guarda o último contador enviado pelo Arduino. No início não existe contador anterior, por isso é `None`.

```python
self.saltos_contador = 0
self.amostras_perdidas = 0
self.amostras_nao_enfileiradas = 0
```

São três métricas diferentes:

```python
self.saltos_contador
```

Conta quantas vezes o contador “pulou”.

Exemplo:

```text
100 → 105
```

Houve um salto.

```python
self.amostras_perdidas
```

Estima quantas amostras foram perdidas antes de chegarem ao Python.

No exemplo:

```text
100 → 105
```

As amostras `101`, `102`, `103` e `104` não chegaram. Portanto:

```python
amostras_perdidas += 4
```

```python
self.amostras_nao_enfileiradas
```

Conta dados que chegaram ao coletor e apareceram no buffer, mas não conseguiram entrar na fila de gravação porque ela estava cheia. Essas amostras podem aparecer no gráfico, mas não chegar ao CSV.

```python
self.hz_medio = 0
self.hz_inst = 0
self.hz_inst_suavizado = 0
```

Cria três medidas de frequência:

```python
self.hz_medio
```

Média de amostras por segundo desde o início da sessão.

```python
self.hz_inst
```

Frequência calculada apenas usando as duas últimas amostras.

```python
self.hz_inst_suavizado
```

Média das últimas frequências instantâneas. Ela oscila menos que `hz_inst`.

```python
self.tempo_arduino_inicial_us = 0
self.tempo_arduino_anterior_us = 0
```

Guardam tempos enviados pelo Arduino.

```python
self.tempo_arduino_inicial_us
```

Será o instante da primeira amostra da sessão. Serve para calcular a frequência média.

```python
self.tempo_arduino_anterior_us
```

Será o instante da amostra anterior. Serve para calcular a frequência instantânea.

```python
self.historico_hzs_inst = deque(maxlen=100)
```

Cria uma fila que guarda no máximo 100 frequências instantâneas.

Quando a 101ª frequência entra, a mais antiga sai automaticamente. Isso evita crescimento infinito de memória e cria uma média móvel de 100 valores.

## Linhas 53 a 56: trocar a fila de gravação

```python
def configurar_fila_gravacao(self, fila_gravacao):
    self.fila_gravacao = fila_gravacao
```

Este método permite trocar ou definir a fila depois de criar o coletor.

O `SensorManager` faz isso quando uma sessão começa:

```python
self.fila_gravacao = Queue(maxsize=50_000)
self.coletor.configurar_fila_gravacao(self.fila_gravacao)
```

Assim, cada sessão recebe uma fila nova e vazia.

## Linhas 60 a 80: detectar saltos no contador

```python
def _registrar_salto(self, contador):
```

O `_` no início é uma convenção: indica que este método é interno à classe. Ainda é possível chamá-lo de fora, mas ele foi pensado para ser usado pelo próprio coletor.

```python
if self.contador_anterior is not None and contador > self.contador_anterior + 1:
```

Essa condição tem duas partes:

```python
self.contador_anterior is not None
```

Evita comparar a primeira amostra com algo inexistente.

```python
contador > self.contador_anterior + 1
```

Verifica se o novo contador avançou mais de uma unidade.

Em uma coleta perfeita:

```text
100 → 101 → 102 → 103
```

Não há salto.

Em uma coleta com lacuna:

```text
100 → 104
```

Existe um salto, porque `104 > 100 + 1`.

```python
perdidas = int(contador - self.contador_anterior - 1)
```

Calcula quantas amostras ficaram no meio.

Exemplo:

```python
contador = 104
self.contador_anterior = 100
perdidas = int(104 - 100 - 1)
```

Resultado:

```python
perdidas = 3
```

As amostras ausentes seriam `101`, `102` e `103`.

```python
self.saltos_contador += 1
```

Registra mais um evento de salto.

```python
self.amostras_perdidas += perdidas
```

Soma a quantidade estimada de amostras ausentes.

```python
print(
    f"[Coletor] Salto no contador: "
    f"{self.contador_anterior:.0f} -> {contador:.0f} "
    f"({perdidas} amostras perdidas)"
)
```

Mostra uma mensagem no terminal. O `f` antes das aspas cria uma f-string: uma string que pode inserir variáveis dentro de `{}`.

O trecho:

```python
{contador:.0f}
```

Mostra o número como inteiro visual, sem casas decimais. O contador foi convertido para `float` no leitor serial, mas conceitualmente é um número inteiro.

```python
self.contador_anterior = contador
```

Esta linha fica fora do `if`, então sempre é executada. Ela atualiza a referência para a próxima comparação.

O método não conta como salto:

```text
100 → 100
100 → 99
100 → 0
```

Isso inclui repetição, retrocesso, reinício do Arduino ou overflow do contador. Ele só procura avanços maiores que um.

## Linhas 82 a 102: enviar dados para o gravador sem travar a coleta

```python
def _enfileirar_gravacao(self, linha):
```

Recebe uma amostra completa em formato de lista.

Exemplo:

```python
[
    tempo_arduino_us,
    timestamp,
    contador,
    ax, ay, az,
    gx, gy, gz,
]
```

```python
if self.fila_gravacao is None:
    return
```

Se não existe fila, não há gravador ativo. `return` encerra imediatamente esse método.

```python
try:
    self.fila_gravacao.put_nowait(linha)
```

`try` significa “tente executar”. `put_nowait()` coloca a amostra na fila sem esperar.

Isso é importante: se o disco estiver lento, o coletor não deve ficar parado esperando o CSV. Parar a thread serial poderia causar perda de dados.

```python
except Full:
```

Se a fila estiver cheia, `put_nowait()` lança a exceção `Full`, e este bloco é executado.

```python
self.amostras_nao_enfileiradas += 1
```

Registra que aquela amostra não seguirá para o arquivo CSV.

```python
if self.amostras_nao_enfileiradas % 1000 == 1:
```

Evita imprimir uma mensagem para cada perda. A condição será verdadeira na primeira perda, na perda 1001, 2001 e assim por diante.

```python
print(
    "[Coletor] Fila de gravacao cheia; "
    "amostras deixaram de ser enviadas ao CSV."
)
```

Informa que o problema é de persistência em disco, não necessariamente de leitura serial.

A ordem no loop principal é importante:

```python
self.buffer.adicionar(...)
self._enfileirar_gravacao(...)
```

Portanto, mesmo que a fila esteja cheia, a amostra já foi colocada no buffer e pode aparecer na interface.

## Linhas 104 a 137: início de uma sessão

```python
def executar(self):
```

Este é o método principal do coletor. Normalmente ele roda em uma thread criada pelo `SensorManager`:

```python
self.thread = Thread(
    target=self.coletor.executar,
    name="coletor-serial",
    daemon=True,
)
```

```python
self.rodando = True
```

Ativa a coleta.

```python
self.numero_amostras = 0
self.tempo_arduino_inicial_us = 0
self.tempo_arduino_anterior_us = 0
self.contador_anterior = None
self.saltos_contador = 0
self.amostras_perdidas = 0
self.amostras_nao_enfileiradas = 0
```

Reinicia as métricas da sessão anterior.

```python
self.hz_medio = 0
self.hz_inst = 0
self.hz_inst_suavizado = 0
```

Também reinicia as medidas de frequência.

```python
self.historico_hzs_inst.clear()
```

Remove as frequências instantâneas da sessão anterior. Sem essa linha, a média suavizada da nova sessão começaria misturada com valores antigos.

```python
print("Coletor iniciado")
```

Mostra no terminal que o loop de aquisição começou.

Um detalhe: este método não chama:

```python
self.buffer.limpar()
```

Logo, ao reiniciar uma sessão, o buffer ainda pode conter amostras da sessão anterior até ser gradualmente sobrescrito pelas novas.

## Linhas 142 a 147: receber amostras do leitor serial

```python
for tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz in ler_dados(
    porta=self.porta,
    baudrate=self.baudrate,
    deve_continuar=lambda: self.rodando,
):
```

`ler_dados()` é um gerador. Em vez de devolver tudo de uma vez, ele entrega uma amostra por vez usando `yield`.

A linha acima significa:

1. chame `ler_dados(...)`;
2. espere uma nova amostra serial;
3. separe os nove valores em variáveis;
4. execute o corpo do `for`;
5. espere a próxima amostra.

Os argumentos enviados são:

```python
porta=self.porta
```

Usa a porta guardada no construtor.

```python
baudrate=self.baudrate
```

Usa a velocidade serial guardada no construtor.

```python
deve_continuar=lambda: self.rodando
```

`lambda` é uma função pequena e sem nome. Esta equivale aproximadamente a:

```python
def deve_continuar():
    return self.rodando
```

O leitor serial consulta essa função repetidamente. Quando `self.rodando` passa a `False`, ele para de ler e fecha a porta serial.

## Linhas 148 a 160: parada, contagem e progresso

```python
if not self.rodando:
    print("Parando")
    break
```

Há uma segunda verificação de parada. Ela protege o caso em que uma amostra foi produzida pelo leitor exatamente antes de `parar()` mudar a chave para `False`.

```python
self.numero_amostras += 1
```

Conta a amostra atual como válida.

```python
self._registrar_salto(contador)
```

Compara o contador recebido com o anterior e atualiza as métricas de perda.

```python
if contador % 1000 == 0:
    print(f"[Coletor] : {contador}")
```

`%` calcula o resto de uma divisão. Quando o contador é múltiplo de 1000, o resto é zero.

Exemplos:

```python
1000 % 1000 == 0
2000 % 1000 == 0
```

A mensagem serve como indicador de progresso no terminal.

## Linhas 162 a 192: cálculo da frequência

```python
if self.numero_amostras == 1:
```

Na primeira amostra não há uma amostra anterior para comparar. Por isso o código apenas guarda referências de tempo.

```python
self.tempo_arduino_inicial_us = tempo_arduino_us
self.tempo_arduino_anterior_us = tempo_arduino_us
```

As duas referências recebem o tempo da primeira amostra.

Depois, nas amostras seguintes:

```python
else:
```

O coletor já pode calcular intervalos de tempo.

```python
dt_total = (
    tempo_arduino_us - self.tempo_arduino_inicial_us
) / 1_000_000
```

Calcula quanto tempo se passou desde a primeira amostra.

Exemplo:

```python
tempo_arduino_us = 1_500_000
self.tempo_arduino_inicial_us = 500_000
```

Então:

```python
dt_total = (1_500_000 - 500_000) / 1_000_000
dt_total = 1.0
```

Passou um segundo.

```python
if dt_total > 0:
    self.hz_medio = (self.numero_amostras - 1) / dt_total
```

Evita divisão por zero ou por tempo inválido.

O `- 1` existe porque a frequência depende de intervalos. Com 10 amostras existem 9 intervalos entre a primeira e a última.

Exemplo:

```python
self.numero_amostras = 201
dt_total = 1.0
```

Então:

```python
self.hz_medio = (201 - 1) / 1.0
self.hz_medio = 200.0
```

A taxa média foi de 200 Hz.

```python
dt_inst = (
    tempo_arduino_us - self.tempo_arduino_anterior_us
) / 1_000_000
```

Calcula apenas o intervalo entre a amostra atual e a imediatamente anterior.

```python
if dt_inst > 0:
    self.hz_inst = 1 / dt_inst
```

Converte o intervalo em frequência.

Exemplo: se a nova amostra chegou 5 ms depois da anterior:

```python
dt_inst = 0.005
self.hz_inst = 1 / 0.005
self.hz_inst = 200.0
```

Logo, a taxa instantânea é 200 Hz.

```python
self.historico_hzs_inst.append(self.hz_inst)
```

Adiciona a frequência instantânea ao histórico limitado a 100 valores.

```python
self.hz_inst_suavizado = (
    sum(self.historico_hzs_inst) / len(self.historico_hzs_inst)
)
```

Calcula a média do histórico.

- `sum(...)`: soma todos os Hz guardados.
- `len(...)`: conta quantos valores existem.
- divisão: produz a média.

Se o histórico contiver:

```python
[198, 201, 200, 199, 202]
```

A frequência suavizada ficará próxima de 200 Hz, mesmo que cada leitura isolada oscile um pouco.

```python
self.tempo_arduino_anterior_us = tempo_arduino_us
```

Atualiza a referência para que a próxima amostra seja comparada com a atual.

Se `dt_total` ou `dt_inst` for zero ou negativo, o código não atualiza o Hz correspondente. Isso evita uma divisão inválida, mas também significa que o valor anterior de Hz permanece visível até surgir um intervalo válido.

## Linhas 194 a 210: enviar a amostra para os dois destinos

```python
self.buffer.adicionar(
    tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz
)
```

Entrega a amostra ao buffer circular usado pela interface.

O método `adicionar()` em `BufferSensores`:

- grava os nove valores;
- usa um `Lock` para evitar que a interface leia uma linha pela metade;
- mantém até 10.000 amostras;
- sobrescreve a mais antiga quando chega ao limite.

```python
self._enfileirar_gravacao([
    tempo_arduino_us,
    timestamp,
    contador,
    ax,
    ay,
    az,
    gx,
    gy,
    gz,
])
```

Cria uma lista com a mesma amostra e tenta enviá-la para a fila do CSV.

A ordem é exatamente a mesma usada no buffer e no cabeçalho do CSV:

```python
[
    "tempo_arduino_us",
    "tempo_relogio_pc",
    "contador",
    "ax",
    "ay",
    "az",
    "gx",
    "gy",
    "gz",
]
```

A lista é separada do buffer porque os destinos têm responsabilidades diferentes:

```python
buffer → dados recentes para visualização
fila   → dados aguardando gravação em CSV
```

## Linhas 213 a 217: pedir a parada

```python
def parar(self):
```

Define o método usado para solicitar o fim da coleta.

```python
print("Aquisição encerrada.")
```

Mostra uma mensagem no terminal.

```python
self.rodando = False
```

Muda a chave de funcionamento para desligado.

Essa linha não força o fechamento físico da porta serial diretamente. O fechamento acontece porque `ler_dados()` vê que o callback agora retorna `False`, encerra seu gerador e sai deste bloco:

```python
with serial.Serial(...) as arduino:
```

Ao sair do `with`, Python fecha a porta serial automaticamente.

## Linhas 222 a 247: modo de execução direta

```python
if __name__ == "__main__":
```

Esse bloco só roda se o arquivo for iniciado diretamente:

```powershell
python -m sensor.coletor
```

Ele não roda quando outro arquivo apenas importa a classe:

```python
from sensor.coletor import Coletor
```

No uso normal da interface, quem controla o coletor é `sensor/manager.py`, não este bloco.

```python
from queue import Queue
from sensor.gravador_worker import GravadorWorker
```

Esses imports ficam dentro do bloco porque só são necessários no modo manual.

```python
fila_gravacao = Queue(maxsize=50_000)
```

Cria uma fila capaz de conter até 50.000 amostras esperando gravação.

```python
gravador = GravadorWorker(fila_gravacao)
gravador.start()
```

Cria e inicia a thread que consome a fila e escreve no CSV.

Começar o gravador antes do coletor evita que a coleta produza dados sem haver um consumidor preparado.

```python
collector = Coletor(fila_gravacao=fila_gravacao)
```

Cria um coletor e já entrega a ele a fila de gravação.

```python
try:
    collector.executar()
```

Inicia o loop de coleta.

```python
except KeyboardInterrupt:
    collector.parar()
```

`KeyboardInterrupt` acontece quando a pessoa pressiona `Ctrl+C` no terminal. Em vez de encerrar abruptamente, o programa pede uma parada organizada.

```python
finally:
    fila_gravacao.put(None)
    gravador.join()
```

`finally` roda tanto em caso normal quanto após `Ctrl+C`.

```python
fila_gravacao.put(None)
```

Coloca a sentinela `None` na fila. O `GravadorWorker` interpreta esse valor assim:

```python
if linha is None:
    break
```

Antes de terminar, ele salva o último lote parcial e fecha o arquivo CSV.

```python
gravador.join()
```

Faz o programa esperar a thread do gravador terminar. Isso impede que o programa feche antes de salvar as últimas amostras.

O encerramento normal fica assim:

```text
Coletor para
   ↓
Nenhuma nova amostra entra na fila
   ↓
None entra na fila
   ↓
Gravador consome o que falta
   ↓
CSV é fechado
   ↓
Programa termina
```

O ponto mais importante do script é a separação de responsabilidades:

```python
ler_dados(...)                 # recebe e converte a serial
self.buffer.adicionar(...)     # alimenta a interface
self._enfileirar_gravacao(...) # encaminha para CSV
```

Essa separação reduz o risco de uma gravação lenta no disco prejudicar a leitura do sensor.
