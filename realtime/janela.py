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
        dados_ax=np.array(self.manager.buffer.ax)
        dados_ay=np.array(self.manager.buffer.ay)
        dados_az=np.array(self.manager.buffer.az)

        dados_gx=np.array(self.manager.buffer.gx)
        dados_gy=np.array(self.manager.buffer.gy)
        dados_gz=np.array(self.manager.buffer.gz)
        ##########################################
        #atualização da curva ax
        if self.checkbox_ax.isChecked():
            self.curva_ax.show()
            self.curva_ax.setData(dados_ax)

        else:
            self.curva_ax.hide()
            
        ########################
        #atualização da curva ay
        if self.checkbox_ay.isChecked():
            self.curva_ay.show()
            self.curva_ay.setData(dados_ay)

        else:
            self.curva_ay.hide()
            

        #########################
        #atualização da curva az
        if self.checkbox_az.isChecked():
            self.curva_az.show()
            self.curva_az.setData(dados_az)
        else:
            self.curva_az.hide()
            
        ########################
        #atualização da curva gx

        if self.checkbox_gx.isChecked():
            self.curva_gx.show()
            self.curva_gx.setData(dados_gx)
        else:
            self.curva_gx.hide()
            
        
        #########################
        #atualização da curva gy
        if self.checkbox_gy.isChecked():
            self.curva_gy.show()
            self.curva_gy.setData(dados_gy)
        else:
            self.curva_gy.hide()
            
        
        #########################
        #atualização da curva gz
        if self.checkbox_gz.isChecked():
            self.curva_gz.show()
            self.curva_gz.setData(dados_gz)
        else:
            self.curva_gz.hide()
        

        #auto scroll
        if self.auto_scroll_ativo:
            self.auto_scroll()

       


    def auto_scroll(self):
        """
        Responsabilidade:
        Manter o gráfico acompanhando as amostras mais recentes.
        """

        #Verificação do Buffer
        if self.manager.buffer.vazio():
            return
        
        numero_amostras = len(self.manager.buffer.ax)
        janela_de_visualizacao = 1000

        inicio = max(0,numero_amostras - janela_de_visualizacao) #max(0,numero_amostras - janela_de_visualizacao) -> Garante que o índice de início não seja negativo, evitando erros de indexação.
        fim = numero_amostras

        self.grafico.setXRange(inicio,fim,padding=0.15) #Define o intervalo do eixo x do gráfico, mostrando apenas as últimas 1000 amostras. O deque proposto nos outros scripts ja se encarrega da remoção das amostras mais antigas, garantindo que o gráfico exiba apenas os dados mais recentes.

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