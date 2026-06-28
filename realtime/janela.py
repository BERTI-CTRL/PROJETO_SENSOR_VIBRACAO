from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)

from PyQt6.QtCore import QTimer

import pyqtgraph as pg

from sensor.manager import manager


class Janela(QMainWindow):

    def __init__(self):

        super().__init__()

        self.manager = manager

        self.setWindowTitle("Sensor de Vibração")

        self.resize(1200, 700)

        self.criar_interface()

        self.criar_timer()

    # -------------------------

    def criar_interface(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout()

        central.setLayout(layout)

        # -------------------------
        # gráfico
        # -------------------------

        self.grafico = pg.PlotWidget()

        self.grafico.setBackground("k")

        self.grafico.showGrid(x=True, y=True)

        self.grafico.setLabel("left", "Aceleração (g)")

        self.grafico.setLabel("bottom", "Amostras")

        layout.addWidget(self.grafico)

        self.curva_ax = self.grafico.plot(
            pen="y",
            width=2,
        )

        # -------------------------
        # status
        # -------------------------

        self.status = QLabel("Status: Parado")

        layout.addWidget(self.status)

        # -------------------------
        # botões
        # -------------------------

        linha = QHBoxLayout()

        layout.addLayout(linha)

        self.bt_iniciar = QPushButton("Iniciar")

        self.bt_parar = QPushButton("Parar")

        linha.addWidget(self.bt_iniciar)

        linha.addWidget(self.bt_parar)

        self.bt_iniciar.clicked.connect(self.iniciar)

        self.bt_parar.clicked.connect(self.parar)

    # -------------------------

    def criar_timer(self):

        self.timer = QTimer()

        self.timer.timeout.connect(self.atualizar_grafico)

        self.timer.start(16)

    # -------------------------

    def iniciar(self):

        self.manager.iniciar()

        self.status.setText("Status: Adquirindo")

    # -------------------------

    def parar(self):

        self.manager.parar()

        self.status.setText("Status: Parado")

    # -------------------------

    def atualizar_grafico(self):

        dados = list(self.manager.buffer.ax)

        if len(dados) == 0:

            return

        self.curva_ax.setData(dados)

    # -------------------------

    def closeEvent(self, event):

        self.manager.parar()

        event.accept()