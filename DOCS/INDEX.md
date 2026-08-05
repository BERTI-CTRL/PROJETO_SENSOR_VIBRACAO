# Índice da documentação — PROJETO_SENSOR_VIBRACAO

**Atualizado:** 04/08/2026

## Componentes principais

| Documento | Conteúdo |
|---|---|
| [[ARQUITETURA]] | Visão geral do fluxo Arduino → Python → CSV → interface. |
| [[arduino_mpu6050]] | Firmware Arduino, registradores do MPU6050 e relação com os PDFs técnicos. |
| [[serial_reader]] | Leitura e validação das linhas recebidas pela serial. |
| [[coletor]] | Processamento das amostras e métricas de frequência. |
| [[buffers]] | Buffer circular NumPy com acesso thread-safe. |
| [[gravador]] / [[gravador_worker]] | Persistência assíncrona dos dados em CSV. |
| [[manager]] | Inicialização e encerramento do pipeline. |
| [[janela]] | Interface principal com dois gráficos em tempo real. |
| [[main]] | Ponto de entrada da aplicação PyQt. |
| [[grafico]] | Interface PyQt mínima usada para depuração rápida. |
| [[plotar_csv]] | Análise posterior de um CSV com Plotly. |
| [[statistics]] | Estatísticas descritivas usadas pela interface. |

## Fluxo resumido

```text
Arduino / MPU6050
        ↓ serial (115200 baud)
serial_reader.py
        ↓
coletor.py (thread de aquisição)
        ├── BufferSensores: dados para a janela
        └── GravadorWorker: dados para o CSV
                                  ↓
                    grafico/plotar_csv.py (análise posterior)
```

## Interface em tempo real

`realtime/janela.py` usa dois timers independentes:

| Tarefa | Intervalo | Dados usados |
|---|---:|---|
| Redesenhar os gráficos | 33 ms | últimas 150 amostras |
| Atualizar estatísticas | 500 ms | últimas 150 amostras |

Há dois gráficos para evitar mistura de escala:

- aceleração: `ax`, `ay`, `az`, em `g`;
- giroscópio: `gx`, `gy`, `gz`, em `°/s`.

## Comandos rápidos

```powershell
# Interface em tempo real
python -m realtime.main

# Analisa o CSV mais recente salvo em dados/
python grafico\plotar_csv.py

# Analisa um CSV escolhido
python grafico\plotar_csv.py dados\arquivo.csv
```

## Documentação de correções

- [[correcao-pulos-amostras-serial]]
- [[correcao-buffer-congelando-wrap-around]]
- [[correcao-controles-parada-e-i2c]]
