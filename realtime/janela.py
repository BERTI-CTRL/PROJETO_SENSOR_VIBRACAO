"""Janela PyQt para monitoramento dos sinais de vibracao em tempo real."""

# ``isfinite`` decide se uma metrica vira numero ou ``--`` no painel.
import math

# NumPy prepara o eixo X reutilizavel e converte cada serie para o setData.
import numpy as np
# Primeira importacao de PyQtGraph, usada pelos widgets e pelas canetas.
import pyqtgraph as pg
# QTimer agenda atualizacoes no event loop; Qt fornece flags de alinhamento.
from PyQt6.QtCore import QTimer, Qt
# Widgets e layouts formam os graficos, paineis e controles da [[janela]].
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

# O singleton coordena [[coletor]], [[buffers]] e persistencia da sessao.
from sensor.manager import manager
# Funcao pura que resume uma janela recente de um eixo; veja [[statistics]].
from utils.statistics import calcular_estatisticas


# A aquisicao recebe aproximadamente 212 Hz. 
# Interface a 30 FPS para visualizacao fluida.
# Otimizacoes agressivas para 30 FPS sem travar
# Importacao duplicada preservada intencionalmente para manter o codigo e sua
# AST originais; ela referencia o mesmo modulo ja importado acima.
import pyqtgraph as pg
# Configuracao global: desliga antialias e solicita OpenGL para reduzir o custo
# de redesenhar seis curvas em tempo real.
pg.setConfigOptions(antialias=False, useOpenGL=True)  # OpenGL backend + sem antialias

# Graficos atualizam em aproximadamente 30 FPS; estatisticas, menos urgentes,
# usam timer independente de 500 ms, isto e, 2 FPS.
INTERVALO_GRAFICO_MS = 33  # aproximadamente 30 FPS
INTERVALO_ESTATISTICAS_MS = 500
# A GUI retém visualmente somente as 150 amostras mais recentes do snapshot;
# o historico completo pertence ao CSV descrito em [[esquema-csv]].
PONTOS_GRAFICO = 150

# Faixas Y iniciais separadas respeitam as unidades fisicas de cada sensor.
INTERVALO_EIXO_Y_ACELERAÇÃO = (-40,40)#g
INTERVALO_EIXO_Y_GIROSCÓPIO = (-50,50)#°/s

# False fixa a navegacao interativa para evitar zoom/pan acidental e trabalho
# extra durante a aquisicao.
MOUSE_ATIVADO = False  # permite zoom e pan com o mouse

# Ordem logica dos sinais e paleta curta compartilhada pela interface.
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
        # Inicializa QMainWindow antes de criar ou anexar qualquer widget.
        super().__init__()

        # Mantem a mesma instancia global descrita em [[manager]], usada por
        # todos os callbacks de controle e atualizacao.
        self.manager = manager

        # Define identificacao e dimensoes iniciais da janela principal.
        self.setWindowTitle("Monitor de Vibração") 

        self.resize(1300,800)

        # Cada tipo de medida usa seu proprio grafico porque aceleracao (g)
        # e velocidade angular (graus/s) possuem unidades e escalas diferentes.
        # As referencias comecam vazias e sao preenchidas por criar_grafico.
        self.grafico_aceleracao = None
        self.grafico_giroscopio = None
        self.curva_ax = None
        self.curva_ay = None
        self.curva_az = None
        self.curva_gx = None
        self.curva_gy = None
        self.curva_gz = None

        # Eixo X relativo reutilizado a cada atualização. Isso evita mover
        # a faixa de visualização e reduz o custo de renderização.
        self._x_data = np.arange(PONTOS_GRAFICO)

        # Monta toda a hierarquia visual antes de ligar os dois timers, evitando
        # callbacks que tentem acessar widgets ainda inexistentes.
        self.criar_interface()
        self.criar_timer()

    # Compoe os quatro blocos visuais dentro do widget central.
    def criar_interface(self):
        # QMainWindow recebe um QWidget central, que passa a possuir o layout.
        central = QWidget()

        self.setCentralWidget(central)

        # O layout vertical empilha graficos, sinais, estatisticas e botoes.
        self.layout = QVBoxLayout()

        central.setLayout(self.layout)

        # A ordem das chamadas tambem determina a ordem vertical dos blocos.
        self.criar_grafico()

        self.criar_painel_sinais()

        self.criar_painel_estatisticas()

        self.criar_barra_botoes()


    def criar_grafico(self):
                                  
        ''' Responsabilidades:
        - Criar um PlotWidget para aceleracao e outro para o giroscopio.
        - Configurar a aparencia dos dois graficos.
        - Criar as curvas que representarao os sinais do MPU6050.'''
                                      

        # Cria o PlotWidget da aceleracao sem menu de contexto e configura
        # fundo, grade, unidades e interacao antes de inseri-lo no layout.
        self.grafico_aceleracao = pg.PlotWidget(enableMenu=False)  # disable context menu
        self.grafico_aceleracao.setBackground("k")
        self.grafico_aceleracao.showGrid(x=True, y=True, alpha=0.3)
        self.grafico_aceleracao.setLabel("left", "Aceleração (g)")
        self.grafico_aceleracao.setLabel("bottom", "Amostras (n)")
        self.grafico_aceleracao.setMouseEnabled(x=MOUSE_ATIVADO, y=MOUSE_ATIVADO)  # disable mouse zoom/pan
        self.layout.addWidget(self.grafico_aceleracao)

        # Desabilita auto-range (causa lag), fixa X na janela de 150 pontos e
        # inicia Y na faixa propria para aceleracao.
        self.grafico_aceleracao.enableAutoRange(x=False, y=False)
        self.grafico_aceleracao.setXRange(0, PONTOS_GRAFICO, padding=0)
        self.grafico_aceleracao.setYRange(INTERVALO_EIXO_Y_ACELERAÇÃO[0], INTERVALO_EIXO_Y_ACELERAÇÃO[1], padding=0)  # fixed range em g

        # Cria as tres curvas de aceleracao com cores distintas e linha fina.
        self.curva_ax = self.grafico_aceleracao.plot(pen=pg.mkPen("y", width=1), name="Ax")
        self.curva_ay = self.grafico_aceleracao.plot(pen=pg.mkPen("g", width=1), name="Ay")
        self.curva_az = self.grafico_aceleracao.plot(pen=pg.mkPen("c", width=1), name="Az")

        # O segundo PlotWidget repete a estrutura visual, mas representa apenas
        # velocidade angular e recebe sua propria escala vertical.
        self.grafico_giroscopio = pg.PlotWidget(enableMenu=False)  # disable context menu
        self.grafico_giroscopio.setBackground("k")
        self.grafico_giroscopio.showGrid(x=True, y=True, alpha=0.3)
        self.grafico_giroscopio.setLabel("left", "Velocidade angular (°/s)")
        self.grafico_giroscopio.setLabel("bottom", "Amostras (n)")
        self.grafico_giroscopio.setMouseEnabled(x=MOUSE_ATIVADO, y=MOUSE_ATIVADO)  # disable mouse zoom/pan
        self.layout.addWidget(self.grafico_giroscopio)

        # O giroscopio tambem conserva X fixo, enquanto Y comeca em -50..50.
        self.grafico_giroscopio.enableAutoRange(x=False, y=False)
        self.grafico_giroscopio.setXRange(0, PONTOS_GRAFICO, padding=0)
        self.grafico_giroscopio.setYRange(INTERVALO_EIXO_Y_GIROSCÓPIO[0], INTERVALO_EIXO_Y_GIROSCÓPIO[1], padding=0)  # fixed range em graus/s

        # Cria as outras tres curvas, totalizando seis series controlaveis.
        self.curva_gx = self.grafico_giroscopio.plot(pen=pg.mkPen("r", width=1), name="Gx")
        self.curva_gy = self.grafico_giroscopio.plot(pen=pg.mkPen("m", width=1), name="Gy")
        self.curva_gz = self.grafico_giroscopio.plot(pen=pg.mkPen("w", width=1), name="Gz")


    def criar_painel_sinais(self):

        ''' Cria o painel por ligar e desligar os sinais que serão exibidos no gráfico.
            ┌────────────── Sinais ──────────────┐
                    ☑ Ax   ☑ Ay   ☑ Az

                    ☐ Gx   ☐ Gy   ☐ Gz
            └────────────────────────────────────┘'''
        
        # O QGroupBox nomeia o bloco; QGridLayout distribui tres eixos por linha.
        grupo_sinais = QGroupBox("Sinais")
        layout = QGridLayout()
        # Cada checkbox guarda a visibilidade de uma curva, sem interromper a
        # aquisicao daquele sinal no [[coletor]]. Todos comecam selecionados.
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

        # A primeira linha controla aceleracao; a segunda, giroscopio.
        layout.addWidget(self.checkbox_ax,0,0) #Adiciona o check box ax na Linha 0 coluna 0,na função grid layout
        layout.addWidget(self.checkbox_ay,0,1) 
        layout.addWidget(self.checkbox_az,0,2)
        layout.addWidget(self.checkbox_gx,1,0) 
        layout.addWidget(self.checkbox_gy,1,1) 
        layout.addWidget(self.checkbox_gz,1,2) 

        # Anexa a grade ao grupo e o grupo ao layout principal.
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
        
        # O grupo empilha duas linhas de indicadores e uma grade por eixo.
        grupo_estatisticas = QGroupBox("Estatísticas")
        layout = QVBoxLayout()

        # Primeira linha: estado da sessao e tres frequencias calculadas pelo
        # [[coletor]], inicializadas com valores neutros antes da aquisicao.
        linha_hz = QHBoxLayout()
        self.label_status = QLabel("Status: parado")
        self.label_hz_medio = QLabel("Hz Médio: 0.00")
        self.label_hz_instantaneo = QLabel("Hz Inst: 0.00")
        self.label_hz_suavizado = QLabel("Hz Suav: 0.00")
        # Adiciona os quatro labels na ordem em que serao lidos na tela.
        for w in (self.label_status, self.label_hz_medio, self.label_hz_instantaneo, self.label_hz_suavizado):
            linha_hz.addWidget(w)
        layout.addLayout(linha_hz)

        # Segunda linha: total da sessao e ocupacao atual do [[buffers]].
        linha_cont = QHBoxLayout()
        self.label_amostras = QLabel("Amostras: 0")
        self.label_buffer = QLabel("Buffer: 0 / 10000")
        linha_cont.addWidget(self.label_amostras)
        linha_cont.addWidget(self.label_buffer)
        layout.addLayout(linha_cont)

        # Define os seis eixos, suas unidades e o indice dos labels que serao
        # atualizados posteriormente sem reconstruir a grade.
        self.eixos = ["ax", "ay", "az", "gx", "gy", "gz"]
        self.unidades = {"ax": "g", "ay": "g", "az": "g", "gx": "°/s", "gy": "°/s", "gz": "°/s"}
        self.stats_labels = {}  # {(eixo, metrica): QLabel}

        # Espacamentos tornam colunas e linhas legiveis sem alterar os dados.
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)

        # A celula superior esquerda fica vazia; cada coluna seguinte recebe
        # o nome centralizado e destacado de um eixo.
        grid.addWidget(QLabel(""), 0, 0)
        for col, eixo in enumerate(self.eixos, 1):
            lbl = QLabel(eixo.upper())
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; color: #88c0d0;")
            grid.addWidget(lbl, 0, col)

        # Somente media, desvio e RMS de [[statistics]] sao exibidos, embora o
        # resultado puro contenha outras medidas para consumidores futuros.
        metricas = [("Média", "media"), ("Desvio", "desvio_padrao"), ("RMS", "rms")]

        # Cada linha recebe seu titulo e seis labels de valor inicialmente vazios.
        for row, (nome, key) in enumerate(metricas, 1):
            lbl_row = QLabel(nome)
            lbl_row.setStyleSheet("font-weight: bold;")
            grid.addWidget(lbl_row, row, 0)

            # A chave (eixo, metrica) permite localizar cada QLabel no refresh.
            for col, eixo in enumerate(self.eixos, 1):
                lbl = QLabel("--")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setMinimumWidth(70)
                self.stats_labels[(eixo, key)] = lbl
                grid.addWidget(lbl, row, col)

        # Finaliza a hierarquia do painel e o insere sob os graficos/sinais.
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
        
        # Um layout horizontal recebe os quatro comandos da sessao e da tela.
        layout = QHBoxLayout()

        # Cria os botoes antes de conecta-los aos respectivos slots.
        self.botao_iniciar = QPushButton("Iniciar")
        self.botao_parar = QPushButton("Parar")
        self.botao_limpar = QPushButton("Limpar")
        self.botao_auto_escala = QPushButton("Auto Escala")

        # Mantem a ordem visual Iniciar, Parar, Limpar e Auto Escala.
        layout.addWidget(self.botao_iniciar)
        layout.addWidget(self.botao_parar)
        layout.addWidget(self.botao_limpar)
        layout.addWidget(self.botao_auto_escala)

        # Os sinais clicked executam os metodos no event loop da GUI.
        self.botao_iniciar.clicked.connect(self.iniciar)
            
        self.botao_parar.clicked.connect(self.parar) 
            
        self.botao_limpar.clicked.connect(self.limpar_grafico)
          
        self.botao_auto_escala.clicked.connect(self.autoescala)

        # A barra encerra verticalmente a composicao da interface.
        self.layout.addLayout(layout) #adiciona o layout à janela


    # Cria agendas independentes para desenho e indicadores textuais.
    def criar_timer(self):
        ''' Timer gráfico: 30 FPS (33ms). Timer estatísticas: 2 FPS (500ms).'''
        
        # O timer grafico chama atualizar_grafico a cada 33 ms (~30 FPS).
        self.timer_grafico = QTimer()
        self.timer_grafico.timeout.connect(self.atualizar_grafico)
        self.timer_grafico.start(INTERVALO_GRAFICO_MS)
        
        # O segundo timer atualiza labels a cada 500 ms (2 FPS); uma estatistica
        # mais lenta nao reduz a cadencia visual do primeiro timer.
        self.timer_stats = QTimer()
        self.timer_stats.timeout.connect(self.atualizar_estatisticas)
        self.timer_stats.start(INTERVALO_ESTATISTICAS_MS)


    # Solicita ao [[manager]] o inicio idempotente da sessao de aquisicao.
    def iniciar(self):
        self.manager.iniciar()
        # Oferece retorno imediato ao clique; o timer ajustara o texto conforme
        # o estado publico real do coletor.
        self.label_status.setText("Status: rodando")


    def parar(self):
        # Registra se a sessao produziu algo antes de pedir o encerramento; ja
        # [[manager]].parar() informa se havia uma aquisicao ativa para encerrar.
        houve_amostras = self.manager.coletor.numero_amostras > 0
        encerrou_aquisicao = self.manager.parar()
        # Atualiza o painel assim que as threads e o CSV ja foram finalizados.
        self.label_status.setText("Status: Parado")

        # So abre o Plotly quando a sessao encerrada realmente produziu dados.
        # Assim, um clique em Parar sem coleta nao reabre um CSV antigo.
        if not encerrou_aquisicao or not houve_amostras:
            return

        # Imports locais evitam carregar Plotly no caminho normal de abertura
        # da interface; eles so sao necessarios depois de uma coleta valida.
        from grafico.plotar_csv import csv_mais_recente, plotar_csv
        from pathlib import Path

        # Resolve a pasta de dados a partir deste arquivo, sem depender do cwd.
        pasta_dados = Path(__file__).parents[1] / "dados"

        # Localiza o CSV mais novo que acabou de ser fechado pelo gravador.
        try:
            arquivo_csv = csv_mais_recente(pasta_dados)
        except FileNotFoundError:
            # Mantem a GUI aberta e explica a ausencia de artefato persistido.
            self.label_status.setText("Status: Parado (nenhum CSV encontrado)")
            return

        # [[plotar_csv]] abre a visualizacao opcional do historico completo.
        plotar_csv(arquivo_csv)



    # Atualiza as seis curvas a partir de uma unica visao consistente do buffer.
    def atualizar_grafico(self):
        '''Responsabiliade: ler o estado atual do buffer e desenhar as curvas selecionadas.'''

        # Sem dados, evita snapshot e chamadas de renderizacao desnecessarias.
        if self.manager.buffer.vazio():
            return

        # Um unico [[buffers]].snapshot limita a leitura a 150 amostras e
        # mantem todos os eixos alinhados no mesmo instante logico.
        dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)

        '''if len(dados) < 2 :
            return'''
        
        # Associa cada sinal ao controle de visibilidade, curva e array oriundo
        # daquele snapshot, evitando seis leituras independentes do buffer.
        curvas = {
            'ax': (self.checkbox_ax, self.curva_ax, dados['ax']),
            'ay': (self.checkbox_ay, self.curva_ay, dados['ay']),
            'az': (self.checkbox_az, self.curva_az, dados['az']),
            'gx': (self.checkbox_gx, self.curva_gx, dados['gx']),
            'gy': (self.checkbox_gy, self.curva_gy, dados['gy']),
            'gz': (self.checkbox_gz, self.curva_gz, dados['gz']),
        }

        # X relativo reutilizado: evita criar um novo array e reposicionar
        # o eixo X em todo frame.
        x = self._x_data[:len(dados['contador'])]

        # Curvas marcadas recebem X/Y sem nova checagem de finitude pelo
        # PyQtGraph; as desmarcadas sao apenas ocultadas, nao removidas.
        for _, (check, curva, y) in curvas.items():
            if check.isChecked():
                curva.show()
                curva.setData(x, np.asarray(y), skipFiniteCheck=True)
            else:
                curva.hide()

    def autoescala(self):
        # A autoescala acompanha somente o eixo Y. O X continua fixo em
        # 0..149, portanto nao ha o custo de reposicionar o grafico.
        # Como as curvas recebem dados a cada 33 ms, o Y sera reajustado
        # junto com elas, aproximadamente a 30 FPS.
        # Ativa o comportamento nos dois PlotWidgets existentes.
        for grafico in (self.grafico_aceleracao, self.grafico_giroscopio):
            grafico.enableAutoRange(x=False, y=True)


    def atualizar_estatisticas(self):

        # Reflete a flag publica do [[coletor]], inclusive mudancas ocorridas
        # entre cliques, sem inferir estado apenas pelo texto anterior.
        if self.manager.coletor.rodando:
            self.label_status.setText("Status: Adquirindo")
        else:
            self.label_status.setText("Status: Parado")

        # Formata as tres frequencias publicas do coletor com duas casas:
        # media da sessao, ultima amostra e media movel suavizada.
        self.label_hz_medio.setText(
            f"Hz Médio: {self.manager.coletor.hz_medio:.2f}"
        )

        self.label_hz_instantaneo.setText(
            f"Hz Inst: {self.manager.coletor.hz_inst:.2f}"
        )

        self.label_hz_suavizado.setText(
            f"Hz Suav: {self.manager.coletor.hz_inst_suavizado:.2f}"
        )

        # Exibe separadamente o total adquirido na sessao e a ocupacao limitada
        # do buffer circular; a GUI nao guarda o historico completo.
        self.label_amostras.setText(
            f"Amostras: {self.manager.coletor.numero_amostras}"
        )

        self.label_buffer.setText(
            f"Buffer: {self.manager.buffer.tamanho_atual()} / 10000"
        )

        # Usa outro snapshot unico de 150 pontos para que as estatisticas dos
        # seis eixos descrevam a mesma janela recente a cada tick de 2 FPS.
        snap = self.manager.buffer.snapshot(PONTOS_GRAFICO)

        # Medidas indefinidas aparecem como --; as demais usam quatro casas.
        def fmt(v):
            return "--" if not math.isfinite(v) else f"{v:.4f}"

        # Calcula o registro completo por eixo, mas atualiza somente os tres
        # labels que a grade oferece, acrescentando a unidade correspondente.
        for eixo in self.eixos:
            dados = snap[eixo]
            est = calcular_estatisticas(dados)
            unidade = self.unidades[eixo]
            self.stats_labels[(eixo, "media")].setText(f"{fmt(est.media)} {unidade}")
            self.stats_labels[(eixo, "desvio_padrao")].setText(f"{fmt(est.desvio_padrao)} {unidade}")
            self.stats_labels[(eixo, "rms")].setText(f"{fmt(est.rms)} {unidade}")


    # Reinicia o historico visual sem interromper a sessao nem apagar o CSV.
    def limpar_grafico(self):
        '''Limpa a janela de amostras exibida e as seis curvas atuais.'''

        # O reset logico e protegido pelo Lock do buffer. Se a aquisicao estiver
        # ativa, somente as amostras recebidas depois deste clique reaparecem.
        self.manager.buffer.limpar()

        # Remove os pontos ja desenhados imediatamente, sem aguardar o timer.
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
        
        # Impede novos callbacks enquanto a janela encerra a aquisicao.
        self.timer_grafico.stop()
        self.timer_stats.stop()
        # Aplica a sequencia cooperativa de [[threads-e-encerramento]], inclusive
        # flush/close do gravador, mesmo se o usuario fechar durante a coleta.
        self.manager.parar()
        
        event.accept()  # Aceita o evento de fechamento da janela, permitindo que a aplicação seja encerrada corretamente.
