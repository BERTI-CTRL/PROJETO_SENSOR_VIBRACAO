# Esquema do CSV

[[coletor]] encaminha à fila do [[gravador_worker]] uma lista com nove valores. [[gravador]] grava essa ordem com vírgula como delimitador e o cabeçalho abaixo. [[testar_dados]] exige exatamente esse cabeçalho; [[plotar_csv]] usa `contador` e os seis eixos para desenhar os sinais.

| Coluna | Tipo conceitual | Unidade | Origem | Consumidores |
|---|---|---|---|---|
| `tempo_arduino_us` | número inteiro conceitual | µs | `micros()` do firmware | [[coletor]], [[testar_dados]] |
| `tempo_relogio_pc` | ponto flutuante | s do relógio monotônico local | `time.perf_counter()` em [[serial_reader]] | [[testar_dados]], análise temporal |
| `contador` | número inteiro conceitual | sem unidade | contador incremental do firmware | [[coletor]], [[plotar_csv]], [[testar_dados]] |
| `ax` | ponto flutuante | g | aceleração X do MPU6050 | [[plotar_csv]], [[testar_dados]] |
| `ay` | ponto flutuante | g | aceleração Y do MPU6050 | [[plotar_csv]], [[testar_dados]] |
| `az` | ponto flutuante | g | aceleração Z do MPU6050 | [[plotar_csv]], [[testar_dados]] |
| `gx` | ponto flutuante | °/s | giroscópio X do MPU6050 | [[plotar_csv]], [[testar_dados]] |
| `gy` | ponto flutuante | °/s | giroscópio Y do MPU6050 | [[plotar_csv]], [[testar_dados]] |
| `gz` | ponto flutuante | °/s | giroscópio Z do MPU6050 | [[plotar_csv]], [[testar_dados]] |

`tempo_relogio_pc` não é tempo de época: vem de `time.perf_counter()` no momento de recepção pelo PC. [[tempo-frequencia-e-perdas]] explica por que a frequência usa `tempo_arduino_us` e não esse valor.

O firmware lê 14 bytes do MPU6050, incluindo temperatura, mas transmite somente contador, `micros()` e os seis eixos. Portanto, temperatura não aparece no protocolo [[protocolo-serial]] nem neste CSV.
