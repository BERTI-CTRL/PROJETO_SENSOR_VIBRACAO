# Índice da Documentação - PROJETO_SENSOR_VIBRACAO

**Versão:** 1.0  
**Atualizado:** 31/07/2026  

---

## 📁 Estrutura da Documentação

```
DOCS/
├── INDEX.md                    # Este arquivo
├── [[ARQUITETURA]]              # Visão geral + fluxo completo
├── [[serial_reader]]            # Leitura serial (generator)
├── [[coletor]]                  # Thread de aquisição
├── [[buffers]]                  # Buffer circular NumPy (wrap-around)
├── [[gravador]]                 # CSV writer com batch
├── [[gravador_worker]]          # Thread de gravação assíncrona
├── [[manager]]                  # Facade/orquestrador
├── [[janela]]                   # UI PyQt6 completa
├── [[main]]                     # Entry point PyQt
├── [[grafico]]                  # UI alternativa minimalista
├── [[statistics]]               # Estatísticas descritivas (NumPy)
└── ../ERROS/                   # Bugs corrigidos
    ├── [[correcao-pulos-amostras-serial]]
    └── [[correcao-buffer-congelando-wrap-around]]
```

---

## 📖 Guia de Leitura por Perfil

### 🔧 Desenvolvedor Backend (Pipeline de Dados)
1. **[[ARQUITETURA]]** - Visão macro
2. **[[serial_reader]]** - Interface Arduino → Python
3. **[[coletor]]** - Thread aquisição + métricas Hz
4. **[[buffers]]** - Buffer circular (crítico: wrap-around)
5. **[[gravador]]** + **[[gravador_worker]]** - Persistência CSV
6. **[[manager]]** - Orquestração

### 🎨 Desenvolvedor Frontend (UI PyQt)
1. **[[ARQUITETURA]]** - Fluxo UI ↔ Backend
2. **[[janela]]** - UI completa (5 FPS, 6 canais, stats)
3. **[[main]]** - Entry point
4. **[[grafico]]** - UI alternativa (60 FPS, debug)
5. **[[statistics]]** - Métricas exibidas (RMS, skew, kurtose)

### 🐛 Debug / Troubleshooting
1. **[[correcao-pulos-amostras-serial]]** - Serial `readline()` vs `in_waiting`
2. **[[correcao-buffer-congelando-wrap-around]]** - Buffer NumPy wrap-around
3. **[[buffers]]** - Seção "Bugs Corrigidos"
4. **[[serial_reader]]** - Seção "Bugs Corrigidos"

### 📊 Análise de Dados / Vibração
1. **[[statistics]]** - Métricas (RMS, assimetria, curtose, CV%)
2. **[[coletor]]** - Hz médio/instantâneo/suavizado
3. **[[janela]]** - Painel estatísticas (500ms)

---

## 🔄 Fluxo de Dados Resumido

```
Arduino (MPU6050)                           Python Backend
─────────────────                           ───────────────
Serial 115200 baud                          serial_reader.py
contador,micros(),ax,ay,az,         ──▶    readline() + parse CSV
gx,gy,gz (CSV \n)                           yield tuplas
                                             │
                                             ▼
                                    coletor.py (Thread)
                                    ├── _registrar_salto()
                                    ├── _calcular_hz()
                                    ├── buffer.adicionar() ──▶ buffers.py (NumPy 2D)
                                    └── fila_gravacao.put() ──▶ gravador_worker.py
                                                                     │
                                                                     ▼
                                                            gravador.py (CSV batch)
```

**UI (Main Thread):**
```
QTimer 200ms ──▶ atualizar_grafico()
                    ├── buffer.snapshot(250)  (thread-safe, ordem cronológica)
                    ├── np.arange(250)        (eixo X relativo 0..249)
                    └── curva.setData()       (pyqtgraph GPU)
QTimer 500ms ──▶ atualizar_estatisticas()
                    ├── buffer.snapshot(250)["ax"]
                    ├── calcular_estatisticas() (RMS, skew, kurtose)
                    └── QLabels update
```

---

## ⚙️ Configurações-Chave

| Parâmetro | Arquivo | Valor | Impacto |
|-----------|---------|-------|---------|
| Baud rate | `serial_reader.py` + Arduino | 115200 | **Deve coincidir** |
| Buffer size | `buffers.py` | 10.000 | ~46s histórico @ 215 Hz |
| FPS gráfico | `janela.py` | 5 FPS (200ms) | CPU vs fluidez |
| Pontos/frame | `janela.py` | 250 | Janela ~1.16s |
| Batch CSV | `gravador.py` | 1000 linhas | I/O efficiency |
| Queue size | `manager.py` | 50.000 | Pico ~3.8 min |

---

## 🧪 Testes Rápidos

```bash
# 1. Serial direto (deve dar ~215 Hz)
python -c "
import serial, time
with serial.Serial('COM4', 115200, timeout=1) as s:
    time.sleep(12); s.reset_input_buffer()
    t=time.time(); c=0
    while time.time()-t<10:
        if s.readline().decode().strip(): c+=1
    print(f'{c/10:.1f} Hz')
"

# 2. Pipeline completo (CLI)
python -m sensor.teste_manager

# 3. UI completa
python -m realtime.main

# 4. UI debug (60 FPS, 1 canal)
python realtime/gráfico.py

# 5. Teste wrap-around buffer
python -c "
import sys; sys.path.insert(0, '.')
from sensor.buffers import BufferSensores
import numpy as np
b = BufferSensores(tamanho=10)
for i in range(15): b.adicionar(i,i,i,i*0.1,i*0.2,i*0.3,i,i*2,i*3)
print('OK' if np.array_equal(b.contador, b.snapshot(10)['contador']) else 'FALHA')
"
```

---

## 📝 Convenção de Atualização

> **SEMPRE** que alterar um script, atualize seu `.md` correspondente em `DOCS/`.
> 
> Se corrigir bug, adicione entrada em `ERROS/` seguindo o template:
> - Causa Raiz + trecho problemático vs corrigido
> - Cronologia da descoberta
> - Evidências (logs antes/depois)
> - Lições aprendidas + checklist anti-regressão
> - Comandos de teste

---

## 🔗 Referências Externas

| Tecnologia | Documentação |
|------------|--------------|
| PyQt6 | https://doc.qt.io/qtforpython-6/ |
| pyqtgraph | https://pyqtgraph.readthedocs.io/ |
| NumPy | https://numpy.org/doc/ |
| pyserial | https://pyserial.readthedocs.io/ |
| MPU6050 Datasheet | `arduino/mpu-6050_datasheet_v3 4.pdf` |
| MPU6050 Register Map | `arduino/MPU-6000-Register-Map1 (1).pdf` |