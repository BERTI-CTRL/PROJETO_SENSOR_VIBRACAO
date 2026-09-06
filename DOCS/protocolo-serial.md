# Protocolo serial

O firmware descrito em [[arduino_mpu6050]] transmite uma amostra por linha, terminada por quebra de linha:

```text
contador,tempo_arduino_us,ax,ay,az,gx,gy,gz
```

[[serial_reader]] exige exatamente estes oito campos, separados por vírgula e conversíveis para `float`.

| Posição | Campo | Origem | Unidade/uso |
|---:|---|---|---|
| 1 | `contador` | contador incremental do Arduino | identifica ordem e lacunas |
| 2 | `tempo_arduino_us` | `micros()` | microssegundos; base para Hz |
| 3 | `ax` | MPU6050 | g |
| 4 | `ay` | MPU6050 | g |
| 5 | `az` | MPU6050 | g |
| 6 | `gx` | MPU6050 | °/s |
| 7 | `gy` | MPU6050 | °/s |
| 8 | `gz` | MPU6050 | °/s |

## Transporte não é o CSV gravado

A linha serial possui oito campos e não inclui horário do PC. Ao recebê-la, [[serial_reader]] adiciona `timestamp` de `time.perf_counter()` e entrega nove valores ao [[coletor]]. O coletor encaminha esses nove valores à fila; o arquivo persistido, documentado em [[esquema-csv]], tem as nove colunas `tempo_arduino_us, tempo_relogio_pc, contador, ax, ay, az, gx, gy, gz`.

Mensagens livres do firmware, linhas parciais e linhas com outra quantidade de campos não pertencem a este protocolo e são descartadas pelo leitor. A correção histórica em [[correcao-pulos-amostras-serial]] explica por que a implementação usa `readline()` em vez de dividir bytes brutos já disponíveis.
