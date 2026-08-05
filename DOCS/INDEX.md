# Índice da documentação — PROJETO_SENSOR_VIBRACAO

**Atualizado:** 05/08/2026

## Comece por aqui

1. [[ARQUITETURA]] — visão do caminho completo de uma amostra.
2. [[arduino_mpu6050]] — conexão, registradores e escalas do MPU6050.
3. [[janela]] — uso da interface em tempo real e limites de desempenho.
4. [[plotar_csv]] — análise do CSV inteiro no navegador.
5. [[calibrar_vibracao]] — primeiro ensaio com vibração RMS conhecida.

## Scripts e relação entre eles

| Documento | Script | Uso principal |
|---|---|---|
| [[arduino_mpu6050]] | `arduino/mpu-6050/mpu-6050.ino` | Lê o sensor e envia a linha serial. |
| [[serial_reader]] | `sensor/serial_reader.py` | Lê e valida a linha serial. |
| [[coletor]] | `sensor/coletor.py` | Calcula Hz, detecta saltos e encaminha a amostra. |
| [[buffers]] | `sensor/buffers.py` | Mantém as últimas 10.000 amostras. |
| [[gravador]] / [[gravador_worker]] | `sensor/gravador*.py` | Salva CSV sem bloquear a serial. |
| [[manager]] | `sensor/manager.py` | Inicia e para as duas threads. |
| [[testar_dados]] | `sensor/teste_manager.py` | Testa a coleta sem abrir GUI. |
| [[main]] / [[janela]] | `realtime/main.py`, `realtime/janela.py` | Interface principal. |
| [[grafico]] | `realtime/gráfico.py` | Debug visual rápido de `ax`. |
| [[plotar_csv]] | `grafico/plotar_csv.py` | Plotly com o CSV completo. |
| [[statistics]] | `utils/statistics.py` | Métricas usadas na janela. |
| [[calibrar_vibracao]] | `calibração/calibrar_vibracao.py` | Gera offset e ganho a partir de referência RMS. |

## Comandos rápidos

```powershell
# Janela principal
python -m realtime.main

# Teste serial sem interface
python -m sensor.teste_manager

# Debug visual mínimo (somente ax)
python realtime\gráfico.py

# Plotly do último CSV
python grafico\plotar_csv.py

# Calibração simples com referência de 0,50 g RMS em az
python calibração\calibrar_vibracao.py 0.50
```

## Correções registradas

- [[correcao-pulos-amostras-serial]]
- [[correcao-buffer-congelando-wrap-around]]
- [[correcao-controles-parada-e-i2c]]
