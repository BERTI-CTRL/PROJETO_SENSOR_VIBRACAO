# realtime/janela.py

**Responsabilidade:** Interface gráfica PyQt6 para monitoramento tempo real dos sinais de vibração.  
**Tipo:** Classe `Janela` (herda `QMainWindow`)  
**Thread:** Main thread (GUI) + `QTimer` para atualização periódica

---

## Interface Pública

```python
class Janela(QMainWindow):
    def __init__(self):
        """Cria janela completa: gráfico, painel sinais, estatísticas, botões."""
    
    def iniciar(self) -> None:
        """Conecta ao manager e inicia aquisição."""
    
    def parar(self) -> None:
        """Para aquisição via manager."""
    
    def limpar_grafico(self) -> None:
        """Limpa curvas do gráfico (não para aquisição)."""
    
    def autoescala(self) -> None:
        """Habilita auto-range no eixo Y."""
    
    def closeEvent(self, event) -> None:
        """Para aquisição ao fechar janela."""
```

---

## Layout da Interface

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitor de Vibração                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Gráfico Tempo Real                │   │
│  │  pyqtgraph.PlotWidget (fundo preto, grid)           │   │
│  │  6 curvas: Ax(amarelo), Ay(verde), Az(ciano),       │   │
│  │            Gx(vermelho), Gy(rosa), Gz(branco)       │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Sinais                    │  Estatísticas                   │
│  ☑ ax (amarelo)            │  Status: Adquirindo            │
│  ☑ ay (verde)              │  Hz Médio: 214.56  Hz Inst: 214.32  Hz Suav: 214.45 │
│  ☑ az (ciano)              │  Amostras: 15234  Buffer: 10000 / 10000          │
│  ☑ gx (vermelho)           │  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  ☑ gy (rosa)               │  │          │    ax    │    ay    │    az    │    gx    │    gy    │    gz    │ │
│  ☑ gz (branco)             │  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤ │
│                            │  │ Média    │  0.0012  │ -0.0040  │ -0.0380  │ -3.649   │  0.214   │ -0.344   │ │
│                            │  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤ │
│                            │  │ Desvio   │  0.0456  │  0.0050  │  0.0060  │  0.134   │  0.310   │  0.148   │ │
│                            │  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤ │
│                            │  │ RMS      │  0.0457  │  0.0060  │  0.0390  │  3.651   │  0.376   │  0.374   │ │
│                            │  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘ │
├─────────────────────────────────────────────────────────────┤
│  [Iniciar] [Parar] [Limpar] [Auto Escala]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Configurações de Performance

```python
# Linhas 24-28
INTERVALO_GRAFICO_MS = 200      # 5 FPS (era 100ms/10 FPS)
INTERVALO_ESTATISTICAS_MS = 500 # 0.5 FPS (compartilha timer)
PONTOS_GRAFICO = 250            # Pontos por frame (era 500)

EIXOS = ("ax", "ay", "az", "gx", "gy", "gz")
CORES = {"ax": "y", "ay": "g", "az": "c", "gx": "r", "gy": "m", "gz": "w"}
```

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `INTERVALO_GRAFICO_MS` | 200ms (5 FPS) | Balanceia fluidez vs CPU; evita lock contention no buffer |
| `PONTOS_GRAFICO` | 250 | Janela ~1.16s a 215 Hz; suficiente para visualização |
| Timer compartilhado | `timeout.connect(atualizar_grafico)` + `timeout.connect(atualizar_estatisticas)` | Single timer, duas callbacks |

---

## Timer e Atualização

```python
def criar_timer(self):
    self.timer = QTimer()
    self.timer.timeout.connect(self.atualizar_grafico)
    self.timer.timeout.connect(self.atualizar_estatisticas)
    self.timer.start(INTERVALO_GRAFICO_MS)  # 200ms
```

**Fluxo a cada 200ms:**
```
Timer timeout
    │
    ├─▶ atualizar_grafico()
    │     ├─ buffer.vazio()? → return
    │     ├─ snapshot(250) → dict com 6 arrays (cópia thread-safe)
    │     ├─ contadores = np.arange(len)  # Eixo X RELATIVO 0..249
    │     ├─ Para cada eixo ativo (checkbox):
    │     │    curva.setData(contadores, dados[eixo], skipFiniteCheck=True)
    │     └─ auto_scroll(contador_atual)  # Mantém janela no final
    │
    └─▶ atualizar_estatisticas() (mesmo tick)
          ├─ Status: Adquirindo/Parado
          ├─ Hz: médio, instantâneo, suavizado (coletor)
          ├─ Amostras total + buffer size
          ├─ Estatísticas Ax via utils.statistics.calcular_estatisticas()
          │    (média, desvio, RMS, CV%, assimetria, curtose)
          └─ Atualiza QLabels
```

---

## Decisões Críticas de UI

### 1. Eixo X Relativo (`np.arange(len)`)
```python
# ANTES (problemático): contadores absolutos do Arduino
contadores = np.asarray(dados['contador'])  # Ex: [10001, 10002, ...]
# Problema: após wrap-around, salto visual 9999 → 10001

# DEPOIS (corrigido): índice relativo
contadores = np.arange(len(dados['contador']))  # [0, 1, 2, ..., 249]
# Vantagem: gráfico contínuo, sempre 0..249
```
**Por que:** Contador do Arduino cresce indefinidamente (10k, 20k, 30k...). Buffer circular mantém últimos 250, mas contadores absolutos "pulam" visualmente a cada wrap-around.

### 2. `skipFiniteCheck=True` no `setData()`
```python
self.curva_ax.setData(contadores, dados_ax, skipFiniteCheck=True)
```
**Por que:** PyQtGraph por padrão verifica NaN/Inf (lento). Dados do MPU6050 são sempre finitos → pula verificação = performance.

### 3. Auto-scroll Inteligente
```python
def auto_scroll(self, contador_atual):
    inicio = max(0, contador_atual - PONTOS_GRAFICO + 1)
    self.grafico.setXRange(inicio, contador_atual, padding=0.15)
```
Mantém janela sempre nas amostras mais recentes.

---

## Painel de Estatísticas (`atualizar_estatisticas`)

O painel agora exibe estatísticas para **todos os 6 eixos** (ax, ay, az, gx, gy, gz) em grid 3×6:

```python
# Grid 3×6: Média/Desvio/RMS × ax,ay,az,gx,gy,gz
self.eixos = ["ax", "ay", "az", "gx", "gy", "gz"]
self.unidades = {"ax": "g", "ay": "g", "az": "g", "gx": "°/s", "gy": "°/s", "gz": "°/s"}
self.stats_labels = {}  # {(eixo, metrica): QLabel}

# Cria grid QGridLayout com cabeçalho + 3 linhas (Média/Desvio/RMS)
# Atualização única por tick:
snap = self.manager.buffer.snapshot(PONTOS_GRAFICO)

def fmt(v):
    return "--" if not math.isfinite(v) else f"{v:.4f}"

for eixo in self.eixos:
    dados = snap[eixo]
    est = calcular_estatisticas(dados)
    unidade = self.unidades[eixo]
    self.stats_labels[(eixo, "media")].setText(f"{fmt(est.media)} {unidade}")
    self.stats_labels[(eixo, "desvio_padrao")].setText(f"{fmt(est.desvio_padrao)} {unidade}")
    self.stats_labels[(eixo, "rms")].setText(f"{fmt(est.rms)} {unidade}")
```

**Métricas por eixo:** Média, Desvio padrão, RMS  
**Unidades:** g (aceleração ax/ay/az) | °/s (giroscópio gx/gy/gz)  
**Formatação:** `--` se NaN/Inf, caso contrário 4 casas decimais

---

## Botões e Ações

| Botão | Método | Ação |
|-------|--------|------|
| Iniciar | `iniciar()` | `manager.iniciar()` + status "Adquirindo" |
| Parar | `parar()` | `manager.parar()` + status "Parado" |
| Limpar | `limpar_grafico()` | `curva.clear()` nas 6 curvas |
| Auto Escala | `autoescala()` | `grafico.enableAutoRange()` |

---

## Thread Safety (UI ↔ Aquisição)

| Recurso UI | Acesso Buffer | Proteção |
|------------|---------------|----------|
| `atualizar_grafico()` | `buffer.snapshot(250)` | Lock interno `BufferSensores` |
| `atualizar_estatisticas()` | `buffer.snapshot(250)` + `coletor.hz_*` | Lock buffer + variáveis atômicas |
| `buffer.vazio()` | `buffer.vazio()` | Lock |
| `buffer.contador[-1]` | Property `contador` | Lock (retorna cópia `np.ndarray`) |

**Princípio:** UI **nunca** bloqueia thread de aquisição. `snapshot()` faz cópia rápida (NumPy) sob lock curto.

---

## Métricas de Performance

| Métrica | Valor |
|---------|-------|
| FPS gráfico | 5 FPS (200ms) |
| Pontos/frame | 250 |
| CPU UI (plot) | ~2-5% (pyqtgraph GPU) |
| CPU stats | ~0.5% (NumPy stats) |
| Latência UI → Dados | < 200ms (timer) |
| Memória curvas | 6 × 250 × 8 bytes ≈ 12 KB |

---

## Teste Standalone

```bash
# Executar janela diretamente
python -m realtime.main

# Ou via script
python -c "
import sys; sys.path.insert(0, '.')
from PyQt6.QtWidgets import QApplication
from realtime.janela import Janela

app = QApplication(sys.argv)
janela = Janela()
janela.show()
sys.exit(app.exec())
"
```

---

## Dependências

- `PyQt6` ≥ 6.11 (Qt6 bindings)
- `pyqtgraph` ≥ 0.14 (plotting acelerado)
- `numpy` ≥ 2.4.6 (arrays, math)
- `sensor.manager` (pipeline)
- `utils.statistics.calcular_estatisticas` (stats)

---

## Referências Cruzadas

| Arquivo | Linha | Relação |
|---------|-------|---------|
| [[main]] | - | Entry point |
| [[grafico]] | - | UI alternativa simples |
| [[manager]] | - | Pipeline backend |
| [[buffers]] | - | Buffer thread-safe |
| [[statistics]] | - | Estatísticas (todos os 6 eixos) |
| [[coletor]] | - | Métricas Hz |