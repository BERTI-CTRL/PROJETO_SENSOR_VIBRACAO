# MPU-6000/MPU-6050 Product Specification

> [!abstract] Leitura dirigida
>
> Esta nota usa o [mpu-6050_datasheet_v3 4.pdf](<../../arduino/mpu-6050_datasheet_v3 4.pdf>) apenas para fundamentar decisões reais de [[arduino_mpu6050]]. Não é uma explicação integral do datasheet nem uma lista de recursos que o firmware ainda não utiliza.

## Para que serve este PDF

Enquanto [[mpu6050_register_map]] diz “qual registrador e quais bits”, o *Product Specification* responde “qual é a escala, sensibilidade, interface e limite físico associado à escolha”. Os dois documentos devem ser lidos juntos sempre que uma configuração do `.ino` mudar.

## Mapa das páginas usadas

| PDF p. | Informação relevante | Consequência no firmware |
| --- | --- | --- |
| 7–8 | MPU6050 integra acelerômetro e giroscópio de três eixos, com ADCs de 16 bits e I2C no MPU6050 | Justifica os seis eixos e a leitura digital por `Wire`. |
| 10 | Faixas programáveis dos dois sensores | Contextualiza a escolha de fundo de escala feita em registradores. |
| 12 | Faixas e sensibilidades do giroscópio | Justifica ±2000 °/s e o divisor `16.4`. |
| 13 | Faixas e sensibilidades do acelerômetro | Justifica ±16 g e o divisor `2048`. |
| 15 | Frequência I2C e endereços conforme AD0 | Justifica `0x68` e o uso do barramento I2C. |
| 17 | Taxas internas segundo filtro e fonte de clock | Explica por que taxa real não deve ser presumida pelo código. |
| 34–36 | START, STOP, ACK, repeated START e leitura de registrador | Fundamenta o padrão usado por `Wire` para ler o bloco de dados. |

As referências apontam para a numeração do visualizador do PDF, que também aparece como “n of 52” no cabeçalho.

## Código explicado a partir das escolhas físicas

### Seis eixos, dados de 16 bits e I2C

Na [PDF p. 7](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=7>), o MPU-60X0 é descrito como um dispositivo que integra um giroscópio e um acelerômetro, cada um com três eixos. A página também informa três ADCs de 16 bits para cada conjunto. Isso dá o contexto físico da sequência transmitida pelo `.ino`:

```text
ax, ay, az, gx, gy, gz
```

Na [PDF p. 8](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=8>), a tabela de diferenças diz que o MPU6050 suporta I2C, enquanto SPI é característica do MPU6000. Por isso o firmware inclui `Wire.h` e usa `Wire.begin()`; essa não é uma escolha de formatação, e sim a interface prevista para esse componente.

Os 16 bits explicam a recomposição de dois bytes em cada eixo no `.ino`. Para descobrir a ordem dos registradores, consulte [[mpu6050_register_map]]; para interpretar o número bruto depois de recomposto, consulte as tabelas de sensibilidade abaixo.

### Por que existem fundos de escala

A [PDF p. 10](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=10>) informa que ambas as famílias de sensores têm faixa programável. Escolher fundo de escala é uma troca:

- uma faixa maior tolera movimentos maiores antes de saturar;
- uma faixa menor representa pequenas variações com mais contagens digitais por unidade física;
- nenhuma opção é universalmente “melhor”: a faixa deve corresponder ao ensaio.

O firmware escolhe as maiores faixas disponíveis para aceleração e giro. Essa decisão protege ensaios com picos altos, mas reduz a resolução nominal para vibrações suaves. [[teoria_vibração]] explica por que saturação e resolução mudam o significado físico de um gráfico.

### Giroscópio: ±2000 °/s e o divisor `16.4`

No `.ino`:

```cpp
Wire.write(0x1B);
Wire.write(0b00011000);
// ...
Serial.print(Gyrx / 16.4);
```

A seleção dos bits pertence a [[mpu6050_register_map]]. A [PDF p. 12](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=12>) fornece a ponte para a unidade física:

| `FS_SEL` | Faixa | Sensibilidade nominal |
| --- | --- | --- |
| 0 | ±250 °/s | 131 LSB/(°/s) |
| 1 | ±500 °/s | 65,5 LSB/(°/s) |
| 2 | ±1000 °/s | 32,8 LSB/(°/s) |
| 3 | ±2000 °/s | 16,4 LSB/(°/s) |

Como o `.ino` escreve `FS_SEL=3`, cada 16,4 contagens brutas equivale nominalmente a um grau por segundo. Dividir por `16.4` é, portanto, a conversão compatível com o registrador configurado.

> [!warning] “Nominal” não significa calibração perfeita
>
> A mesma página especifica tolerância do fator de sensibilidade e offset de taxa zero, inclusive com variação de temperatura. O divisor torna a unidade correta pela escala escolhida; não elimina erro particular do módulo. Para análise quantitativa, use uma estratégia de calibração e registre suas condições.

### Acelerômetro: ±16 g e o divisor `2048`

No `.ino`:

```cpp
Wire.write(0x1C);
Wire.write(0b00011000);
// ...
Serial.print(a_x / 2048);
```

A [PDF p. 13](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=13>) fornece a tabela equivalente:

| `AFS_SEL` | Faixa | Sensibilidade nominal |
| --- | --- | --- |
| 0 | ±2 g | 16384 LSB/g |
| 1 | ±4 g | 8192 LSB/g |
| 2 | ±8 g | 4096 LSB/g |
| 3 | ±16 g | 2048 LSB/g |

Como `AFS_SEL=3`, a conversão por 2048 gera a unidade `g` esperada por [[esquema-csv]] e pelos limites aplicados em [[testar_dados]]. A página também documenta tolerância inicial de zero-g, variação térmica e sensibilidade entre eixos; por isso um módulo parado pode não fornecer exatamente zero nos eixos horizontais.

> [!note] A gravidade é parte da leitura
>
> Com o módulo parado, um eixo alinhado verticalmente tende a registrar aproximadamente uma unidade `g`. Isso não indica vibração; é a contribuição da gravidade à aceleração específica. A distinção conceitual é desenvolvida em [[teoria_vibração]].

### Endereço I2C e o valor `0x68`

O firmware declara:

```cpp
const int MPU = 0x68;
```

A [PDF p. 15](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=15>) informa os endereços I2C de sete bits:

| Estado de AD0 | Endereço binário | Endereço hexadecimal |
| --- | --- | --- |
| baixo | `1101000` | `0x68` |
| alto | `1101001` | `0x69` |

Logo, `0x68` não é um valor genérico para qualquer MPU6050: ele depende da ligação do pino AD0 no módulo. A mesma página informa I2C padrão de 100 kHz e modo rápido de 400 kHz; a frequência efetiva é controlada pela plataforma `Wire` e não é configurada diretamente neste `.ino`.

### Leitura I2C em duas fases

O trecho abaixo aparenta ter poucas linhas, mas representa um protocolo completo:

```cpp
Wire.beginTransmission(MPU);
Wire.write(0x3B);
Wire.endTransmission(false);
Wire.requestFrom(MPU, 14, true);
```

As [PDF pp. 34–36](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=34>) definem START, STOP, ACK e repeated START. Para ler registradores internos, o mestre envia endereço do chip em modo escrita, envia o endereço do registrador, emite novo START, endereça o chip em modo leitura e recebe bytes até concluir com NACK e STOP.

`Wire.endTransmission(false)` instrui a biblioteca a não emitir STOP entre as duas fases; a próxima operação cria a sequência contínua de leitura. O chip, por sua vez, incrementa o endereço dos registradores durante a leitura em rajada, o que permite começar em `0x3B` e receber 14 bytes consecutivos. A lista dos 14 bytes está em [[mpu6050_register_map]].

### Taxa interna, filtro e taxa observada não são a mesma coisa

A [PDF p. 17](<../../arduino/mpu-6050_datasheet_v3 4.pdf#page=17>) relaciona taxas internas ao filtro digital e à fonte de clock. Ela mostra, por exemplo, taxas de giroscópio distintas para `DLPFCFG=0` e para outras configurações.

O `.ino` não escreve em `CONFIG` nem em `SMPLRT_DIV`. Logo, ele não documenta uma taxa de sensor explicitamente escolhida. A taxa que aparece em [[janela]] e [[tempo-frequencia-e-perdas]] é medida a partir de `micros()` do Arduino, refletindo também I2C, execução do laço e transmissão serial.

> [!warning] Não deduza frequência somente da taxa de serial
>
> `115200` é a velocidade de transporte de bits pela USB serial, não a frequência de amostragem física. A regra segura é medir o intervalo entre amostras e verificar se ele atende ao fenômeno estudado.

## Recursos deliberadamente fora do escopo do `.ino`

O datasheet também descreve FIFO, DMP, interrupções, filtros programáveis, modos de baixo consumo, sensores auxiliares e limites elétricos. Eles são relevantes em projetos mais avançados, mas não aparecem no código atual. Esta nota não os explica para evitar apresentar capacidade do chip como funcionalidade pronta do sistema.

Se uma dessas capacidades for adicionada no futuro, atualize [[arduino_mpu6050]], [[mpu6050_register_map]], [[protocolo-serial]] e [[teoria_vibração]] conforme o impacto real.

## Insights para outros projetos

- **Escala é uma decisão de experimento:** selecione-a antes de coletar e documente-a junto ao CSV.
- **Divisores têm origem rastreável:** `2048` e `16.4` vêm de tabelas de sensibilidade, não de tentativa e erro.
- **Interface e medição são camadas diferentes:** I2C transporta registradores; a física determina como transformar suas contagens em unidade.
- **Taxa declarada não é taxa medida:** qualquer análise de vibração precisa conferir a cadência real do sinal registrado.

## Resumo mental

Este PDF justifica o sentido físico das escolhas do firmware. Ele confirma que o MPU6050 entrega seis eixos digitais de 16 bits por I2C, fornece as escalas e sensibilidades que tornam `2048` e `16.4` corretos para a configuração atual, define por que AD0 baixo leva a `0x68` e descreve a sequência I2C usada para buscar o bloco de dados. Para endereços e bits específicos, a referência complementar é [[mpu6050_register_map]].
#PROJETO_SENSOR_VIBRAÇÃO
