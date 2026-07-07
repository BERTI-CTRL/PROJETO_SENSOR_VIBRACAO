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
    QGroupBox,
    
    
)

import numpy as np

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

from sensor.manager import manager,buffer

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

        ''' Cria o painel por ligar e desligar os sinais que serão exibidos no gráfico.
            ┌────────────── Sinais ──────────────┐
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

        '''Cria o painel responsável por exibir as estatísticas da aquisição.
        ┌────────── Estatísticas ──────────┐

                Status: Parado

                Hz Médio: 0.0

                Hz Instantâneo: 0.0

                Hz Instantâneo Suavizado: 0.0

                Amostras: 0

                Buffer: 0 / 1000

            └──────────────────────────────────┘'''
        
        grupo_estatisticas = QGroupBox("Estatísticas") #cria a caixa
        layout = QVBoxLayout() #layout verrtical (por isso QV e não outro)

        self.label_status = QLabel("Status: parado")
        self.label_hz_medio = QLabel("Hz Médio: 0.0")
        self.label_hz_instantaneo = QLabel("Hz Instantâneo: 0.0")
        self.label_hz_suavizado = QLabel("Hz Instantâneo Suavizado: 0.0")
        self.label_amostras = QLabel("Amostras: 0")
        self.label_buffer = QLabel("Buffer: 0 / 1000")

        #Adicionando ao layout
        layout.addWidget(self.label_status)
        layout.addWidget(self.label_hz_medio)
        layout.addWidget(self.label_hz_instantaneo)
        layout.addWidget(self.label_hz_suavizado)
        layout.addWidget(self.label_amostras)
        layout.addWidget(self.label_buffer)

        
        grupo_estatisticas.setLayout(layout) #adiciona o layout à caixa (grupo estatiscas)
        self.layout.addWidget(grupo_estatisticas)# e adiciona a caixa (grupo estatiscas) à janela



    def criar_barra_botoes(self):
        ''' O que queremos construir é uma barra de botões que permita iniciar, parar, limpar e auto escalar o gráfico. 
        Responsabilidades:
        - Criar os botões de controle.
        - Organizar os botões horizontalmente.
        - Conectar cada botão ao método correspondente.
        
        ┌──────────────────────────────────────────────┐

        [ Iniciar ] [ Parar ] [ Limpar ] [ Auto Escala ]

        └──────────────────────────────────────────────┘
        '''
        
        layout = QHBoxLayout()

        self.botao_iniciar = QPushButton("Iniciar")
        self.botao_parar = QPushButton("Parar")
        self.botao_limpar = QPushButton("Limpar")
        self.botao_auto_escala = QPushButton("Auto Escala")

        #Adicionando ao layout
        layout.addWidget(self.botao_iniciar)
        layout.addWidget(self.botao_parar)
        layout.addWidget(self.botao_limpar)
        layout.addWidget(self.botao_auto_escala)

        #Conectando os botões aos métodos correspondentes
        self.botao_iniciar.clicked.connect(self.iniciar)
            
        self.botao_parar.clicked.connect(self.parar) 
            

        self.botao_limpar.clicked.connect(self.limpar_grafico)
          
        self.botao_auto_escala.clicked.connect(self.autoescala)
            


        self.layout.addLayout(layout) #adiciona o layout à janela


        

    # Controle
    def criar_timer(self):
        ''' Função: executar periodicamente determinadas funções em intervalos regulares de tempo. No projeto, a cada 16 ms atualizar o gráfico e as estisitcias
        Por que 16ms? 1000ms / 16ms \\aprox 62Hz,ou 62 FPS'''

        self.timer = QTimer()

        #conectar o timer ao método atualizar_grafico
        self.timer.timeout.connect(self.atualizar_grafico)

        #conectar o timer ao método atualizar_estatitiscas
        self.timer.timeout.connect(self.atualizar_estatisticas)
        self.timer.start(16) #inicia o timer com intervalo de 16ms


    '''
    Usuário                                                             
        │
        ▼
    Botão
        │
        ▼
    Janela
        │
        ▼
    SensorManager
        │
        ▼
    Coletor
        │
        ▼
    Serial
        │
        ▼
    Arduino
    '''
    def iniciar(self):
        self.manager.iniciar()
        self.label_status.setText("Status: rodando")

    def parar(self):
        self.manager.parar()
        self.label_status.setText("Status: parado")

    # Atualização
    def atualizar_grafico(self,sensor.manager.buffer):
        '''Responsabiliade: ler o estado atual do buffer e desenhar as curvas selecionadas'''
        
        dados_ax=np.array(sensor.manager.buffer.ax)
        dados_ay=np.array(sensor.manager.buffer.ay)
        dados_az=np.array(sensor.manager.buffer.az)

        dados_gx=np.array(sensor.manager.buffer.gx)
        dados_gy=np.array(sensor.manager.buffer.gy)
        dados_gz=np.array(sensor.manager.buffer.gz)

        if sensor.manager.buffer.vazio:
            return

        #Verificação do Buffer
        if self.checkbox_ax.is_Checked():


        if self.checkbox_ay.is_Checked():


        if self.checkbox_az.is_Checked():


        if self.checkbox_gx.is_Checked():


        if self.checkbox_gy.is_Checked():


        if self.checkbox_gz.is_Checked():


    def atualizar_estatisticas(self):

    # Utilidades
    def limpar_grafico(self)

    def autoescala(self)

    def closeEvent(self)