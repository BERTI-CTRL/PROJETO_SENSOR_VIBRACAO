# Firmware Arduino e MPU6050

Este documento explica o arquivo [arduino/mpu-6050/mpu-6050.ino](../arduino/mpu-6050/mpu-6050.ino), relacionando cada parte importante com os dois documentos técnicos mantidos na pasta arduino.

## 1. Os PDFs e como usá-los

| Documento | Para que serve | Quando consultar |
|---|---|---|
| [MPU-6000/MPU-6050 Product Specification](<../arduino/mpu-6050_datasheet_v3 4.pdf>) | Descreve capacidades, faixas, sensibilidades, ruído, taxa de saída e limites elétricos/físicos. | Para escolher escala, avaliar ruído, frequência e precisão esperada. |
| [MPU-6000/MPU-6050 Register Map and Descriptions](<../arduino/MPU-6000-Register-Map1 (1).pdf>) | Descreve cada registrador, endereço, bits e valores de configuração. | Para entender ou alterar cada chamada Wire.write do firmware. |

A diferença é importante:

~~~text
Datasheet:       “o que o sensor é capaz de fazer”
Register Map:    “como pedir ao sensor que faça isso por meio dos registradores”
Firmware .ino:   “quais capacidades foram escolhidas neste projeto”
~~~

Consultar somente o Datasheet ajuda a entender os limites do sensor, mas não informa todos os endereços de registradores. Consultar somente o Register Map permite programar os registros, mas não explica com a mesma profundidade o desempenho e as tolerâncias.

## 2. Papel do firmware no projeto

O firmware executa quatro tarefas:

1. inicia a serial e o barramento I2C;
2. acorda e configura o MPU6050;
3. lê aceleração, temperatura e giro do sensor;
4. envia aceleração e giro por USB em uma linha CSV.

Fluxo:

~~~text
MPU6050
   │ I2C
   ▼
mpu-6050.ino
   │ Serial USB, 115200 baud
   ▼
sensor/serial_reader.py
   ▼
coletor.py → buffer → janela / CSV
~~~

O firmware não calcula estatísticas, não salva CSV e não abre gráficos. Essas tarefas pertencem ao Python.

## 3. Biblioteca e endereço I2C

No início do arquivo:

~~~cpp
#include <Wire.h>
const int MPU = 0x68;
~~~

### Wire.h

Wire é a biblioteca Arduino para comunicação I2C.

**Por que usar I2C:** o MPU6050 expõe seus registradores por I2C. O Arduino escreve o endereço do registrador que quer acessar e depois lê ou escreve bytes nesse endereço.

### Endereço 0x68

0x68 é o endereço I2C mais comum do MPU6050. Ele depende do pino AD0 do chip/módulo.

**Por que isso importa:** se o Arduino não recebe resposta no endereço 0x68, a causa pode ser ligação elétrica, alimentação, endereço diferente ou módulo com problema. Alguns módulos podem usar 0x69 quando AD0 está em nível alto.

## 4. Variáveis e contador

O firmware declara:

~~~cpp
static unsigned long contador = 0;
float a_x, a_y, a_z, temperatura, Gyrx, Gyry, Gyrz;
~~~

- contador identifica a ordem de cada amostra;
- a_x, a_y e a_z guardam aceleração bruta;
- Gyrx, Gyry e Gyrz guardam giro bruto;
- temperatura recebe a leitura de temperatura, embora ela ainda não seja enviada pela serial.

### Por que o contador é importante

O contador permite ao Python detectar uma sequência não contínua. Se o projeto recebe 1000 e depois 1005, existem quatro amostras ausentes.

O coletor Python usa isso para incrementar amostras_perdidas e informar saltos no terminal.

### Limite do contador

unsigned long possui tamanho finito. Em uma execução muito longa ele pode voltar a zero. Para ensaios curtos isso não é um problema, mas para monitoramento contínuo esse overflow deve ser tratado no Python.

## 5. Inicialização: setup()

### 5.1 Serial

~~~cpp
Serial.begin(115200);
~~~

Esse comando define a velocidade da porta serial.

**Por que 115200:** é uma taxa comum e suficientemente alta para transportar linhas com contador, tempo e seis medidas. A taxa deve ser exatamente a mesma no Python:

~~~python
Coletor(porta="COM4", baudrate=115200)
~~~

Se os valores forem diferentes, a leitura pode falhar, vir corrompida ou não produzir linhas válidas.

### 5.2 Início do I2C

~~~cpp
Wire.begin();
~~~

Isso inicializa o barramento I2C do Arduino.

**Por que:** sem inicializar I2C, as chamadas Wire.beginTransmission, Wire.write e Wire.requestFrom não conseguem conversar com o MPU6050.

### 5.3 Teste de presença

~~~cpp
Wire.beginTransmission(MPU);
if (Wire.endTransmission() == 0) {
    delay(10000);
} else {
    Serial.println("Erro MPU");
}
~~~

Wire.endTransmission retorna zero quando o dispositivo respondeu ao endereço I2C.

**Por que fazer esse teste:** ele verifica se existe um dispositivo respondendo em 0x68 antes de iniciar leituras.

**O que ele não verifica:** esse teste não confirma que o dispositivo é realmente um MPU6050 nem que todos os registradores funcionam. Uma verificação mais forte leria o registrador WHO_AM_I.

### 5.4 Atraso de 10 segundos

O firmware executa delay(10000) quando o sensor responde.

**Possível intenção:** aguardar estabilização do hardware e dar tempo para abrir a serial.

**Consequência:** o sensor só começa a enviar dados aproximadamente 10 segundos depois do boot. O serial_reader.py espera apenas 2 segundos e limpa o buffer; portanto, é normal a janela ficar inicialmente sem amostras.

Para testes rápidos, esse atraso pode ser reduzido ou removido depois de confirmar que o sistema inicia de forma estável.

## 6. Acordar o MPU6050: registrador 0x6B

O código faz:

~~~cpp
Wire.beginTransmission(MPU);
Wire.write(0x6B);
Wire.write(0);
Wire.endTransmission(true);
~~~

Segundo o Register Map, 0x6B é o registrador PWR_MGMT_1, de gerenciamento de energia.

Escrever zero limpa o bit SLEEP e acorda o sensor.

**Por que isso é necessário:** o MPU6050 inicia em modo de sono. Sem essa escrita, o sensor pode não atualizar os registradores de aceleração e giro.

### O que essa escolha também significa

Ao escrever zero em todo o registrador, o firmware usa a configuração de clock associada ao valor padrão desse campo. O código não escolhe explicitamente outra fonte de clock, não ativa ciclo de baixo consumo e não configura reset.

Para uma aplicação didática isso é uma inicialização simples. Para uma aplicação mais exigente, é recomendado documentar a fonte de clock e os modos de energia escolhidos.

## 7. Configuração do giroscópio: registrador 0x1B

O firmware usa:

~~~cpp
Wire.beginTransmission(MPU);
Wire.write(0x1B);
Wire.write(0b00011000);
Wire.endTransmission(true);
~~~

No Register Map, 0x1B é GYRO_CONFIG.

Os bits FS_SEL selecionam a faixa do giroscópio:

| Valor dos bits | Faixa |
|---|---:|
| 00 | ±250 °/s |
| 01 | ±500 °/s |
| 10 | ±1000 °/s |
| 11 | ±2000 °/s |

O valor 0b00011000 coloca FS_SEL em 11, selecionando ±2000 °/s.

### Por que escolher ±2000 °/s

Uma faixa maior reduz o risco de saturação em movimentos rápidos, impactos com rotação ou ensaios agressivos.

### Qual é o custo

Faixa maior significa menor sensibilidade por unidade de rotação. No caso de ±2000 °/s, a conversão usada é:

~~~text
giro_em_°_por_s = valor_bruto / 16,4
~~~

Se o objetivo for medir rotações lentas com maior resolução, uma faixa menor pode ser mais apropriada. Mas, se a rotação exceder a faixa, ocorre saturação e a informação do pico é perdida.

### Relação com o Datasheet

O Datasheet informa as faixas disponíveis e os fatores de sensibilidade. O Register Map informa que FS_SEL está em GYRO_CONFIG e quais bits devem ser escritos.

Sempre que mudar o valor de 0x1B, atualize o divisor utilizado no envio serial:

| Faixa configurada | Divisor correto |
|---|---:|
| ±250 °/s | 131 |
| ±500 °/s | 65,5 ou 65,6 |
| ±1000 °/s | 32,8 |
| ±2000 °/s | 16,4 |

## 8. Configuração do acelerômetro: registrador 0x1C

O código faz:

~~~cpp
Wire.beginTransmission(MPU);
Wire.write(0x1C);
Wire.write(0b00011000);
Wire.endTransmission(true);
~~~

No Register Map, 0x1C é ACCEL_CONFIG.

Os bits AFS_SEL selecionam a faixa do acelerômetro:

| Valor dos bits | Faixa |
|---|---:|
| 00 | ±2 g |
| 01 | ±4 g |
| 10 | ±8 g |
| 11 | ±16 g |

O valor 0b00011000 coloca AFS_SEL em 11, selecionando ±16 g.

### Por que escolher ±16 g

A faixa de ±16 g reduz a chance de saturar em choques e vibrações intensas.

### Qual é o custo

A resolução por g é menor do que nas faixas menores. Para ±16 g, a conversão usada é:

~~~text
aceleracao_em_g = valor_bruto / 2048
~~~

Para vibrações suaves, pode ser melhor usar ±2 g ou ±4 g, desde que os picos esperados não ultrapassem essa faixa.

| Faixa configurada | Divisor correto |
|---|---:|
| ±2 g | 16384 |
| ±4 g | 8192 |
| ±8 g | 4096 |
| ±16 g | 2048 |

### Relação com calibração

Escolher o divisor correto apenas converte o valor bruto para unidade física; isso não elimina offset e erro de ganho particulares do módulo. A calibração documentada em calibração/guia_calibracao_mpu6050.md deve ser aplicada depois dessa conversão.

## 9. Leituras de dados: início em 0x3B

No loop:

~~~cpp
Wire.beginTransmission(MPU);
Wire.write(0x3B);
Wire.endTransmission(false);
Wire.requestFrom(MPU, 14, true);
~~~

Segundo o Register Map, 0x3B é ACCEL_XOUT_H, o primeiro registrador do bloco de dados.

Os 14 bytes solicitados são:

| Ordem | Registradores | Conteúdo |
|---:|---|---|
| 1 e 2 | 0x3B e 0x3C | aceleração X |
| 3 e 4 | 0x3D e 0x3E | aceleração Y |
| 5 e 6 | 0x3F e 0x40 | aceleração Z |
| 7 e 8 | 0x41 e 0x42 | temperatura |
| 9 e 10 | 0x43 e 0x44 | giro X |
| 11 e 12 | 0x45 e 0x46 | giro Y |
| 13 e 14 | 0x47 e 0x48 | giro Z |

### Por que pedir 14 bytes em sequência

O sensor disponibiliza os dados consecutivamente no mapa de registradores. Uma única leitura em bloco é mais eficiente e reduz a chance de X, Y e Z serem lidos em momentos muito diferentes.

### Repeated start

Wire.endTransmission(false) não encerra a comunicação com uma condição de parada antes da leitura. Isso implementa o padrão de informar o registrador e, em seguida, solicitar os bytes.

**Por que:** essa sequência é o modo usual de leitura de registradores I2C e mantém a transação coerente.

### Leitura incompleta

Depois de `Wire.requestFrom(MPU, 14, true)`, o firmware verifica `Wire.available() < 14` e retorna sem enviar uma linha.

**Por que:** cada amostra exige os 14 bytes completos. Sem essa verificação, uma falha parcial no I2C poderia reutilizar valores anteriores das variáveis e registrá-los como se fossem uma nova medida. O contador também só é incrementado após a leitura completa.

## 10. Conversão de bytes para números

O firmware usa, por exemplo:

~~~cpp
a_x = Wire.read() << 8 | Wire.read();
~~~

Cada medida ocupa dois bytes: o byte alto e o byte baixo. O deslocamento de 8 bits e a operação OR recompõem a palavra de 16 bits.

**Por que:** o MPU6050 possui ADC de 16 bits e envia cada medida em dois registradores consecutivos. Ler apenas um byte perderia precisão e sinal.

A variável temperatura também é lida, mas o firmware atual não a converte nem a envia pela serial.

**Por que registrar temperatura no futuro:** ela pode ajudar a explicar variações de offset, especialmente no giroscópio, e apoiar uma calibração dependente da temperatura.

## 11. Formato serial enviado

Depois de ler e converter as medidas, o firmware envia:

~~~text
contador,tempo_arduino_us,ax,ay,az,gx,gy,gz
~~~

Exemplo:

~~~text
1,10002956,1.00,-0.01,-0.04,-3.48,0.12,-0.24
~~~

A ordem é importante. O leitor Python espera exatamente oito campos:

~~~python
contador, tempo_arduino_us, ax, ay, az, gx, gy, gz
~~~

### Por que usar CSV

- é simples de inspecionar no Serial Monitor;
- é fácil de dividir com split por vírgula no Python;
- pode ser salvo diretamente em arquivos CSV;
- torna o protocolo visível e fácil de depurar.

### Cuidados decisivos

- Não adicione Serial.print de depuração no mesmo canal dos dados.
- Mensagens como Erro MPU e frases livres não possuem oito números separados por vírgulas; o Python as descarta como linha inválida.
- Mantenha uma quebra de linha no final de cada amostra. O Python usa readline e depende dela para separar mensagens.
- Se mudar a ordem ou a quantidade de campos, atualize todo o caminho de dados.

O caminho a atualizar é:

~~~text
mpu-6050.ino
   ↓
sensor/serial_reader.py
   ↓
sensor/coletor.py
   ↓
sensor/buffers.py
   ↓
sensor/gravador.py e CSV
   ↓
realtime/janela.py e grafico/plotar_csv.py
~~~

## 12. Taxa de amostragem e filtros: o que o firmware ainda não define

O Register Map descreve registradores que não são configurados explicitamente no firmware:

| Registrador | Endereço | Função |
|---|---:|---|
| SMPLRT_DIV | 0x19 | divisor da taxa de amostragem |
| CONFIG | 0x1A | filtro digital passa-baixa e sincronismo |
| WHO_AM_I | 0x75 | identificação do dispositivo |

### SMPLRT_DIV

A taxa interna é determinada pela configuração do sensor e pelo divisor de amostragem. O Register Map descreve a relação:

~~~text
sample rate = gyroscope output rate / (1 + SMPLRT_DIV)
~~~

O firmware atual não escreve em 0x19. Portanto, ele não fixa explicitamente uma taxa de saída do MPU6050.

### CONFIG e DLPF

O registrador 0x1A configura o filtro digital passa-baixa, DLPF, para acelerômetro e giroscópio.

O firmware atual não escreve em 0x1A. Isso significa que o filtro não está explicitamente escolhido pelo projeto.

**Por que isso importa para vibração:** o filtro pode atenuar vibrações de maior frequência. Se ele for muito baixo, parte do sinal de interesse desaparece; se for muito alto, mais ruído entra na medida. Antes de uma calibração dinâmica, a taxa e o filtro devem ser conhecidos e mantidos constantes.

### Taxa real do sistema

Mesmo que o MPU6050 seja configurado para uma taxa interna, a taxa registrada no CSV depende também de:

- velocidade do I2C;
- tempo de execução do loop Arduino;
- formatação dos números em Serial.print;
- limite de 115200 baud;
- leitura do Python.

Por isso, o projeto calcula Hz usando micros do Arduino e exibe Hz Médio, Hz Inst e Hz Suav na janela.

**Regra prática:** não deduza a taxa apenas do código. Meça a taxa efetiva e confirme se ela é suficiente para a frequência de vibração que se quer estudar.

### Possível reset do MPU6050 durante o ensaio

Se um eixo parado muda de aproximadamente `1 g` para `8 g` depois de um movimento forte, e os valores do giro também ficam cerca de oito vezes maiores, suspeite de reset do MPU6050. O chip pode voltar às escalas padrão (`±2 g` e `±250 °/s`), enquanto o firmware continua dividindo como se estivesse em `±16 g` e `±2000 °/s`.

O código atual configura as escalas apenas no `setup()`. Como verificação futura, leia periodicamente `ACCEL_CONFIG` (`0x1C`) e `GYRO_CONFIG` (`0x1B`); se não forem `0b00011000`, reconfigure o sensor e investigue alimentação, cabo e I²C. Essa proteção não substitui corrigir a causa elétrica de um reset.

## 13. O que modificar com segurança

### Mudar fundo de escala

Ao mudar GYRO_CONFIG ou ACCEL_CONFIG:

1. escolha os bits corretos no Register Map;
2. atualize o divisor da conversão;
3. registre a alteração nos metadados de calibração;
4. reveja a escala visual dos gráficos;
5. repita calibração e validação se o uso mudou.

**Por que:** um divisor incompatível gera números com unidade errada e pode invalidar toda a análise.

### Adicionar temperatura ao CSV

É possível enviar temperatura, mas a alteração exige atualizar o protocolo inteiro.

1. converter a temperatura conforme a fórmula do Datasheet;
2. adicioná-la à linha Serial;
3. mudar a validação de oito campos no serial_reader;
4. encaminhá-la no coletor e buffer;
5. criar coluna no CSV;
6. atualizar a janela e o plotador se ela for exibida.

**Por que:** mudar somente o Arduino faz o leitor Python descartar todas as linhas, pois ele espera exatamente oito campos.

### Configurar taxa e filtro

Para uma evolução de vibração, defina explicitamente SMPLRT_DIV e CONFIG, documente os valores e valide novamente o sistema em bancada.

**Por que:** frequência de amostragem e filtro fazem parte da medição. Alterá-los muda a resposta em frequência e pode tornar uma calibração anterior inválida.

## 14. Limitações e melhorias recomendadas

| Situação atual | Consequência | Melhoria futura |
|---|---|---|
| apenas resposta I2C em 0x68 | não confirma identidade do chip | ler WHO_AM_I |
| delay de 10 segundos | início lento | reduzir/remover após validação |
| filtro e taxa não explícitos | resposta dinâmica não totalmente controlada | configurar CONFIG e SMPLRT_DIV |
| temperatura não enviada | difícil compensar drift térmico | incluir coluna de temperatura |
| sem FIFO | leitura depende do tempo do loop | estudar FIFO para aquisições mais controladas |
| sem calibração aplicada | unidades corretas, mas com erros particulares | aplicar coeficientes no coletor |
| escala ±16 g e ±2000 °/s | maior margem, menor resolução | selecionar faixa conforme ensaio |

Essas limitações não impedem o uso didático atual. Elas indicam onde evoluir quando o projeto passar de visualização para medição quantitativa de vibração.

## 15. Checklist para alterar o firmware

- [ ] Consulte o Register Map para confirmar endereço e bits.
- [ ] Consulte o Datasheet para confirmar escala, sensibilidade e limites.
- [ ] Mantenha o baud rate igual no Arduino e no Python.
- [ ] Não misture textos de depuração com linhas CSV.
- [ ] Se mudar campos do CSV, atualize todos os consumidores Python.
- [ ] Meça a taxa real depois de qualquer alteração.
- [ ] Verifique se há saltos no contador.
- [ ] Repita a calibração se a escala, filtro, taxa ou montagem forem alterados.

## Referências locais

- [Firmware Arduino](../arduino/mpu-6050/mpu-6050.ino)
- [Datasheet do MPU6050](<../arduino/mpu-6050_datasheet_v3 4.pdf>)
- [Register Map do MPU6050](<../arduino/MPU-6000-Register-Map1 (1).pdf>)
- [Guia de calibração](../calibração/guia_calibracao_mpu6050.md)
- [Leitor serial Python](../sensor/serial_reader.py)
- [Coletor Python](../sensor/coletor.py)
