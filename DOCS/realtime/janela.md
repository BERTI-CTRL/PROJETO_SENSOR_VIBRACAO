# janela.py — explicação completa, em ordem de linhas

O arquivo [realtime/janela.py](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\realtime\janela.py) constrói a tela de monitoramento do sensor. Ele mostra dois gráficos, controles de visibilidade, frequência, estatísticas e botões para controlar a sessão.

Ele não lê o Arduino nem escreve o CSV diretamente. A janela pede dados ao manager; o manager coordena a coleta e a gravação.

```text
Arduino → serial_reader.py → coletor.py → BufferSensores
                                              ↓
                                      janela.py
                           ┌──────────────────┼──────────────────┐
                           ↓                  ↓                  ↓
                     gráficos           estatísticas           botões
```

| Termo | Significado |
|---|---|
| GUI | Interface visual: janela, botão, texto e gráfico. |
| widget | Elemento visual individual, como QLabel, QPushButton ou PlotWidget. |
| layout | Organizador que posiciona widgets. |
| callback/slot | Método chamado por um evento, como clique ou timer. |
| event loop | Ciclo do Qt que recebe eventos e atualiza a tela. |
| QTimer | Relógio que dispara atualizações periódicas. |
| snapshot | Cópia coerente do buffer usada pela interface. |
| curva | Linha do gráfico que representa um eixo do sensor. |

## Linhas 1 a 28: imports

```python
"""Janela PyQt para monitoramento dos sinais de vibracao em tempo real."""
import math
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QVBoxLayout, QWidget,
)
from sensor.manager import manager
from utils.statistics import calcular_estatisticas
```

A primeira linha é uma docstring: texto que descreve o módulo. Não monta a janela.

A linha com math fornece math.isfinite, usado mais adiante para decidir se uma estatística pode ser exibida como número ou deve aparecer como --.

NumPy é importado com o apelido np. Ele cria o eixo X reutilizável e converte vetores antes de enviá-los para o gráfico.

PyQtGraph, apelidado pg, cria os gráficos e as canetas coloridas. QTimer é o temporizador da interface; Qt contém, entre outros itens, a regra de alinhamento central de textos.

Os widgets importados têm papéis distintos:

```python
QMainWindow  # janela principal
QWidget      # recipiente visual genérico
QVBoxLayout  # organiza verticalmente
QHBoxLayout  # organiza horizontalmente
QGridLayout  # organiza em linhas e colunas
QGroupBox    # caixa visual com título
QLabel       # texto
QPushButton  # botão
QCheckBox    # caixa de seleção
```

O manager é a instância global que inicia e para o pipeline. calcular_estatisticas é a função que calcula média, desvio padrão e RMS para cada eixo.

## Linhas 31 a 59: configuração global

```python
import pyqtgraph as pg
pg.setConfigOptions(antialias=False, useOpenGL=True)

INTERVALO_GRAFICO_MS = 33
INTERVALO_ESTATISTICAS_MS = 500
PONTOS_GRAFICO = 150

INTERVALO_EIXO_Y_ACELERAÇÃO = (-40, 40)
INTERVALO_EIXO_Y_GIROSCÓPIO = (-50, 50)
MOUSE_ATIVADO = False

EIXOS = ("ax", "ay", "az", "gx", "gy", "gz")
CORES = {"ax": "y", "ay": "g", "az": "c", "gx": "r", "gy": "m", "gz": "w"}
```

A segunda importação de pg é redundante: ela referencia o mesmo módulo já importado. A linha setConfigOptions desliga antialias, que suavizaria visualmente linhas mas custa desempenho, e solicita OpenGL para acelerar o desenho.

33 ms é aproximadamente 30 atualizações por segundo: 1000 / 33 ≈ 30. As estatísticas atualizam a cada 500 ms, ou duas vezes por segundo. Essa separação evita calcular medidas seis vezes a cada frame.

PONTOS_GRAFICO limita a tela às 150 amostras recentes. Não limita a coleta nem apaga o CSV.

As duas tuplas definem somente a escala inicial vertical. Aceleração está em g; giroscópio em graus por segundo. MOUSE_ATIVADO igual a False desliga zoom e arraste por mouse. EIXOS e CORES registram a ordem e a paleta dos sinais; as cores também aparecem diretamente ao criar cada curva.

## Linhas 62 a 116: classe Janela e construtor

```python
class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Monitor de Vibração")
        self.resize(1300, 800)
```

class cria o molde da janela. Janela herda QMainWindow, portanto já possui o comportamento básico de uma janela Qt.

super().__init__ inicializa essa parte herdada antes de criar widgets. self.manager guarda a mesma instância global importada acima. setWindowTitle define o texto da barra de título. resize define largura 1300 e altura 800, em pixels, como tamanho inicial.

```python
self.grafico_aceleracao = None
self.grafico_giroscopio = None
self.curva_ax = None
self.curva_ay = None
self.curva_az = None
self.curva_gx = None
self.curva_gy = None
self.curva_gz = None
```

Essas linhas criam atributos antes de atribuir widgets reais. None significa “ainda não existe objeto”. criar_grafico substitui cada referência pelo gráfico ou curva correspondente.

```python
self._x_data = np.arange(PONTOS_GRAFICO)
self.criar_interface()
self.criar_timer()
```

np.arange(150) produz os números de 0 a 149. O eixo X é criado uma vez e reaproveitado para reduzir alocações.

criar_interface vem antes de criar_timer porque o timer pode chamar métodos logo após começar. Se ele começasse antes dos gráficos e labels existirem, o callback poderia tentar acessar um atributo incompleto.

## Linhas 119 a 138: estrutura principal da interface

```python
def criar_interface(self):
    central = QWidget()
    self.setCentralWidget(central)
    self.layout = QVBoxLayout()
    central.setLayout(self.layout)

    self.criar_grafico()
    self.criar_painel_sinais()
    self.criar_painel_estatisticas()
    self.criar_barra_botoes()
```

QMainWindow precisa de um widget central. central é esse recipiente. setCentralWidget entrega sua posse à janela.

QVBoxLayout empilha itens de cima para baixo. Ao ligar esse layout ao widget central, as quatro chamadas seguintes passam a montar a tela nessa ordem: gráficos, sinais, estatísticas e barra de botões.

## Linhas 140 a 187: os dois gráficos e seis curvas

```python
self.grafico_aceleracao = pg.PlotWidget(enableMenu=False)
self.grafico_aceleracao.setBackground("k")
self.grafico_aceleracao.showGrid(x=True, y=True, alpha=0.3)
self.grafico_aceleracao.setLabel("left", "Aceleração (g)")
self.grafico_aceleracao.setLabel("bottom", "Amostras (n)")
self.grafico_aceleracao.setMouseEnabled(
    x=MOUSE_ATIVADO, y=MOUSE_ATIVADO
)
self.layout.addWidget(self.grafico_aceleracao)
```

PlotWidget é o gráfico do PyQtGraph. enableMenu=False remove seu menu de contexto. k é preto. showGrid desenha linhas de grade horizontal e vertical com transparência 0.3. As duas chamadas setLabel nomeiam os eixos. setMouseEnabled usa a constante global; com False, não há pan nem zoom. addWidget coloca o gráfico no layout vertical.

```python
self.grafico_aceleracao.enableAutoRange(x=False, y=False)
self.grafico_aceleracao.setXRange(0, PONTOS_GRAFICO, padding=0)
self.grafico_aceleracao.setYRange(
    INTERVALO_EIXO_Y_ACELERAÇÃO[0],
    INTERVALO_EIXO_Y_ACELERAÇÃO[1],
    padding=0,
)
```

enableAutoRange desliga o reajuste automático inicial. X fica sempre de 0 a 150; Y começa entre -40 e 40. padding=0 remove espaço extra nas bordas.

```python
self.curva_ax = self.grafico_aceleracao.plot(
    pen=pg.mkPen("y", width=1), name="Ax"
)
self.curva_ay = self.grafico_aceleracao.plot(
    pen=pg.mkPen("g", width=1), name="Ay"
)
self.curva_az = self.grafico_aceleracao.plot(
    pen=pg.mkPen("c", width=1), name="Az"
)
```

plot cria três curvas inicialmente sem dados. mkPen cria a caneta: y é amarelo, g é verde e c é ciano; width=1 cria uma linha fina.

```python
self.grafico_giroscopio = pg.PlotWidget(enableMenu=False)
self.grafico_giroscopio.setBackground("k")
self.grafico_giroscopio.showGrid(x=True, y=True, alpha=0.3)
self.grafico_giroscopio.setLabel("left", "Velocidade angular (°/s)")
self.grafico_giroscopio.setLabel("bottom", "Amostras (n)")
self.grafico_giroscopio.setMouseEnabled(
    x=MOUSE_ATIVADO, y=MOUSE_ATIVADO
)
self.layout.addWidget(self.grafico_giroscopio)
```

O segundo gráfico repete a estrutura para giroscópio. Ele é separado porque as unidades e amplitudes não são comparáveis diretamente com aceleração.

```python
self.grafico_giroscopio.enableAutoRange(x=False, y=False)
self.grafico_giroscopio.setXRange(0, PONTOS_GRAFICO, padding=0)
self.grafico_giroscopio.setYRange(
    INTERVALO_EIXO_Y_GIROSCÓPIO[0],
    INTERVALO_EIXO_Y_GIROSCÓPIO[1],
    padding=0,
)
self.curva_gx = self.grafico_giroscopio.plot(pen=pg.mkPen("r", width=1), name="Gx")
self.curva_gy = self.grafico_giroscopio.plot(pen=pg.mkPen("m", width=1), name="Gy")
self.curva_gz = self.grafico_giroscopio.plot(pen=pg.mkPen("w", width=1), name="Gz")
```

As linhas fazem a mesma configuração, agora com faixa -50 a 50. r é vermelho, m é magenta/rosa e w é branco.

## Linhas 190 a 232: painel Sinais

```python
grupo_sinais = QGroupBox("Sinais")
layout = QGridLayout()
```

QGroupBox cria uma caixa com o título Sinais. QGridLayout posiciona elementos por linha e coluna.

```python
self.checkbox_ax = QCheckBox("ax (amarelo)")
self.checkbox_ax.setChecked(True)
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
```

Cada par cria uma caixa e a marca inicialmente. As caixas não desligam o sensor: elas controlam apenas a visibilidade da curva no próximo atualizar_grafico.

```python
layout.addWidget(self.checkbox_ax, 0, 0)
layout.addWidget(self.checkbox_ay, 0, 1)
layout.addWidget(self.checkbox_az, 0, 2)
layout.addWidget(self.checkbox_gx, 1, 0)
layout.addWidget(self.checkbox_gy, 1, 1)
layout.addWidget(self.checkbox_gz, 1, 2)
grupo_sinais.setLayout(layout)
self.layout.addWidget(grupo_sinais)
```

Os três acelerômetros ficam na linha zero, colunas 0, 1 e 2. Os três giroscópios ficam na linha um. Depois a grade é colocada dentro do grupo, e o grupo entra no layout principal.

## Linhas 235 a 317: painel Estatísticas

```python
grupo_estatisticas = QGroupBox("Estatísticas")
layout = QVBoxLayout()
linha_hz = QHBoxLayout()
self.label_status = QLabel("Status: parado")
self.label_hz_medio = QLabel("Hz Médio: 0.00")
self.label_hz_instantaneo = QLabel("Hz Inst: 0.00")
self.label_hz_suavizado = QLabel("Hz Suav: 0.00")
```

O grupo contém os indicadores. linha_hz organiza horizontalmente status e três frequências. QLabel cria texto; os valores iniciais são neutros porque ainda não houve coleta.

```python
for w in (
    self.label_status, self.label_hz_medio,
    self.label_hz_instantaneo, self.label_hz_suavizado,
):
    linha_hz.addWidget(w)
layout.addLayout(linha_hz)
```

O for evita repetir addWidget quatro vezes. Cada w é temporariamente um label da tupla. Depois a linha inteira entra no layout vertical.

```python
linha_cont = QHBoxLayout()
self.label_amostras = QLabel("Amostras: 0")
self.label_buffer = QLabel("Buffer: 0 / 10000")
linha_cont.addWidget(self.label_amostras)
linha_cont.addWidget(self.label_buffer)
layout.addLayout(linha_cont)
```

A segunda linha mostra duas informações diferentes: amostras recebidas na sessão e quantidade ainda preservada no buffer circular.

```python
self.eixos = ["ax", "ay", "az", "gx", "gy", "gz"]
self.unidades = {
    "ax": "g", "ay": "g", "az": "g",
    "gx": "°/s", "gy": "°/s", "gz": "°/s",
}
self.stats_labels = {}
grid = QGridLayout()
grid.setHorizontalSpacing(12)
grid.setVerticalSpacing(4)
```

self.eixos determina a ordem das colunas. self.unidades associa cada eixo à unidade. stats_labels será um dicionário que permitirá localizar uma célula específica. Os espaçamentos afetam apenas aparência.

```python
grid.addWidget(QLabel(""), 0, 0)
for col, eixo in enumerate(self.eixos, 1):
    lbl = QLabel(eixo.upper())
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("font-weight: bold; color: #88c0d0;")
    grid.addWidget(lbl, 0, col)
```

A primeira célula da tabela fica vazia, pois a coluna zero é usada pelos nomes das métricas. enumerate com início 1 devolve pares como (1, ax). upper transforma ax em AX. AlignCenter centraliza o texto e setStyleSheet aplica negrito/cor.

```python
metricas = [
    ("Média", "media"),
    ("Desvio", "desvio_padrao"),
    ("RMS", "rms"),
]
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
```

metricas define texto exibido e nome do atributo devolvido por calcular_estatisticas. O primeiro for cria cada linha. O segundo cria seis células por métrica, todas iniciando em --. A chave composta, por exemplo (ax, rms), permite atualizar o label certo mais tarde sem procurar visualmente pela grade.

```python
layout.addLayout(grid)
grupo_estatisticas.setLayout(layout)
self.layout.addWidget(grupo_estatisticas)
```

Essas linhas concluem a hierarquia: grade dentro do painel; painel dentro da janela.

## Linhas 320 a 359: barra de botões

```python
layout = QHBoxLayout()
self.botao_iniciar = QPushButton("Iniciar")
self.botao_parar = QPushButton("Parar")
self.botao_limpar = QPushButton("Limpar")
self.botao_auto_escala = QPushButton("Auto Escala")
```

O layout horizontal organiza quatro QPushButton.

```python
layout.addWidget(self.botao_iniciar)
layout.addWidget(self.botao_parar)
layout.addWidget(self.botao_limpar)
layout.addWidget(self.botao_auto_escala)

self.botao_iniciar.clicked.connect(self.iniciar)
self.botao_parar.clicked.connect(self.parar)
self.botao_limpar.clicked.connect(self.limpar_grafico)
self.botao_auto_escala.clicked.connect(self.autoescala)
self.layout.addLayout(layout)
```

As quatro primeiras linhas definem a ordem visual. clicked é o sinal emitido pelo Qt ao clicar. connect registra qual método deve responder: iniciar, parar, limpar_grafico ou autoescala. A última linha anexa a barra à interface.

## Linhas 362 a 375: timers

```python
self.timer_grafico = QTimer()
self.timer_grafico.timeout.connect(self.atualizar_grafico)
self.timer_grafico.start(INTERVALO_GRAFICO_MS)

self.timer_stats = QTimer()
self.timer_stats.timeout.connect(self.atualizar_estatisticas)
self.timer_stats.start(INTERVALO_ESTATISTICAS_MS)
```

Há dois timers, não duas threads. Ambos trabalham no event loop da GUI. O primeiro pede redesenho a cada 33 ms. O segundo pede atualização de textos e cálculos a cada 500 ms. Eles são salvos em self para que closeEvent consiga pará-los.

## Linhas 378 a 416: iniciar e parar a sessão

```python
def iniciar(self):
    self.manager.iniciar()
    self.label_status.setText("Status: rodando")
```

O botão não abre serial por conta própria. manager.iniciar cria fila, gravador e thread do coletor. setText oferece resposta visual imediata; no próximo timer o status será atualizado pela flag real do coletor.

```python
def parar(self):
    houve_amostras = self.manager.coletor.numero_amostras > 0
    encerrou_aquisicao = self.manager.parar()
    self.label_status.setText("Status: Parado")
    if not encerrou_aquisicao or not houve_amostras:
        return
```

Primeiro, houve_amostras registra se a sessão produziu algo antes do encerramento. manager.parar pede fim ao coletor, espera as threads e fecha o CSV. Se não existia sessão ou não havia dados, return encerra o método sem abrir um CSV antigo.

```python
from grafico.plotar_csv import csv_mais_recente, plotar_csv
from pathlib import Path
pasta_dados = Path(__file__).parents[1] / "dados"
try:
    arquivo_csv = csv_mais_recente(pasta_dados)
except FileNotFoundError:
    self.label_status.setText("Status: Parado (nenhum CSV encontrado)")
    return
plotar_csv(arquivo_csv)
```

Os imports são locais porque Plotly só é necessário depois de parar. Path(__file__).parents[1] encontra a raiz do projeto a partir deste arquivo; / dados forma o caminho da pasta de CSVs. Se não houver arquivo, a exceção é tratada e a janela continua aberta. Se existir, plotar_csv abre a visualização do histórico completo.

## Linhas 420 a 457: atualizar as curvas

```python
if self.manager.buffer.vazio():
    return
dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)
```

Se ainda não existe leitura, return evita trabalho visual. snapshot pede uma única cópia das últimas 150 amostras. Um único snapshot mantém ax, ay, az, gx, gy e gz no mesmo instante lógico.

```python
curvas = {
    "ax": (self.checkbox_ax, self.curva_ax, dados["ax"]),
    "ay": (self.checkbox_ay, self.curva_ay, dados["ay"]),
    "az": (self.checkbox_az, self.curva_az, dados["az"]),
    "gx": (self.checkbox_gx, self.curva_gx, dados["gx"]),
    "gy": (self.checkbox_gy, self.curva_gy, dados["gy"]),
    "gz": (self.checkbox_gz, self.curva_gz, dados["gz"]),
}
x = self._x_data[:len(dados["contador"])]
```

O dicionário junta, para cada eixo, o checkbox, a curva e o vetor Y. x é uma fatia do eixo reaproveitado, com exatamente o mesmo tamanho do número de amostras no snapshot. O eixo X é relativo: 0 até n-1; não representa tempo real nem contador do Arduino.

```python
for _, (check, curva, y) in curvas.items():
    if check.isChecked():
        curva.show()
        curva.setData(x, np.asarray(y), skipFiniteCheck=True)
    else:
        curva.hide()
```

items percorre os pares chave/valor do dicionário. _ recebe a chave e informa que ela não será usada. isChecked consulta a caixa correspondente. Se marcada, show torna a curva visível e setData recebe X e Y. np.asarray garante que Y seja um array NumPy. skipFiniteCheck=True economiza uma checagem adicional de NaN/infinito feita pelo PyQtGraph. Se desmarcada, hide oculta a curva, mas não interrompe coleta, buffer, estatística ou CSV.

## Linhas 459 a 466: autoescala

```python
for grafico in (
    self.grafico_aceleracao,
    self.grafico_giroscopio,
):
    grafico.enableAutoRange(x=False, y=True)
```

O for aplica a mesma regra aos dois gráficos. X continua fixo; somente Y passa a se ajustar conforme a amplitude das curvas. Nenhuma amostra é alterada.

## Linhas 469 a 518: atualizar status e estatísticas

```python
if self.manager.coletor.rodando:
    self.label_status.setText("Status: Adquirindo")
else:
    self.label_status.setText("Status: Parado")
```

Esse trecho não confia só no texto deixado pelos botões: consulta a flag real do coletor.

```python
self.label_hz_medio.setText(
    f"Hz Médio: {self.manager.coletor.hz_medio:.2f}"
)
self.label_hz_instantaneo.setText(
    f"Hz Inst: {self.manager.coletor.hz_inst:.2f}"
)
self.label_hz_suavizado.setText(
    f"Hz Suav: {self.manager.coletor.hz_inst_suavizado:.2f}"
)
```

As três f-strings leem medidas calculadas pelo coletor. :.2f significa mostrar duas casas decimais.

```python
self.label_amostras.setText(
    f"Amostras: {self.manager.coletor.numero_amostras}"
)
self.label_buffer.setText(
    f"Buffer: {self.manager.buffer.tamanho_atual()} / 10000"
)
snap = self.manager.buffer.snapshot(PONTOS_GRAFICO)
```

numero_amostras é o total aceito na sessão. tamanho_atual é limitado pela capacidade do buffer. O valor 10000 no texto está fixo no código. snap é uma nova fotografia para a rodada de estatísticas.

```python
def fmt(v):
    return "--" if not math.isfinite(v) else f"{v:.4f}"
```

fmt é uma função local. math.isfinite retorna False para NaN e infinito. Nesse caso a tela recebe --; caso contrário recebe quatro casas decimais.

```python
for eixo in self.eixos:
    dados = snap[eixo]
    est = calcular_estatisticas(dados)
    unidade = self.unidades[eixo]
    self.stats_labels[(eixo, "media")].setText(
        f"{fmt(est.media)} {unidade}"
    )
    self.stats_labels[(eixo, "desvio_padrao")].setText(
        f"{fmt(est.desvio_padrao)} {unidade}"
    )
    self.stats_labels[(eixo, "rms")].setText(
        f"{fmt(est.rms)} {unidade}"
    )
```

O for percorre os seis eixos. snap[eixo] seleciona a série numérica. calcular_estatisticas devolve um objeto com várias medidas. unidade procura g ou °/s. As três últimas linhas localizam cada célula criada anteriormente por chave e atualizam média, desvio padrão e RMS.

## Linhas 521 a 535: limpar gráficos

```python
self.manager.buffer.limpar()
self.curva_ax.clear()
self.curva_ay.clear()
self.curva_az.clear()
self.curva_gx.clear()
self.curva_gy.clear()
self.curva_gz.clear()
```

buffer.limpar faz a limpeza lógica do histórico em memória. As seis chamadas clear removem os pontos já desenhados imediatamente. Isso não para a serial, não zera numero_amostras e não apaga o CSV. Se a coleta continuar, novas amostras aparecerão no próximo timer.

## Linhas 537 a 552: fechar a janela

```python
def closeEvent(self, event):
    self.timer_grafico.stop()
    self.timer_stats.stop()
    self.manager.parar()
    event.accept()
```

closeEvent é chamado automaticamente pelo Qt quando o usuário fecha a janela. stop impede novos callbacks enquanto o fechamento ocorre. manager.parar encerra coleta e gravador de modo organizado. event.accept confirma ao Qt que o fechamento pode continuar.

## Resumo mental

Janela é a consumidora visual do projeto. Ela tira snapshots recentes do buffer, desenha seis sinais em dois gráficos, calcula textos mais lentamente e delega início/parada ao manager. Checkboxes mudam apenas visibilidade; limpar apaga apenas o histórico em memória; fechar a janela interrompe timers e encerra a sessão corretamente.

## Complemento: a árvore visual criada pela janela

As chamadas de criação montam esta hierarquia. Ela ajuda a entender por que cada layout existe:

```text
Janela (QMainWindow)
└── central (QWidget)
    └── self.layout (QVBoxLayout)
        ├── grafico_aceleracao (PlotWidget)
        ├── grafico_giroscopio (PlotWidget)
        ├── grupo_sinais (QGroupBox)
        │   └── QGridLayout com seis checkboxes
        ├── grupo_estatisticas (QGroupBox)
        │   └── QVBoxLayout
        │       ├── linha_hz (QHBoxLayout)
        │       ├── linha_cont (QHBoxLayout)
        │       └── grid (QGridLayout)
        └── barra de botões (QHBoxLayout)
```

A ordem não é apenas estética. Um widget precisa ter um dono: quando a janela fecha, Qt destrói o widget central, que destrói o layout e os widgets que pertencem a ele. Isso evita precisar fechar manualmente cada botão, label ou gráfico.

## Complemento das linhas 276 a 317: como nasce cada célula da tabela

O bloco completo usa dois loops aninhados:

```python
metricas = [
    ("Média", "media"),
    ("Desvio", "desvio_padrao"),
    ("RMS", "rms"),
]

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
```

Na primeira volta do loop externo:

```python
row = 1
nome = "Média"
key = "media"
```

O label “Média” vai para a linha 1, coluna 0. Depois o loop interno percorre os seis eixos:

```python
col = 1, eixo = "ax"  # célula da média de ax
col = 2, eixo = "ay"  # célula da média de ay
# ...
col = 6, eixo = "gz"  # célula da média de gz
```

O dicionário recebe, por exemplo:

```python
self.stats_labels[("ax", "media")] = label_da_celula
self.stats_labels[("gz", "media")] = outro_label
```

Nas duas voltas seguintes, a mesma regra cria as linhas “Desvio” e “RMS”. Ao final existem 18 células de valor: três métricas multiplicadas por seis eixos. Essa preparação só ocorre uma vez no construtor; atualizar_estatisticas apenas troca texto, o que é mais leve do que recriar widgets.

## Complemento das linhas 420 a 457: um frame de gráfico, passo a passo

Suponha que o buffer tenha 150 amostras recentes. A cada disparo do timer gráfico, o método executa este fluxo:

```text
QTimer.timeout
      ↓
atualizar_grafico()
      ↓
buffer.vazio()?
 ├── sim → return
 └── não → snapshot(150)
                ↓
         monta x e os seis vetores y
                ↓
         mostra ou oculta cada curva
```

Para uma curva marcada, estas linhas têm efeitos separados:

```python
curva.show()
curva.setData(x, np.asarray(y), skipFiniteCheck=True)
```

show torna a curva elegível para aparecer. setData substitui todos os pontos anteriores pelos vetores atuais. Portanto, o gráfico não acrescenta uma linha por vez: ele redesenha a janela recente inteira.

Se o checkbox estiver desmarcado:

```python
curva.hide()
```

A curva desaparece, mas y continua existindo no snapshot. O coletor continua recebendo o eixo, o buffer continua armazenando-o, as estatísticas continuam calculando-o e o CSV continua gravando-o.

## Complemento das linhas 469 a 518: dois tempos diferentes de atualização

O gráfico e o painel não representam necessariamente a mesma amostra exata, porque usam timers diferentes:

```text
0 ms     timer_grafico: desenha snapshot recente
33 ms    timer_grafico: desenha novo snapshot
66 ms    timer_grafico: desenha novo snapshot
...
500 ms   timer_stats: lê outro snapshot e atualiza textos
```

Isso é uma escolha de desempenho. A aparência do sinal precisa responder rapidamente; média, RMS e textos não precisam mudar trinta vezes por segundo.

O cálculo por eixo é:

```python
dados = snap[eixo]
est = calcular_estatisticas(dados)
```

dados é um vetor, por exemplo todas as últimas amostras de ax. est contém diversas medidas, mas a janela usa somente:

```python
est.media
est.desvio_padrao
est.rms
```

Média mostra o nível central dos valores. Desvio padrão mede a dispersão em torno da média. RMS resume a intensidade do sinal e é especialmente útil para vibração.

## Complemento: diferença entre os quatro botões

| Botão | Método | O que muda | O que continua igual |
|---|---|---|---|
| Iniciar | iniciar() | Pede ao manager uma nova sessão. | A tela e seus timers já existiam. |
| Parar | parar() | Encerra coletor, gravador e CSV; pode abrir o CSV no Plotly. | O buffer continua com os dados recentes até ser limpo ou sobrescrito. |
| Limpar | limpar_grafico() | Esvazia o histórico visual e remove pontos das curvas. | Serial, CSV, fila e contador da sessão continuam se a coleta estiver ativa. |
| Auto Escala | autoescala() | PyQtGraph passa a ajustar o eixo Y. | Dados, eixo X e taxa de coleta não mudam. |

Durante uma coleta ativa, clicar em Limpar produz esta sequência:

```text
buffer.limpar()
      ↓
curvas.clear()
      ↓
o coletor continua recebendo novas amostras
      ↓
o próximo timer desenha apenas as amostras após a limpeza
```

## Complemento: por que a janela usa manager em vez de Coletor diretamente

Seria possível a interface criar Coletor por conta própria, mas isso exigiria que ela também soubesse criar a fila, iniciar o GravadorWorker, criar threads e parar tudo na ordem correta. Em vez disso, ela usa:

```python
self.manager.iniciar()
self.manager.parar()
```

Essa divisão deixa a janela responsável por interação visual e deixa manager.py responsável pelo ciclo de vida técnico:

```text
Janela: clique, texto e gráfico
Manager: fila, threads, início e join
Coletor: serial, frequência e buffer
GravadorWorker: consumo da fila
GravadorCSV: arquivo
```

## Complemento: limites práticos desta interface

O eixo X do gráfico é uma posição relativa dentro da janela de 150 pontos:

```python
x = self._x_data[:len(dados["contador"])]
```

Assim, ele vai de 0 até n-1 em cada redraw. Ele não mostra segundos, nem o contador do Arduino, nem lacunas de transmissão. Para investigar tempo físico ou perdas, use tempo_arduino_us e contador no CSV ou no buffer.

O texto abaixo também contém um valor fixo:

```python
f"Buffer: {self.manager.buffer.tamanho_atual()} / 10000"
```

Ele descreve corretamente o projeto enquanto BufferSensores for criado com a capacidade padrão de 10.000. Se futuramente alguém criar o buffer com outro tamanho, o segundo número mostrado na tela deverá ser atualizado para refletir tamanho_maximo.
