"""Janela PyQt para monitoramento dos sinais de vibracao em tempo real."""

import math

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QTimer
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


# A aquisicao recebe aproximadamente 212 Hz. A tela nao precisa desenhar
# todas as amostras: 30 FPS e suficiente para uma visualizacao fluida.
INTERVALO_GRAFICO_MS = 33
INTERVALO_ESTATISTICAS_MS = 250
PONTOS_GRAFICO = 1000

EIXOS = ("ax", "ay", "az", "gx", "gy", "gz")
CORES = {"ax": "y", "ay": "g", "az": "c", "gx": "r", "gy": "m", "gz": "w"}


class Janela(QMainWindow):
    def __init__(self):
        super().__init__()

        self.manager = manager
        self.auto_scroll_ativo = True
        self.curvas = {}
        self.checkboxes = {}

        self.setWindowTitle("Monitor de Vibração")
        self.resize(1300, 800)

        self.criar_interface()
        self.criar_timers()

    def criar_interface(self):
        central = QWidget()
        self.setCentralWidget(central)

        self.layout = QVBoxLayout(central)
        self.criar_grafico()
        self.criar_painel_sinais()
        self.criar_painel_estatisticas()
        self.criar_barra_botoes()

    def criar_grafico(self):
        self.grafico = pg.PlotWidget()
        self.grafico.setBackground("k")
        self.grafico.showGrid(x=True, y=True)
        self.grafico.setLabel("left", "Aceleração / Giro")
        self.grafico.setLabel("bottom", "Contador da amostra")
        self.layout.addWidget(self.grafico)

        # Um dicionario evita repetir o mesmo codigo para os seis sinais.
        for eixo in EIXOS:
            self.curvas[eixo] = self.grafico.plot(pen=CORES[eixo], name=eixo.upper())

    def criar_painel_sinais(self):
        grupo = QGroupBox("Sinais exibidos")
        layout = QGridLayout(grupo)

        for indice, eixo in enumerate(EIXOS):
            checkbox = QCheckBox(f"{eixo.upper()} ({CORES[eixo]})")
            checkbox.setChecked(True)
            self.checkboxes[eixo] = checkbox
            layout.addWidget(checkbox, indice // 3, indice % 3)

        self.layout.addWidget(grupo)

    def criar_painel_estatisticas(self):
        grupo = QGroupBox("Estatísticas")
        layout = QVBoxLayout(grupo)

        self.label_status = QLabel("Status: parado")
        self.label_hz_medio = QLabel("Hz médio: 0.00")
        self.label_hz_instantaneo = QLabel("Hz instantâneo: 0.00")
        self.label_hz_suavizado = QLabel("Hz suavizado: 0.00")
        self.label_amostras = QLabel("Amostras recebidas: 0")
        self.label_buffer = QLabel("Buffer: 0 / 10000")
        self.label_perdas = QLabel("Perdas seriais: 0 (0 saltos)")
        self.label_fila = QLabel("Fila CSV: 0")

        # Ax foi escolhido inicialmente por ser o primeiro sinal de vibracao.
        # As outras estatisticas podem seguir o mesmo padrao depois.
        self.label_media_ax = QLabel("Média Ax: --")
        self.label_desvio_ax = QLabel("Desvio padrão Ax: --")
        self.label_rms_ax = QLabel("RMS Ax: --")

        for label in (
            self.label_status,
            self.label_hz_medio,
            self.label_hz_instantaneo,
            self.label_hz_suavizado,
            self.label_amostras,
            self.label_buffer,
            self.label_perdas,
            self.label_fila,
            self.label_media_ax,
            self.label_desvio_ax,
            self.label_rms_ax,
        ):
            layout.addWidget(label)

        self.layout.addWidget(grupo)

    def criar_barra_botoes(self):
        layout = QHBoxLayout()

        botao_iniciar = QPushButton("Iniciar")
        botao_parar = QPushButton("Parar")
        botao_limpar = QPushButton("Limpar histórico")
        botao_auto_escala = QPushButton("Auto Escala")

        botao_iniciar.clicked.connect(self.iniciar)
        botao_parar.clicked.connect(self.parar)
        botao_limpar.clicked.connect(self.limpar_grafico)
        botao_auto_escala.clicked.connect(self.autoescala)

        for botao in (botao_iniciar, botao_parar, botao_limpar, botao_auto_escala):
            layout.addWidget(botao)

        self.layout.addLayout(layout)

    def criar_timers(self):
        # Grafico e estatisticas possuem ritmos diferentes. Separar os timers
        # evita recalcular NumPy mais vezes do que o usuario consegue ler.
        self.timer_grafico = QTimer(self)
        self.timer_grafico.timeout.connect(self.atualizar_grafico)
        self.timer_grafico.start(INTERVALO_GRAFICO_MS)

        self.timer_estatisticas = QTimer(self)
        self.timer_estatisticas.timeout.connect(self.atualizar_estatisticas)
        self.timer_estatisticas.start(INTERVALO_ESTATISTICAS_MS)

    def iniciar(self):
        self.manager.iniciar()
        self.label_status.setText("Status: iniciando")

    def parar(self):
        self.manager.parar()
        self.label_status.setText("Status: parado")

    def atualizar_grafico(self):
        # Snapshot copia todos os eixos sob o mesmo lock. A UI nunca acessa os
        # deques diretamente, evitando eixos desalinhados durante a aquisicao.
        dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)
        if len(dados["contador"]) < 2:
            return

        # O contador e o eixo X real. Assim, uma eventual lacuna na aquisicao
        # aparece no grafico em vez de ser escondida por indices 0, 1, 2, ...
        contadores = np.asarray(dados["contador"], dtype=float)

        for eixo in EIXOS:
            curva = self.curvas[eixo]
            if self.checkboxes[eixo].isChecked():
                curva.show()
                curva.setData(contadores, np.asarray(dados[eixo], dtype=float))
            else:
                curva.hide()

        if self.auto_scroll_ativo:
            self.auto_scroll(contadores[-1])

    def auto_scroll(self, contador_atual):
        inicio = max(0, contador_atual - PONTOS_GRAFICO + 1)
        self.grafico.setXRange(inicio, contador_atual, padding=0.05)

    def atualizar_estatisticas(self):
        coletor = self.manager.coletor
        buffer = self.manager.buffer

        self.label_status.setText(
            "Status: adquirindo" if coletor.rodando else "Status: parado"
        )
        self.label_hz_medio.setText(f"Hz médio: {coletor.hz_medio:.2f}")
        self.label_hz_instantaneo.setText(f"Hz instantâneo: {coletor.hz_inst:.2f}")
        self.label_hz_suavizado.setText(f"Hz suavizado: {coletor.hz_inst_suavizado:.2f}")
        self.label_amostras.setText(f"Amostras recebidas: {coletor.numero_amostras}")
        self.label_buffer.setText(
            f"Buffer: {buffer.tamanho_atual()} / {buffer.tamanho_maximo}"
        )
        self.label_perdas.setText(
            f"Perdas seriais: {coletor.amostras_perdidas} "
            f"({coletor.saltos_contador} saltos)"
        )#janela.py
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

        self.auto_scroll_ativo = True
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
                                    

        # Criando o PlotWidget
        self.grafico = pg.PlotWidget() 

          # Configuração do gráfico
        self.grafico.setBackground("k")
        self.grafico.showGrid(x=True,y=True)
        self.grafico.setLabel("left","Acleração (g)")
        self.grafico.setLabel("bottom","Amostras(n)")
        self.layout.addWidget(self.grafico)


        #curvas
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
        Por que 33ms? 1000ms / 33ms \\aprox 30Hz,ou 30 FPS'''

        self.timer = QTimer()

        #conectar o timer ao método atualizar_grafico
        self.timer.timeout.connect(self.atualizar_grafico)

        #conectar o timer ao método atualizar_estatitiscas
        self.timer.timeout.connect(self.atualizar_estatisticas)
        self.timer.start(33) #inicia o timer com intervalo de 33ms


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
    def atualizar_grafico(self):
        '''Responsabiliade: ler o estado atual do buffer e desenhar as curvas selecionadas e Atualizar o auto scroll (caso esteja habilitado).'''

        #Verificação do Buffer
        if self.manager.buffer.vazio():
            return

        contador = self.manager.buffer.contador[-1]

        if contador % 1000 == 0:
            print(f"[Janela] {contador}")
        
        ##############################
        #leitura dos dados armazenados
        ###########################
        

        dados = self.manager.buffer.snapshot(1000)

        if len(dados) < 2 :
            return
        
        contadores = np.asarray(dados['contador'])
        dados_ax = np.asarray(dados["ax"])
        dados_ay = np.asarray(dados["ay"])
        dados_az = np.asarray(dados["az"])
        dados_gx = np.asarray(dados["gx"])
        dados_gy = np.asarray(dados["gy"])
        dados_gz = np.asarray(dados["gz"])



        ##########################################
        #atualização da curva ax
        if self.checkbox_ax.isChecked():
            self.curva_ax.show()
            self.curva_ax.setData(contadores,dados_ax)

        else:
            self.curva_ax.hide()
            
        ########################
        #atualização da curva ay
        if self.checkbox_ay.isChecked():
            self.curva_ay.show()
            self.curva_ay.setData(contadores,dados_ay)

        else:
            self.curva_ay.hide()
            

        #########################
        #atualização da curva az
        if self.checkbox_az.isChecked():
            self.curva_az.show()
            self.curva_az.setData(contadores,dados_az)
        else:
            self.curva_az.hide()
            
        ########################
        #atualização da curva gx

        if self.checkbox_gx.isChecked():
            self.curva_gx.show()
            self.curva_gx.setData(contadores,dados_gx)
        else:
            self.curva_gx.hide()
            
        
        #########################
        #atualização da curva gy
        if self.checkbox_gy.isChecked():
            self.curva_gy.show()
            self.curva_gy.setData(contadores,dados_gy)
        else:
            self.curva_gy.hide()
            
        
        #########################
        #atualização da curva gz
        if self.checkbox_gz.isChecked():
            self.curva_gz.show()
            self.curva_gz.setData(contadores,dados_gz)
        else:
            self.curva_gz.hide()
        

        #auto scroll
        if self.auto_scroll_ativo:
            self.auto_scroll(contadores[-1])

       


    def auto_scroll(self,contador_atual):
        """
        Responsabilidade:
        Manter o gráfico acompanhando as amostras mais recentes.
        """

        #Verificação do Buffer
        if self.manager.buffer.vazio():
            return
        inicio = max(0, contador_atual - 999)
        self.grafico.setXRange(inicio, contador_atual, padding=0.15)




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
            f"Hz Instantâneo: {self.manager.coletor.hz_inst:.2f}"
        )

        self.label_hz_suavizado.setText(
            f"Hz Instantâneo Suavizado: {self.manager.coletor.hz_inst_suavizado:.2f}"
        )

        ####################################
        # Quantidade de dados
        ####################################

        self.label_amostras.setText(
            f"Amostras: {self.manager.coletor.numero_amostras}"
        )

        self.label_buffer.setText(
            f"Buffer: {len(self.manager.buffer.ax)}"
        )

    # Utilidades
    def limpar_grafico(self):
        '''Responsabilidade: Limpar o gráfico,somente.'''

       

        self.curva_ax.clear()
        self.curva_ay.clear()
        self.curva_az.clear()
        self.curva_gx.clear()
        self.curva_gy.clear()
        self.curva_gz.clear()


    def closeEvent(self,event):
        
        """
        Responsabilidades:
        - Encerrar a aquisição antes do fechamento da aplicação.
        - Permitir que a janela seja fechada com segurança.
        """

        self.manager.parar()

        event.accept()  # Aceita o evento de fechamento da janela, permitindo que a aplicação seja encerrada corretamente.


        '''event.ignore()
        
        Deseja salvar antes de sair?

            [Sim]

            [Não]

            [Cancelar]'''

        fila = self.manager.fila_gravacao
        tamanho_fila = fila.qsize() if fila is not None else 0
        self.label_fila.setText(
            f"Fila CSV: {tamanho_fila} | não enfileiradas: "
            f"{coletor.amostras_nao_enfileiradas}"
        )

        # As estatisticas usam o mesmo recorte do grafico, mas sao calculadas
        # so quatro vezes por segundo para nao disputar CPU com a aquisicao.
        dados = buffer.snapshot(PONTOS_GRAFICO)
        estatisticas_ax = calcular_estatisticas(dados["ax"])
        self.label_media_ax.setText(
            f"Média Ax: {self.formatar_numero(estatisticas_ax.media)} g"
        )
        self.label_desvio_ax.setText(
            f"Desvio padrão Ax: "
            f"{self.formatar_numero(estatisticas_ax.desvio_padrao)} g"
        )
        self.label_rms_ax.setText(
            f"RMS Ax: {self.formatar_numero(estatisticas_ax.rms)} g"
        )

    @staticmethod
    def formatar_numero(valor):
        """Evita mostrar 'nan' na interface quando ainda nao ha dados."""
        return "--" if not math.isfinite(valor) else f"{valor:.4f}"

    def limpar_grafico(self):
        # Limpa o historico visual; a aquisicao continua e preenche o buffer
        # novamente nas proximas amostras.
        self.manager.buffer.limpar()
        for curva in self.curvas.values():
            curva.clear()

    def autoescala(self):
        self.grafico.enableAutoRange()

    def closeEvent(self, event):
        self.manager.parar()
        event.accept()
