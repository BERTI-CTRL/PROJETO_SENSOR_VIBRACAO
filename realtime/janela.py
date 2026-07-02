#janela.py
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

        self.setWindowTitle("Monitor de Vibração") 

        self.resize(1300,800)

        #Widgets

        self.grafico = None
        self.curva_ax = None
        self.curva_ay = None
        self.curva_az = None
        self.curva_gx = None
        self.curva_gy = None
        self.curva_gz = None

        self.criar_interface()
        self.criar_timer()


    # Interface
    def criar_interface(self):
        central = QWidget()

        self.setCentralWidget(central)

    def criar_grafico()

    def criar_painel_sinais()

    def criar_painel_estatisticas()

    def criar_barra_botoes()

    # Controle
    def criar_timer()

    def iniciar()

    def parar()

    # Atualização
    def atualizar_grafico()

    def atualizar_estatisticas()

    # Utilidades
    def limpar_grafico()

    def autoescala()

    def closeEvent()