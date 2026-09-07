# MPU-6000/MPU-6050 Register Map and Descriptions

> [!abstract] Leitura dirigida
>
> Esta nota não resume o PDF inteiro. Ela explica somente os registradores e os campos que aparecem em [[arduino_mpu6050]], com páginas do arquivo [MPU-6000-Register-Map1 (1).pdf](<../../arduino/MPU-6000-Register-Map1 (1).pdf>).

## Para que serve este PDF

O *Register Map* responde à pergunta “qual byte escrever ou ler para pedir determinado comportamento ao chip?”. Ele é diferente do [[mpu6050_product_specification]], que apresenta faixas, sensibilidades, limites elétricos e desempenho físico.

No `.ino`, o PDF é usado em quatro momentos: acordar o MPU6050, configurar as escalas, localizar as saídas de dados e interpretar os 14 bytes retornados.

## Mapa das páginas usadas

| PDF p. | Registro ou assunto | Uso concreto em `mpu-6050.ino` |
| --- | --- | --- |
| 14 | `GYRO_CONFIG`, endereço `0x1B` | Grava `0b00011000` para escolher giro ±2000 °/s. |
| 15 | `ACCEL_CONFIG`, endereço `0x1C` | Grava `0b00011000` para escolher aceleração ±16 g. |
| 29 | `ACCEL_XOUT_H` a `ACCEL_ZOUT_L`, `0x3B`–`0x40` | Define início, ordem, tamanho e sinal dos seis bytes de aceleração. |
| 30 | `TEMP_OUT_H/L`, `0x41`–`0x42` | Explica os dois bytes de temperatura consumidos no meio da leitura. |
| 31 | `GYRO_XOUT_H` a `GYRO_ZOUT_L`, `0x43`–`0x48` | Define os seis bytes de giro e suas saídas assinadas de 16 bits. |
| 40–41 | `PWR_MGMT_1`, endereço `0x6B` | Explica `SLEEP`, `CLKSEL` e o efeito de gravar zero. |

As páginas são as páginas do visualizador do PDF, que também aparecem impressas no cabeçalho como “n of 46”.

## Código explicado, na ordem em que usa o mapa

### `PWR_MGMT_1` em `0x6B`: sair de sono

O firmware escreve:

```cpp
Wire.write(0x6B);
Wire.write(0);
```

Na [PDF p. 40](<../../arduino/MPU-6000-Register-Map1 (1).pdf#page=40>), `0x6B` é identificado como `PWR_MGMT_1`. Seu byte contém `DEVICE_RESET`, `SLEEP`, `CYCLE`, `TEMP_DIS` e `CLKSEL`.

Ao gravar zero, o `.ino` faz três escolhas relevantes:

- `SLEEP=0`: o chip não fica em modo de sono;
- `CYCLE=0`: ele não entra no modo de baixo consumo que acorda somente para amostras ocasionais;
- `CLKSEL=0`: usa o oscilador interno de 8 MHz.

A [PDF p. 41](<../../arduino/MPU-6000-Register-Map1 (1).pdf#page=41>) descreve esses campos e confirma que `SLEEP=1` ativa o sono. A p. 40 observa que uma referência baseada em giroscópio ou fonte externa é recomendada para maior estabilidade, mas o firmware atual deliberadamente mantém a configuração simples de `CLKSEL=0`.

> [!note] O que não foi escolhido
>
> O código não solicita reset por `DEVICE_RESET`, não desliga temperatura com `TEMP_DIS` e não usa `PWR_MGMT_2`. Esses recursos existem no PDF, mas não devem ser confundidos com comportamento do projeto atual.

### `GYRO_CONFIG` em `0x1B`: selecionar ±2000 °/s

O trecho é:

```cpp
Wire.write(0x1B);
Wire.write(0b00011000);
```

Na [PDF p. 14](<../../arduino/MPU-6000-Register-Map1 (1).pdf#page=14>), o endereço hexadecimal `1B` corresponde a `GYRO_CONFIG`. Os bits 7, 6 e 5 ativariam autoteste de X, Y e Z; eles permanecem em zero no valor gravado. Os bits 4 e 3 são `FS_SEL[1:0]`.

O valor binário gravado deixa `FS_SEL=3`. A tabela da mesma página associa esse valor à faixa de ±2000 °/s. A escolha do código e o divisor `16.4` usado na transmissão precisam ser lidos juntos; a justificativa da sensibilidade está em [[mpu6050_product_specification]].

### `ACCEL_CONFIG` em `0x1C`: selecionar ±16 g

O firmware repete o padrão:

```cpp
Wire.write(0x1C);
Wire.write(0b00011000);
```

Na [PDF p. 15](<../../arduino/MPU-6000-Register-Map1 (1).pdf#page=15>), `1C` é `ACCEL_CONFIG`. Os bits 7 a 5 são de autoteste e permanecem desligados. Os bits 4 e 3 são `AFS_SEL[1:0]`; `AFS_SEL=3` corresponde à faixa de ±16 g.

A página menciona também filtro passa-alta digital e autoteste, mas o `.ino` não configura esses recursos de modo explícito. O único campo usado é a seleção de faixa. O divisor de `2048` para converter a leitura em `g` vem da tabela de sensibilidade da [[mpu6050_product_specification]].

### Bloco de aceleração: `0x3B` até `0x40`

O laço começa a leitura por:

```cpp
Wire.write(0x3B);
Wire.endTransmission(false);
Wire.requestFrom(MPU, 14, true);
```

A [PDF p. 29](<../../arduino/MPU-6000-Register-Map1 (1).pdf#page=29>) mostra que `0x3B` é `ACCEL_XOUT_H`; os endereços seguintes fornecem byte alto e baixo de X, Y e Z até `0x40`. Ela estabelece três fatos usados no código:

1. cada eixo ocupa 16 bits em complemento de dois;
2. os seis bytes estão em posições consecutivas;
3. a leitura em rajada dos registros voltados ao usuário mantém as medições no mesmo instante de amostragem.

Por isso o `.ino` recompõe pares na ordem X, Y, Z. Inverter bytes ou eixos mudaria radicalmente a interpretação física feita em [[teoria_vibração]].

### Temperatura: `0x41` e `0x42`

Na [PDF p. 30](<../../arduino/MPU-6000-Register-Map1 (1).pdf#page=30>), os dois endereços após `az` são `TEMP_OUT_H` e `TEMP_OUT_L`. O `.ino` lê os dois em `temperatura`:

```cpp
temperatura = Wire.read() << 8 | Wire.read();
```

Ele não envia temperatura pela serial. Ainda assim, precisa consumir esses bytes, pois os valores de giro começam somente depois deles. A página inclui fórmula de conversão para graus Celsius, mas ela não é usada no firmware e, portanto, não pertence ao protocolo atual de [[protocolo-serial]].

### Bloco de giro: `0x43` até `0x48`

A [PDF p. 31](<../../arduino/MPU-6000-Register-Map1 (1).pdf#page=31>) mapeia os seis bytes seguintes como `GYRO_XOUT_H/L`, `GYRO_YOUT_H/L` e `GYRO_ZOUT_H/L`. Eles também são palavras de 16 bits em complemento de dois.

Depois de consumir os oito bytes de aceleração e temperatura, o firmware lê exatamente estes três pares:

```cpp
Gyrx = Wire.read() << 8 | Wire.read();
Gyry = Wire.read() << 8 | Wire.read();
Gyrz = Wire.read() << 8 | Wire.read();
```

Agora fica claro por que são solicitados 14 bytes: seis de aceleração, dois de temperatura e seis de giro. Esse tamanho não é arbitrário nem inclui campos invisíveis.

## Relação entre mapa e leitura I2C

O *Register Map* localiza os dados; [[mpu6050_product_specification]] explica a conversa I2C em si. O `false` em `Wire.endTransmission(false)` mantém a sequência sem STOP entre apontar `0x3B` e começar a receber o bloco. A especificação chama esse padrão de repeated START.

O teste a seguir protege a interpretação do mapa:

```cpp
if (Wire.available() < 14) {
  return;
}
```

Sem todos os bytes, os pares alto/baixo poderiam ficar desalinhados. Ao abandonar a iteração, o firmware preserva a regra de que uma linha serial representa um conjunto completo de seis eixos.

## Limites de interpretação

- O mapa identifica bits e endereços; ele não transforma automaticamente números brutos em `g` e °/s. Isso depende das sensibilidades da [[mpu6050_product_specification]].
- O PDF informa que os dados são assinados em complemento de dois. A implementação atual deve ser validada na placa-alvo para confirmar que a recomposição e a promoção de tipos preservam leituras negativas corretamente.
- `SMPLRT_DIV`, `CONFIG`, FIFO, interrupções e `WHO_AM_I` aparecem no mapa, mas não são usados pelo `.ino`. Eles ficam fora desta nota de propósito.

## Insights para outros projetos

- **Use o mapa para justificar cada número mágico.** `0x1B`, `0x1C`, `0x3B` e `0x6B` deixam de ser mistério quando ligados a nome, bits e página.
- **Um burst tem estrutura.** Saber onde começa, quantos bytes contém e que campos atravessa previne leituras deslocadas.
- **Separar “registrador” de “unidade” evita erros.** O mapa define seleção e formato; a especificação define conversão e desempenho.

## Resumo mental

Este PDF é o dicionário de endereços usado pelo firmware. O `.ino` escreve `PWR_MGMT_1`, `GYRO_CONFIG` e `ACCEL_CONFIG`; depois lê, em uma única sequência, `ACCEL_*`, `TEMP_*` e `GYRO_*`. Cada uma dessas decisões pode ser rastreada às páginas acima, sem tentar transformar a nota em resumo do manual inteiro.
#PROJETO_SENSOR_VIBRAÇÃO
