# Argumentos do processo sao entregues a QApplication e o codigo do loop Qt
# volta ao sistema operacional ao encerrar esta interface de depuracao.
import sys

# PyQtGraph fornece o widget e a curva; QtCore/QtWidgets fornecem timer e UI.
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

# Esta janela usa o mesmo singleton de aquisicao documentado em [[manager]].
from sensor.manager import manager


# Interface minima para inspecionar apenas o eixo ax; [[janela]] continua sendo
# a interface principal para os seis sinais e suas estatisticas.
class Janela(QtWidgets.QMainWindow):

    def __init__(self):
        # Inicializa a infraestrutura de QMainWindow antes dos widgets filhos.
        super().__init__()

        # Identifica a janela de diagnostico e define seu tamanho inicial.
        self.setWindowTitle("Sensor de Vibração")

        self.resize(1200, 600)

        # Um unico PlotWidget ocupa a area central desta interface enxuta.
        self.grafico = pg.PlotWidget()
        self.setCentralWidget(self.grafico)

        # A unica curva, amarela, recebera as amostras recentes de ax.
        self.curva = self.grafico.plot(
            pen="y",
            width=2
        )

        # Grade e rotulos tornam explicitas a unidade vertical e a ordenacao
        # horizontal por amostras, sem construir os paineis da [[janela]].
        self.grafico.showGrid(x=True, y=True)

        self.grafico.setLabel("left", "Aceleração (g)")
        self.grafico.setLabel("bottom", "Amostras")

        # A aquisicao comeca automaticamente neste utilitario de depuracao.
        manager.iniciar()

        # Timer proprio solicita redesenho a cada 16 ms (aproximadamente
        # 60 FPS), independentemente dos timers usados pela janela principal.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.atualizar)
        self.timer.start(16)       # ~60 FPS

    def atualizar(self):

        # A propriedade de compatibilidade ax vem do buffer circular mantido
        # pelo [[coletor]] por meio de [[buffers]].
        dados = manager.buffer

        # Evita desenhar uma curva sem ao menos dois pontos.
        if len(dados.ax) < 2:
            return

        # Converte a copia cronologica de ax em lista e limita a visualizacao
        # as 500 amostras mais recentes; nenhum outro eixo e consultado.
        ax = list(dados.ax)[-500:]

        # Substitui os pontos da curva no tick atual do timer.
        self.curva.setData(ax)

    def closeEvent(self, event):

        # O mesmo [[manager]] encerra coletor e gravador antes de a janela
        # aceitar o fechamento, preservando o fluxo de [[threads-e-encerramento]].
        manager.parar()

        event.accept()


# Este arquivo e um script de depuracao: cria sua propria e unica QApplication,
# constroi/exibe a janela minima e assume o event loop no nivel do modulo.
app = QtWidgets.QApplication(sys.argv)

janela = Janela()
janela.show()

sys.exit(app.exec())
