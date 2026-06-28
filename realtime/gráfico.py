import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from sensor.manager import manager


class Janela(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sensor de Vibração")

        self.resize(1200, 600)

        # gráfico
        self.grafico = pg.PlotWidget()
        self.setCentralWidget(self.grafico)

        self.curva = self.grafico.plot(
            pen="y",
            width=2
        )

        self.grafico.showGrid(x=True, y=True)

        self.grafico.setLabel("left", "Aceleração (g)")
        self.grafico.setLabel("bottom", "Amostras")

        # inicia aquisição
        manager.iniciar()

        # atualiza o gráfico
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.atualizar)
        self.timer.start(16)       # ~60 FPS

    def atualizar(self):

        dados = manager.buffer

        if len(dados.ax) < 2:
            return

        ax = list(dados.ax)[-500:]

        self.curva.setData(ax)

    def closeEvent(self, event):

        manager.parar()

        event.accept()


app = QtWidgets.QApplication(sys.argv)

janela = Janela()
janela.show()

sys.exit(app.exec())