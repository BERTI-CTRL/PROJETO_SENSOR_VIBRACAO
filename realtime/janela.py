#janela.py
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox
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

'''
┌──────────────────────────────────────────────────────────┐
│                     Sensor de Vibração                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                    Gráfico Tempo Real                    │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ Sinais                                                   │
│ ☑ Ax  ☑ Ay  ☑ Az  ☐ Gx  ☐ Gy  ☐ Gz                    │
├──────────────────────────────────────────────────────────┤
│ Estatísticas                                             │
│ Hz Médio:                                                │
│ Hz Instantâneo:                                          │
│ Hz Suavizado:                                            │
│ Amostras:                                                │
│ Status:                                                  │
├──────────────────────────────────────────────────────────┤
│ [Iniciar] [Parar] [Limpar] [Auto Escala]                 │
└──────────────────────────────────────────────────────────┘'''
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

        self.layout = QVBoxLayout()

        central.setLayout(self.layout)

        self.criar_grafico()

        self.criar_painel_sinais()

        self.criar_painel_estatisticas()

        self.criar_barra_botoes()




    def criar_grafico(self):
        self.grafico = pg.PlotWidget() 
        self.grafico.setBackground("k")
        self.grafico.showGrid(x=True,y=True)
        self.grafico.setLabel("left","Acleração (g)")
        self.grafico.setLabel("bottom","Amostras(n)")
        self.layout.addWidget(self.grafico)

        self.curva_ax = self.grafico.plot(
            pen="y",
            name="Ax"
        )
        self.curva_ay = self.grafico.plot(
            pen="g",
            name="Ay"
        )
        self.curva_az = self.grafico.plot(
            pen="c",
            name="Az"
        )
        self.curva_gx = self.grafico.plot(
            pen="r",
            name="Gx"
        )
        self.curva_gy = self.grafico.plot(
            pen="m",
            name="Gy"
        )
        self.curva_gz = self.grafico.plot(
            pen="w",
            name="Gz"
        )


    def criar_painel_sinais(self):

        ''' ┌────────────── Sinais ──────────────┐
                    ☑ Ax   ☑ Ay   ☑ Az

                    ☐ Gx   ☐ Gy   ☐ Gz
            └────────────────────────────────────┘'''
        

        grupo_sinais = QGroupBox("Sinais")
        layout = QGridLayout()
        self.checkbox_ax = QCheckBox("ax")
        self.checkbox_ax.setChecked(True) #Deixa o check box ax marcado por padrão

        self.checkbox_ay = QCheckBox("ay")
        self.checkbox_ay.setChecked(True)

        self.checkbox_az = QCheckBox("az")
        self.checkbox_az.setChecked(True)

        self.checkbox_gx = QCheckBox("gx")
        self.checkbox_gx.setChecked(True)

        self.checkbox_gy = QCheckBox("gy")
        self.checkbox_gy.setChecked(True)

        self.checkbox_gz = QCheckBox("gz")
        self.checkbox_gz.setChecked(True)

        #Adicionando ao layout
        layout.addWidget(self.checkbox_ax,0,0) #Adiciona o check box ax na Linha 0 coluna 0,na função grid layout
        layout.addWidget(self.checkbox_ay,0,1) 
        layout.addWidget(self.checkbox_az,0,2)
        layout.addWidget(self.checkbox_gx,1,0) 
        layout.addWidget(self.checkbox_gy,1,1) 
        layout.addWidget(self.checkbox_gz,1,2) 

        grupo_sinais.setLayout(layout) #coloca o layout dentro da caixa (grupo)  
        self.layout.addWidget(grupo_sinais) # e coloca a caixa(grupo)dentro da janela


    def criar_painel_estatisticas(self):
        '''┌────────── Estatísticas ──────────┐

                Status: Parado

                Hz Médio: 0.0

                Hz Instantâneo: 0.0

                Hz Suavizado: 0.0

                Amostras: 0

                Buffer: 0 / 1000

            └──────────────────────────────────┘'''
        
        grupo_estatiscas = QGroupBox("Estatísticas")
        layout = QVBoxLayout()


    def criar_barra_botoes(self)

    # Controle
    def criar_timer(self)

    def iniciar(self)

    def parar(self)

    # Atualização
    def atualizar_grafico(self)

    def atualizar_estatisticas(self)

    # Utilidades
    def limpar_grafico(self)

    def autoescala(self)

    def closeEvent(self)