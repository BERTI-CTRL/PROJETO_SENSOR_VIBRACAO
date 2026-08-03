# realtime/gráfico.py

**Responsabilidade:** Interface alternativa minimalista para visualização rápida (single plot, 60 FPS).  
**Tipo:** Script executável standalone (`python realtime/gráfico.py`)  
**Thread:** Main thread (GUI)

---

## Código Completo

```python
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from sensor.manager import manager


class Janela(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor de Vibração")
        self.resize(1200, 600)

        # Gráfico simples
        self.grafico = pg.PlotWidget()
        self.setCentralWidget(self.grafico)

        self.curva = self.grafico.plot(pen="y", width=2)
        self.grafico.showGrid(x=True, y=True)
        self.grafico.setLabel("left", "Aceleração (g)")
        self.grafico.setLabel("bottom", "Amostras")

        # Inicia aquisição
        manager.iniciar()

        # Timer ~60 FPS (16ms)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.atualizar)
        self.timer.start(16)

    def atualizar(self):
        dados = manager.buffer
        if len(dados.ax) < 2:
            return
        ax = list(dados.ax)[-500:]  # Últimos 500 pontos
        self.curva.setData(ax)

    def closeEvent(self, event):
        manager.parar()
        event.accept()


app = QtWidgets.QApplication(sys.argv)
janela = Janela()
janela.show()
sys.exit(app.exec())
```

---

## Diferenças vs `janela.py` (Principal)

| Aspecto | `gráfico.py` (Simples) | `janela.py` (Completa) |
|---------|------------------------|------------------------|
| **Linhas** | ~63 | ~532 |
| **Canais** | 1 (ax apenas) | 6 (ax,ay,az,gx,gy,gz) |
| **FPS** | 60 FPS (16ms) | 5 FPS (200ms) |
| **Pontos** | 500 fixos | 250 configuráveis |
| **Controles** | Nenhum | Checkboxes, botões, stats |
| **Estatísticas** | Não | Hz, RMS, média, desvio, etc. |
| **Eixo X** | Índice implícito (0..499) | Relativo (0..249) |
| **Uso** | Debug rápido / teste | Produção / monitoramento |

---

## Fluxo de Atualização (60 FPS)

```
Timer 16ms
    │
    ▼
atualizar()
    │
    ├─ manager.buffer → dados
    ├─ len(dados.ax) < 2? → return
    ├─ ax = list(dados.ax)[-500:]  # Conversão list + slice
    └─ self.curva.setData(ax)       # Plot widget update
```

**Nota:** `list(dados.ax)` cria cópia Python list → overhead maior que `janela.py` que usa `np.asarray()` + `setData()` direto.

---

## Quando Usar Cada Um

| Cenário | Recomendado |
|---------|-------------|
| Teste rápido "liga/desliga" | `python realtime/gráfico.py` |
| Verificar se Arduino envia dados | `gráfico.py` |
| Debug de taxa de amostragem | `gráfico.py` (60 FPS) |
| Monitoramento produção | `python -m realtime.main` (`janela.py`) |
| Análise de múltiplos eixos | `janela.py` |
| Estatísticas em tempo real | `janela.py` |
| Apresentação / relatórios | `janela.py` |

---

## Dependências

- `PyQt6` / `pyqtgraph.Qt` (Qt6 bindings)
- `pyqtgraph` - PlotWidget
- `sensor.manager` - Pipeline global

---

## Referências Cruzadas

| Arquivo | Relação |
|---------|---------|
| [[main]] | Entry point oficial (usa `janela.py`) |
| [[janela]] | Versão completa |
| [[manager]] | Instância global `manager` |