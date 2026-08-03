"""Janela PyQt para monitoramento dos sinais de vibracao em tempo real."""

import math

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sensor.manager import manager
from utils.statistics import calcular_estatisticas


# A aquisicao recebe aproximadamente 212 Hz. 
# Interface a 30 FPS para visualizacao fluida.
# Otimizacoes agressivas para 30 FPS sem travar
import pyqtgraph as pg
pg.setConfigOptions(antialias=False, useOpenGL=True)  # OpenGL backend + sem antialias

INTERVALO_GRAFICO_MS = 33
INTERVALO_ESTATISTICAS_MS = 500
PONTOS_GRAFICO = 150

EIXOS = ("ax", "ay", "az", "gx", "gy", "gz")
CORES = {"ax": "y", "ay": "g", "az": "c", "gx": "r", "gy": "m", "gz": "w"}


class Janela(QMainWindow):
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

        self.auto_scroll_ativo = False
        self._x_data = np.arange(PONTOS_GRAFICO)
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
                                  
        ''' Responsabilidades:
        - Criar o PlotWidget.
        - Configurar a aparência do gráfico.
        - Criar as curvas que representarão os sinais do MPU6050.'''
                                      

        # Criando o PlotWidget com OpenGL
        self.grafico = pg.PlotWidget(enableMenu=False)  # disable context menu
        self.grafico.setBackground("k")
        self.grafico.showGrid(x=True, y=True, alpha=0.3)
        self.grafico.setLabel("left", "Aceleração (g)")
        self.grafico.setLabel("bottom", "Amostras (n)")
        self.grafico.setMouseEnabled(x=False, y=False)  # disable mouse zoom/pan
        self.layout.addWidget(self.grafico)

        # Desabilita auto-range (causa lag)
        self.grafico.setAutoRange(x=False, y=False)
        self.grafico.setXRange(0, PONTOS_GRAFICO, padding=0)
        self.grafico.setYRange(-20, 20, padding=0)  # fixed range

        # Curvas com render otimizado
        self.curva_ax = self.grafico.plot(pen=pg.mkPen("y", width=1), name="Ax")
        self.curva_ay = self.grafico.plot(pen=pg.mkPen("g", width=1), name="Ay")
        self.curva_az = self.grafico.plot(pen=pg.mkPen("c", width=1), name="Az")
        self.curva_gx = self.grafico.plot(pen=pg.mkPen("r", width=1), name="Gx")
        self.curva_gy = self.grafico.plot(pen=pg.mkPen("m", width=1), name="Gy")
        self.curva_gz = self.grafico.plot(pen=pg.mkPen("w", width=1), name="Gz")


    def criar_painel_sinais(self):

        ''' Cria o painel por ligar e desligar os sinais que serão exibidos no gráfico.
            ┌────────────── Sinais ──────────────┐
                    ☑ Ax   ☑ Ay   ☑ Az

                    ☐ Gx   ☐ Gy   ☐ Gz
            └────────────────────────────────────┘'''
        
        grupo_sinais = QGroupBox("Sinais")
        layout = QGridLayout()
        self.checkbox_ax = QCheckBox("ax (amarelo)")
        self.checkbox_ax.setChecked(True) #Deixa o check box ax marcado por padrão

        self.checkbox_ay = QCheckBox("ay (verde)")
        self.checkbox_ay.setChecked(True)

        self.checkbox_az = QCheckBox("az(ciano)")
        self.checkbox_az.setChecked(True)

        self.checkbox_gx = QCheckBox("gx (vermelho)")
        self.checkbox_gx.setChecked(True)

        self.checkbox_gy = QCheckBox("gy(rosa)")
        self.checkbox_gy.setChecked(True)

        self.checkbox_gz = QCheckBox("gz (white)")
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
        ┌─────────────────────────────────────────────────────────────────┐
        │ Status: Adquirindo                                              │
        │ Hz Médio: 214.56  |  Hz Inst: 214.32  |  Hz Suav: 214.45       │
        │ Amostras: 15234  |  Buffer: 10000 / 10000                      │
        ├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐ │
        │          │    ax    │    ay    │    az    │    gx    │   gy   │   gz   │
        ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤ │
        │ Média    │  0.0012  │ -0.0040  │ -0.0380  │ -3.649   │  0.214 │ -0.344 │
        ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤ │
        │ Desvio   │  0.0456  │  0.0050  │  0.0060  │  0.134   │  0.310 │  0.148 │
        ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤ │
        │ RMS      │  0.0457  │  0.0060  │  0.0390  │  3.651   │  0.376 │  0.374 │
        └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘'''
        
        grupo_estatisticas = QGroupBox("Estatísticas")
        layout = QVBoxLayout()

        # Linha 1: Status e Hz
        linha_hz = QHBoxLayout()
        self.label_status = QLabel("Status: parado")
        self.label_hz_medio = QLabel("Hz Médio: 0.00")
        self.label_hz_instantaneo = QLabel("Hz Inst: 0.00")
        self.label_hz_suavizado = QLabel("Hz Suav: 0.00")
        for w in (self.label_status, self.label_hz_medio, self.label_hz_instantaneo, self.label_hz_suavizado):
            linha_hz.addWidget(w)
        layout.addLayout(linha_hz)

        # Linha 2: Contadores
        linha_cont = QHBoxLayout()
        self.label_amostras = QLabel("Amostras: 0")
        self.label_buffer = QLabel("Buffer: 0 / 10000")
        linha_cont.addWidget(self.label_amostras)
        linha_cont.addWidget(self.label_buffer)
        layout.addLayout(linha_cont)

        # Grid de estatísticas por eixo
        self.eixos = ["ax", "ay", "az", "gx", "gy", "gz"]
        self.unidades = {"ax": "g", "ay": "g", "az": "g", "gx": "°/s", "gy": "°/s", "gz": "°/s"}
        self.stats_labels = {}  # {(eixo, metrica): QLabel}

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)

        # Cabeçalho
        grid.addWidget(QLabel(""), 0, 0)
        for col, eixo in enumerate(self.eixos, 1):
            lbl = QLabel(eixo.upper())
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; color: #88c0d0;")
            grid.addWidget(lbl, 0, col)

        # Linhas: Média, Desvio, RMS
        metricas = [("Média", "media"), ("Desvio", "desvio_padrao"), ("RMS", "rms")]
        for row, (nome, key) in enumerate(metricas, 1):
            lbl_row = QLabel(nome)
            lbl_row.setStyleSheet("font-weight: bold;")
            grid.addWidget(lbl_row, row, 0)
            for col, eixo in enumerate(self.eixos, 1):
                lbl = QLabel("--")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setMinimumWidth(70)
                self.stats_labels[(eixo, key)] = lbl
                grid.addWidget(lbl, row, col)

        layout.addLayout(grid)
        grupo_estatisticas.setLayout(layout)
        self.layout.addWidget(grupo_estatisticas)


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
        self.botao_auto_escala = QPushButton("Auto Scroll: OFF")

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
        ''' Timer gráfico: 30 FPS (33ms). Timer estatísticas: 2 FPS (500ms).'''
        
        # Timer gráfico - 30 FPS
        self.timer_grafico = QTimer()
        self.timer_grafico.timeout.connect(self.atualizar_grafico)
        self.timer_grafico.start(INTERVALO_GRAFICO_MS)
        
        # Timer estatísticas - 2 FPS (independente do gráfico)
        self.timer_stats = QTimer()
        self.timer_stats.timeout.connect(self.atualizar_estatisticas)
        self.timer_stats.start(INTERVALO_ESTATISTICAS_MS)


# Controle
    def iniciar(self):
        self.manager.iniciar()
        self.label_status.setText("Status: rodando")


    def parar(self):
        self.manager.parar()
        self.label_status.setText("Status: Parado")


    # Atualização
    def atualizar_grafico(self):
        '''Responsabiliade: ler o estado atual do buffer e desenhar as curvas selecionadas e Atualizar o auto scroll (caso esteja habilitado).'''

        #Verificação do Buffer
        if self.manager.buffer.vazio():
            return

        # Snapshot único
        dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)

        '''if len(dados) < 2 :
            return'''
        
        # Mapeia eixos -> (checkbox, curva, dados)
        curvas = {
            'ax': (self.checkbox_ax, self.curva_ax, dados['ax']),
            'ay': (self.checkbox_ay, self.curva_ay, dados['ay']),
            'az': (self.checkbox_az, self.curva_az, dados['az']),
            'gx': (self.checkbox_gx, self.curva_gx, dados['gx']),
            'gy': (self.checkbox_gy, self.curva_gy, dados['gy']),
            'gz': (self.checkbox_gz, self.curva_gz, dados['gz']),
        }

        # X relativo (cache) - evita alocação
        n = len(dados['contador'])
        x = self._x_data[:n]

        # Só atualiza curvas visíveis
        for _, (check, curva, y) in curvas.items():
            if check.isChecked():
                curva.show()
                curva.setData(x, np.asarray(y), skipFiniteCheck=True)
            else:
                curva.hide()

        # Auto scroll
        if self.auto_scroll_ativo:
            self.auto_scroll(self.manager.buffer.contador[-1])


    def auto_scroll(self, contador_atual):
        """Auto-scroll só quando ativado pelo usuário."""
        if not self.auto_scroll_ativo:
            return
        if self.manager.buffer.vazio():
            return
        inicio = max(0, contador_atual - PONTOS_GRAFICO + 1)
        self.grafico.setXRange(inicio, contador_atual, padding=0.02)

    def toggle_auto_scroll(self):
        """Alterna auto-scroll on/off."""
        self.auto_scroll_ativo = not self.auto_scroll_ativo
        self.botao_auto_escala.setText("Auto Scroll: ON" if self.auto_scroll_ativo else "Auto Scroll: OFF")

    def autoescala(self):
        self.grafico.enableAutoRange()


    def atualizar_estatisticas(self):

        ####################################
        # Status
        ####################################

        if self.manager.coletor.rodando:
            self.label_status.setText("Status: Adquirindo")
        else:
            self.label_status.setText("Status: Parado")

        ####################################
        # Frequência de aquisição
        ####################################

        self.label_hz_medio.setText(
            f"Hz Médio: {self.manager.coletor.hz_medio:.2f}"
        )

        self.label_hz_instantaneo.setText(
            f"Hz Inst: {self.manager.coletor.hz_inst:.2f}"
        )

        self.label_hz_suavizado.setText(
            f"Hz Suav: {self.manager.coletor.hz_inst_suavizado:.2f}"
        )

        ####################################
        # Quantidade de dados
        ####################################

        self.label_amostras.setText(
            f"Amostras: {self.manager.coletor.numero_amostras}"
        )

        self.label_buffer.setText(
            f"Buffer: {len(self.manager.buffer.ax)} / 10000"
        )

        ####################################
        # Estatísticas por eixo
        ####################################

        # Pega snapshot uma vez
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


    # Utilidades
    def limpar_grafico(self):
        '''Responsabilidade: Limpar o gráfico,somente.'''

       
        self.curva_ax.clear()
        self.curva_ay.clear()
        self.curva_az.clear()
        self.curva_gx.clear()
        self.curva_gy.clear()
        self.curva_gz.clear()


    def toggle_auto_scroll(self):
        """Alterna auto-scroll on/off."""
        self.auto_scroll_ativo = not self.auto_scroll_ativo
        self.botao_auto_escala.setText("Auto Scroll: ON" if self.auto_scroll_ativo else "Auto Scroll: OFF")

    def autoescala(self):
        self.grafico.enableAutoRange()


    def closeEvent(self,event):
        
        """
        Responsabilidades:
        - Encerrar a aquisição antes do fechamento da aplicação.
        - Permitir que a janela seja fechada com segurança.
        """
        
        self.timer_grafico.stop()
        self.timer_stats.stop()
        self.manager.parar()
        
        event.accept()  # Aceita o evento de fechamento da janela, permitindo que a aplicação seja encerrada corretamente.