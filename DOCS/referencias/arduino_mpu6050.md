# mpu-6050.ino

> [!abstract] Em uma frase
>
> `arduino/mpu-6050/mpu-6050.ino` acorda o MPU6050, seleciona as escalas de ±16 g e ±2000 °/s, lê em bloco os seis eixos e transmite cada amostra como uma linha CSV pela USB serial.

## Papel no projeto

O firmware é o começo da cadeia de medição. Ele conversa com o chip pelo barramento I2C e transforma registradores binários em oito campos separados por vírgulas:

```text
contador,tempo_arduino_us,ax,ay,az,gx,gy,gz
```

[[serial_reader]] reconhece exatamente esses oito campos e cria a tupla Python de nove valores ao acrescentar o timestamp do PC. Depois, [[coletor]] calcula frequência e perdas, [[gravador]] preserva a sessão no formato descrito em [[esquema-csv]], e [[janela]] a mostra em tempo real. Mudar a ordem, a quantidade ou a unidade de qualquer campo no firmware exige rever todos esses consumidores.

## O que o firmware usa dos PDFs

| Decisão no código | Fonte técnica precisa | Onde é explicada nesta documentação |
| --- | --- | --- |
| Endereço I2C `0x68` | Product Specification, PDF p. 15: AD0 baixo corresponde ao endereço binário `1101000` | [[mpu6050_product_specification]] |
| Escrita em `0x6B` para acordar | Register Map, PDF pp. 40–41: `PWR_MGMT_1`, bits `SLEEP` e `CLKSEL` | [[mpu6050_register_map]] |
| Faixa de giro ±2000 °/s | Register Map, PDF p. 14: `GYRO_CONFIG`; Product Specification, PDF p. 12: sensibilidade `16,4 LSB/(°/s)` | [[mpu6050_register_map]] e [[mpu6050_product_specification]] |
| Faixa de aceleração ±16 g | Register Map, PDF p. 15: `ACCEL_CONFIG`; Product Specification, PDF p. 13: sensibilidade `2048 LSB/g` | [[mpu6050_register_map]] e [[mpu6050_product_specification]] |
| Leitura em bloco iniciada em `0x3B` | Register Map, PDF pp. 29–31: aceleração, temperatura e giro em 14 bytes consecutivos | [[mpu6050_register_map]] |
| Sequência I2C de leitura | Product Specification, PDF pp. 34–36: START, endereço, registrador, repeated START e leitura | [[mpu6050_product_specification]] |

Essas são as referências relevantes para **este** `.ino`; os PDFs têm muito mais recursos, mas eles não fazem parte do comportamento implementado.

## Fluxo mental

```text
Arduino inicia
   │
   ├─ Serial.begin(230400) ──► linha CSV para o PC
   │
   └─ Wire.begin() ──────────► I2C com MPU6050 em 0x68
                                  │
                                  ▼
                     acordar + selecionar fundos de escala
                                  │
                                  ▼
loop: apontar 0x3B → solicitar 14 bytes → validar tamanho
                                  │
                                  ▼
             recompor valores brutos → converter por sensibilidade
                                  │
                                  ▼
        contador,micros(),ax,ay,az,gx,gy,gz + quebra de linha
```

## Código explicado, na ordem do arquivo

### Inclusão, endereço e estado que sobrevive ao `loop()`

```cpp
#include <Wire.h>

const int MPU = 0x68;
static unsigned long contador = 0;
float a_x, a_y, a_z, temperatura, Gyrx, Gyry, Gyrz;
```

`Wire.h` fornece as operações I2C da placa Arduino. O endereço `0x68` pressupõe que o pino AD0 do MPU6050 esteja em nível baixo; se ele estiver alto, a especificação indica o endereço `0x69`. A escolha e sua implicação elétrica estão detalhadas em [[mpu6050_product_specification]].

`static unsigned long contador` existe uma única vez e não é reiniciado entre chamadas de `loop()`. Ele dá sequência às amostras para que [[coletor]] possa identificar lacunas. Como todo contador finito, eventualmente pode ocorrer overflow; ensaios longos devem considerar essa hipótese.

As sete variáveis `float` guardam valores lidos dos registradores. Temperatura é consumida para manter o alinhamento da leitura em bloco, mas não entra na linha serial atual.

### `setup()`: serial e barramento I2C

```cpp
Serial.begin(230400);
Wire.begin();
```

`Serial.begin(230400)` abre a porta USB serial na taxa escolhida pelo firmware. O programa Python usa o mesmo valor por meio de `BAUD_RATE` em `sensor/config.py`; a divergência não é corrigida automaticamente. `Wire.begin()` configura a placa como mestre do I2C para alcançar o MPU6050.

O teste seguinte tenta iniciar uma transmissão e interpreta retorno zero como ACK:

```cpp
Wire.beginTransmission(MPU);
if (Wire.endTransmission() == 0) {
  delay(10000);
} else {
  Serial.println("Erro MPU");
}
```

Ele verifica se algum dispositivo responde nesse endereço, mas não confirma que seja realmente um MPU6050. A mensagem livre `Erro MPU` não é uma amostra: [[serial_reader]] a descarta por não conter oito números CSV. O atraso de dez segundos dá tempo de inicialização, mas faz a interface ficar sem dados logo após abrir a porta.

> [!warning] Diagnóstico não interrompe a aquisição
>
> Após imprimir `Erro MPU`, o código ainda tenta configurar e ler o endereço. Para uma aplicação mais robusta, uma falha de ACK deveria impedir o restante da aquisição ou acionar uma nova tentativa controlada. Esta é uma melhoria sugerida, não um comportamento presente.

### `PWR_MGMT_1`: acordar o chip

```cpp
Wire.beginTransmission(MPU);
Wire.write(0x6B);
Wire.write(0);
Wire.endTransmission(true);
```

O endereço `0x6B` é `PWR_MGMT_1`. Escrever zero limpa `SLEEP` e deixa `CLKSEL=0`, selecionando o oscilador interno de 8 MHz. A semântica dos bits e a observação de que uma referência de giroscópio pode ter estabilidade melhor estão em [[mpu6050_register_map]].

O firmware escolhe uma inicialização simples: não ativa modo de baixo consumo, não coloca eixos em espera e não seleciona explicitamente PLL. Isso é diferente de dizer que tais recursos não existem; eles simplesmente não são usados aqui.

### `GYRO_CONFIG`: fundo de escala do giroscópio

```cpp
Wire.beginTransmission(MPU);
Wire.write(0x1B);
Wire.write(0b00011000);
Wire.endTransmission(true);
```

`0x1B` seleciona `GYRO_CONFIG`. Os bits 4 e 3 recebem `11`, isto é, `FS_SEL=3`, escolhendo ±2000 °/s. Os bits de autoteste ficam desligados. A tabela de seleção vem do [[mpu6050_register_map]], e o divisor físico usado depois vem de [[mpu6050_product_specification]].

Essa faixa reduz o risco de saturar em rotações intensas, mas oferece menos resolução por grau por segundo que faixas menores. O comentário no próprio `.ino` lista alternativas, mas somente ±2000 °/s é executado.

### `ACCEL_CONFIG`: fundo de escala do acelerômetro

```cpp
Wire.beginTransmission(MPU);
Wire.write(0x1C);
Wire.write(0b00011000);
Wire.endTransmission(true);
```

`0x1C` é `ACCEL_CONFIG`. Novamente, os bits 4 e 3 ficam em `11`; agora isso significa `AFS_SEL=3`, logo ±16 g. A decisão privilegia margem para impactos e vibrações grandes. O custo é uma leitura menos detalhada para movimentos pequenos quando comparada a ±2 g ou ±4 g.

> [!warning] Configuração e conversão são inseparáveis
>
> O valor escrito em `0x1B` determina o divisor do giro; o valor em `0x1C` determina o divisor da aceleração. Alterar somente o registrador ou somente a divisão serial gera unidade física errada. [[testar_dados]] também usa limites coerentes com as escalas atuais.

### `loop()`: apontar o primeiro registrador e pedir o bloco completo

```cpp
Wire.beginTransmission(MPU);
Wire.write(0x3B);
Wire.endTransmission(false);
Wire.requestFrom(MPU, 14, true);

if (Wire.available() < 14) {
  return;
}
```

`0x3B` é `ACCEL_XOUT_H`, o primeiro de uma sequência contínua: seis bytes de aceleração, dois de temperatura e seis de giro. Os detalhes da sequência estão em [[mpu6050_register_map]].

`endTransmission(false)` evita enviar STOP entre selecionar o registrador e iniciar a leitura; a biblioteca implementa a sequência de leitura I2C com repeated START descrita em [[mpu6050_product_specification]]. Pedir os 14 bytes juntos é melhor que ler cada eixo em operações separadas: os registros voltados ao usuário preservam uma leitura coerente do mesmo instante de amostragem.

Se chegarem menos de 14 bytes, `return` abandona a iteração. Assim, o firmware não mistura valores antigos e novos, não aumenta `contador` e não transmite uma linha incompleta.

### Recombinação dos pares de bytes

```cpp
a_x = Wire.read() << 8 | Wire.read();
a_y = Wire.read() << 8 | Wire.read();
a_z = Wire.read() << 8 | Wire.read();
temperatura = Wire.read() << 8 | Wire.read();
Gyrx = Wire.read() << 8 | Wire.read();
Gyry = Wire.read() << 8 | Wire.read();
Gyrz = Wire.read() << 8 | Wire.read();
```

Cada medição ocupa 16 bits: primeiro o byte alto, depois o baixo. O deslocamento de oito bits e o `|` recompõem a palavra. [[mpu6050_register_map]] informa que as saídas são números de 16 bits em complemento de dois.

> [!warning] Interpretação de sinal depende da plataforma
>
> O código recompõe a palavra e a armazena diretamente em `float`, sem converter explicitamente para `int16_t`. Em placas Arduino cuja promoção de tipos não preserve a interpretação assinada esperada, valores negativos podem ser lidos incorretamente. Validar essa conversão com leituras estáticas e, se necessário, usar `int16_t`, é uma melhoria recomendada antes de medições quantitativas críticas.

Temperatura é lida, mas não convertida nem enviada. Ela precisa ser consumida porque ocupa os bytes entre `az` e `gx`; pular esses dois bytes deslocaria os três valores do giroscópio.

### Contador, tempo e conversão para unidades

```cpp
contador++;
Serial.print(contador);
Serial.print(",");
Serial.print(micros());
Serial.print(",");
Serial.print(a_x / 2048);
// ... ay e az também usam / 2048
Serial.print(Gyrx / 16.4);
// ... Gyry e Gyrz também usam / 16.4
```

Em ±16 g, a especificação define `2048 LSB/g`; portanto, dividir a saída bruta por 2048 produz a aceleração em `g`. Em ±2000 °/s, o divisor é `16,4 LSB/(°/s)`. [[mpu6050_product_specification]] registra as duas tabelas e suas tolerâncias nominais.

`micros()` acrescenta o relógio local do Arduino. [[coletor]] prefere essa coluna a tempo de PC para estimar a taxa efetiva, como explicado em [[tempo-frequencia-e-perdas]]. Tanto `micros()` quanto `contador` têm faixa finita e podem voltar ao início em execuções muito longas.

### Fechamento da linha serial

```cpp
Serial.println(Gyrz / 16.4);
```

`println` escreve o último campo e o terminador de linha. Essa quebra de linha é parte do protocolo: o leitor Python chama `readline()`, logo precisa saber onde uma amostra termina.

## O que o `.ino` não configura

O firmware não escreve em `SMPLRT_DIV` nem no registrador de filtro digital `CONFIG`. Portanto, a taxa de saída e a filtragem interna não são escolhas explícitas deste projeto. [[mpu6050_product_specification]] mostra que taxa, filtro e relógio interferem na resposta dinâmica; [[teoria_vibração]] explica por que isso é decisivo para Nyquist e interpretação de frequência.

Também não usa FIFO, interrupção de dados prontos, leitura de `WHO_AM_I`, calibração de offset ou fusão de sensores. São possíveis evoluções, mas não devem ser descritas como se já estivessem ativas.

## Estratégia segura para alterações

1. Consulte [[mpu6050_register_map]] para confirmar endereço do registrador e bits.
2. Consulte [[mpu6050_product_specification]] para faixa, sensibilidade e consequência física.
3. Altere juntos a escrita de configuração e o divisor da conversão.
4. Atualize [[protocolo-serial]], [[esquema-csv]] e os consumidores se o formato mudar.
5. Faça uma coleta curta, valide-a com [[testar_dados]] e compare-a em [[plotar_csv]].

## Insights para outros projetos

- **Registrador e unidade são um contrato único:** bit de escala e divisor de conversão devem evoluir juntos.
- **Leitura em bloco protege coerência temporal:** coordenadas de um mesmo vetor devem representar o mesmo instante físico.
- **Uma linha serial é uma API:** delimitador, ordem e terminador são parte da compatibilidade com o restante do sistema.
- **Recursos disponíveis não são recursos usados:** PDFs descrevem muitas capacidades; a documentação deve separar implementação atual de possibilidades futuras.

## Resumo mental

O `.ino` é um adaptador entre registros do MPU6050 e uma mensagem CSV estável. Ele configura faixas, lê um bloco coerente de seis eixos, converte com sensibilidades específicas e fornece contador e tempo para o Python avaliar qualidade e cadência. As justificativas de cada registrador e divisor ficam rastreáveis em [[mpu6050_register_map]] e [[mpu6050_product_specification]].
#PROJETO_SENSOR_VIBRAÇÃO
