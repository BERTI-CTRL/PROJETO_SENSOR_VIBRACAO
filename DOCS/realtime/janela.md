# janela.py

`realtime/janela.py` implementa a interface PyQt6 de monitoramento: dois gráficos para seis eixos, seletores de visibilidade, indicadores de sessão e estatísticas recentes. Ela controla a sessão pelo singleton [[manager]], mas não abre a serial nem grava CSV diretamente.

## Resumo, entrada e saída

```text
manager.buffer.snapshot(150) ─┬→ seis curvas PyQtGraph, ~30 FPS
                              └→ statistics por eixo, 2 FPS

botões → manager.iniciar()/parar() → coletor, gravador_worker e CSV
```

A única classe, `Janela(QMainWindow)`, recebe indiretamente o estado público do [[manager]]: buffer, frequências e contadores do [[coletor]]. Ela produz atualizações visuais, pedidos de início/parada e, depois de uma sessão válida, abre o CSV completo via [[plotar_csv]]. Não há EDO, integração numérica ou modelo físico: os dados são apresentados e resumidos depois de recebidos.

## Dependências

- `numpy`: eixo X reutilizável e vetores enviados ao desenho.
- `pyqtgraph`: `PlotWidget`, curvas e canetas. `pg.setConfigOptions(antialias=False, useOpenGL=True)` na linha 39 privilegia renderização rápida.
- PyQt6: janela, layouts, botoes, labels, checkboxes e `QTimer`.
- [[manager]]: singleton que orquestra [[coletor]] e [[gravador_worker]].
- [[statistics]]: função `calcular_estatisticas` para cada eixo.
- [[plotar_csv]]: importado apenas quando uma sessão com dados é parada.

> [!note] Importacao duplicada
> `pyqtgraph as pg` aparece nas linhas 9 e 36. A segunda importação é redundante; a configuração global da linha 39 é que produz efeito.

## Constantes e estratégia de desempenho

```python
INTERVALO_GRAFICO_MS = 33
INTERVALO_ESTATISTICAS_MS = 500
PONTOS_GRAFICO = 150
```

O gráfico roda aproximadamente a 30 FPS, enquanto textos e estatísticas rodam a 2 FPS. Isto separa o caminho quente de renderização do cálculo menos urgente. `self._x_data = np.arange(PONTOS_GRAFICO)` é criado uma única vez e fatiado a cada frame, evitando uma nova alocação do eixo X.

`MOUSE_ATIVADO = False` desativa zoom/pan. As faixas Y iniciais são `(-40, 40)` g e `(-50, 50)` °/s: enquadramentos visuais, não limites ou calibração do sensor. `EIXOS` e `CORES` no módulo não dirigem a atualização atual; a classe repete eixos em `self.eixos` e define canetas diretamente.

## Classe `Janela`: construção top-down

### `__init__()`

Nas linhas 84–116, inicializa `QMainWindow`, retém `self.manager = manager`, define título/tamanho, prepara referências dos gráficos/curvas, cria `_x_data`, e executa:

```python
self.criar_interface()
self.criar_timer()
```

A ordem evita que timers chamem callbacks antes de os widgets existirem.

### `criar_interface()`

Cria um `QWidget` central com `QVBoxLayout`, depois empilha: `criar_grafico`, `criar_painel_sinais`, `criar_painel_estatisticas` e `criar_barra_botoes`. A sequência de chamadas é a hierarquia vertical final.

### `criar_grafico()`

Cria dois `PlotWidget`s com fundo preto, grade, menu desabilitado e mouse conforme a constante. Aceleração recebe curvas `ax`/`ay`/`az`; giroscópio recebe `gx`/`gy`/`gz`. Ambos iniciam com X fixo em 0–150 e Y sem auto-range:

```python
self.grafico_aceleracao.setXRange(0, PONTOS_GRAFICO, padding=0)
self.grafico_aceleracao.setYRange(-40, 40, padding=0)
```

Separar os tipos de medida evita que amplitudes angulares comprimam variacoes de aceleracao.

### `criar_painel_sinais()`

Cria seis `QCheckBox`, todos marcados. Eles não ligam/desligam coleta: `atualizar_grafico()` consulta cada `isChecked()` e mostra ou oculta a curva. Dados, buffer, estatísticas e CSV continuam sendo processados.

### `criar_painel_estatisticas()`

Cria labels para status, três frequências, amostras e buffer. Depois monta uma grade de seis eixos por três métricas e guarda cada label em `self.stats_labels[(eixo, metrica)]`. A interface mostra média, desvio padrão e RMS; [[statistics]] também calcula outras medidas que aqui não são exibidas.

### `criar_barra_botoes()` e `criar_timer()`

Os botões conectam-se a `iniciar`, `parar`, `limpar_grafico` e `autoescala`. Os dois timers são independentes:

```python
self.timer_grafico.timeout.connect(self.atualizar_grafico)
self.timer_grafico.start(INTERVALO_GRAFICO_MS)
self.timer_stats.timeout.connect(self.atualizar_estatisticas)
self.timer_stats.start(INTERVALO_ESTATISTICAS_MS)
```

`QTimer` executa callbacks no event loop da GUI; não é uma thread adicional.

## Métodos de controle

### `iniciar()`

Chama `self.manager.iniciar()` e muda o label para “rodando”. [[manager]] evita iniciar uma segunda sessão enquanto a thread coletora está viva; o timer de estatísticas posteriormente exibe a flag efetiva `coletor.rodando`.

### `parar()`

Registra se houve amostras, chama `manager.parar()` e só então procura/abre CSV se a sessão foi encerrada e produziu dados:

```python
arquivo_csv = csv_mais_recente(pasta_dados)
plotar_csv(arquivo_csv)
```

Se não houver CSV, o `FileNotFoundError` vira o status “nenhum CSV encontrado”.

> [!warning] “Mais recente” não identifica a sessão
> A busca considera qualquer `*.csv` mais novo em `dados/`, não um caminho devolvido pelo gravador da sessão. Outro processo pode alterar a escolha. Além disso, [[gravador]] grava em `dados/` relativo ao diretório de trabalho, mas a janela busca `dados/` relativo à raiz do projeto; iniciar fora da raiz pode divergir gravação e busca.

### `limpar_grafico()` e `autoescala()`

`limpar_grafico()` chama `buffer.limpar()` e executa `clear()` nas seis curvas. A limpeza descarta o histórico em memória exibido pela interface, mas não para a coleta, não apaga o CSV e não reinicia os contadores da sessão.

> [!tip] Nova janela visual durante a coleta
> Se a aquisição estiver ativa, o buffer volta a receber dados logo após o clique; no próximo tick, aparecem somente as amostras recebidas desde essa limpeza. Com a aquisição parada, as curvas e estatísticas permanecem vazias.

`autoescala()` faz `enableAutoRange(x=False, y=True)` nos dois widgets. X continua fixo; não há método para desligar essa autoescala e restaurar os limites Y iniciais.

## Métodos de atualização

### `atualizar_grafico()`

Retorna quando [[buffers]] está vazio. Caso contrário, faz uma única leitura coerente:

```python
dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)
x = self._x_data[:len(dados['contador'])]
```

O dicionário `curvas` associa checkbox, curva e vetor para os seis eixos. Cada curva marcada recebe `curva.setData(x, np.asarray(y), skipFiniteCheck=True)`; a desmarcada apenas recebe `hide()`. Um snapshot único mantém os eixos alinhados e evita seis leituras concorrentes.

> [!warning] X relativo e finitude
> O X é a posição `0..n-1` da janela recente, não contador, tempo Arduino ou timestamp do PC; por isso reinicia em cada frame e não revela lacunas seriais. `skipFiniteCheck=True` pula a verificação no desenho, embora a conversão serial aceite `nan`/`inf`; [[statistics]] filtra esses valores, mas o comportamento visual fica com PyQtGraph.

### `atualizar_estatisticas()`

Atualiza status por `coletor.rodando`, as três frequências, total de amostras e ocupação do buffer. Em seguida pede outro `snapshot(150)`, calcula estatísticas para cada eixo e escreve média, desvio e RMS. `fmt()` mostra `--` para medidas não finitas.

O snapshot do [[buffers]] usa `Lock`; já os campos escalares do coletor são lidos enquanto a thread serial os atualiza. Assim, um refresh pode combinar valores de instantes ligeiramente diferentes, sem uma leitura transacional única.

### `closeEvent(event)`

Para ambos os timers, chama `manager.parar()` e aceita o evento, seguindo [[threads-e-encerramento]].

> [!warning] Parada sincrona na GUI
> `manager.parar()` aguarda `join()` da coleta e gravação. A serial tem timeout e espera inicial cancelável, mas um bloqueio externo pode manter a interface sem resposta durante o fechamento.

## Relação com serial, buffers e persistência

```text
Arduino → [[serial_reader]] → [[coletor]]
        → [[buffers]] → snapshot(150) → Janela
        → fila limitada → [[gravador_worker]] → [[gravador]] → CSV
```

O histórico visual é curto; [[buffers]] retém até 10.000 amostras por padrão e o CSV segue [[esquema-csv]]. O label “Buffer: … / 10000” está codificado na janela, portanto só permanece correto enquanto a capacidade padrão do buffer for 10.000.

## Código explicado, na ordem do arquivo

### Importações e configuração global (linhas 3–59)

```python
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

`math.isfinite` decide como mostrar metricas invalidas; NumPy cria/converte
vetores; PyQtGraph desenha; PyQt6 fornece widgets, layouts, alinhamento e
timers. [[manager]] e a unica porta de acesso da UI ao pipeline do sensor, e
[[statistics]] recebe cada vetor de eixo. A segunda linha `import pyqtgraph as
pg` (linha 36) e redundante, seguida da configuracao global exata:

```python
pg.setConfigOptions(antialias=False, useOpenGL=True)
```

As constantes seguintes determinam cadencia, janela e faixas iniciais:

```python
INTERVALO_GRAFICO_MS = 33
INTERVALO_ESTATISTICAS_MS = 500
PONTOS_GRAFICO = 150
INTERVALO_EIXO_Y_ACELERAÇÃO = (-40,40)
INTERVALO_EIXO_Y_GIROSCÓPIO = (-50,50)
MOUSE_ATIVADO = False
EIXOS = ("ax", "ay", "az", "gx", "gy", "gz")
CORES = {"ax": "y", "ay": "g", "az": "c", "gx": "r", "gy": "m", "gz": "w"}
```

Nao recebem parametros nem produzem saida por si. `EIXOS`/`CORES` sao
declaracoes de referencia; a implementacao abaixo ainda usa listas e canetas
escritas diretamente.

### Classe `Janela` e `__init__()` (linhas 62–116)

```python
class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Monitor de Vibração")
        self.resize(1300,800)
```

O construtor nao recebe configuracao externa e retorna `None`. Inicializa a
base Qt, conserva a instancia global e fixa propriedades basicas. Em seguida,
declara `None` para ambos os graficos e as seis curvas, criando atributos que
serao preenchidos depois por `criar_grafico`.

```python
self._x_data = np.arange(PONTOS_GRAFICO)
self.criar_interface()
self.criar_timer()
```

`_x_data` e `array([0, ..., 149])` reutilizado. Criar primeiro a UI e so depois
os timers evita callbacks sobre referencias ainda `None`.

### `criar_interface()` (linhas 119–138)

```python
central = QWidget()
self.setCentralWidget(central)
self.layout = QVBoxLayout()
central.setLayout(self.layout)
self.criar_grafico()
self.criar_painel_sinais()
self.criar_painel_estatisticas()
self.criar_barra_botoes()
```

O metodo nao recebe argumentos alem de `self` nem retorna valor. Cria o dono
central exigido pelo `QMainWindow` e ordena verticalmente os quatro blocos. A
ordem das chamadas determina a ordem que o usuario ve.

### `criar_grafico()` (linhas 140–187)

Para aceleracao, o bloco relevante e:

```python
self.grafico_aceleracao = pg.PlotWidget(enableMenu=False)
self.grafico_aceleracao.setBackground("k")
self.grafico_aceleracao.showGrid(x=True, y=True, alpha=0.3)
self.grafico_aceleracao.setLabel("left", "Aceleração (g)")
self.grafico_aceleracao.setLabel("bottom", "Amostras (n)")
self.grafico_aceleracao.setMouseEnabled(x=MOUSE_ATIVADO, y=MOUSE_ATIVADO)
self.grafico_aceleracao.enableAutoRange(x=False, y=False)
self.grafico_aceleracao.setXRange(0, PONTOS_GRAFICO, padding=0)
self.grafico_aceleracao.setYRange(INTERVALO_EIXO_Y_ACELERAÇÃO[0], INTERVALO_EIXO_Y_ACELERAÇÃO[1], padding=0)
```

Depois sao criadas `curva_ax`, `curva_ay` e `curva_az` com `pg.mkPen` amarelo,
verde e ciano. O segundo bloco repete a estrategia para `grafico_giroscopio`,
com label °/s, faixa de giroscopio e curvas `gx`, `gy`, `gz` vermelha, magenta
e branca. Separar os widgets preserva escalas fisicas legiveis. O metodo
somente configura objetos da UI; nao consulta dados.

### `criar_painel_sinais()` (linhas 190–232)

```python
self.checkbox_ax = QCheckBox("ax (amarelo)")
self.checkbox_ax.setChecked(True)
# ... ay, az, gx, gy, gz
layout.addWidget(self.checkbox_ax,0,0)
# ... seis posições de uma QGridLayout
grupo_sinais.setLayout(layout)
self.layout.addWidget(grupo_sinais)
```

Cada checkbox inicia verdadeiro e ocupa duas linhas por tres colunas. Este
metodo apenas constroi controles; nao conecta `toggled`. A decisao de
visibilidade acontece dentro do loop de `atualizar_grafico`, logo nao cria
trabalho extra fora do refresh periodico.

### `criar_painel_estatisticas()` (linhas 235–317)

```python
self.label_status = QLabel("Status: parado")
self.label_hz_medio = QLabel("Hz Médio: 0.00")
self.label_hz_instantaneo = QLabel("Hz Inst: 0.00")
self.label_hz_suavizado = QLabel("Hz Suav: 0.00")
self.label_amostras = QLabel("Amostras: 0")
self.label_buffer = QLabel("Buffer: 0 / 10000")
```

Esses labels recebem estado de sessao. Em seguida o metodo define eixos e
unidades e cria a tabela:

```python
self.eixos = ["ax", "ay", "az", "gx", "gy", "gz"]
self.unidades = {"ax": "g", "ay": "g", "az": "g", "gx": "°/s", "gy": "°/s", "gz": "°/s"}
self.stats_labels = {}
metricas = [("Média", "media"), ("Desvio", "desvio_padrao"), ("RMS", "rms")]
```

O loop pelas `metricas` e pelos eixos cria `QLabel("--")`, armazena cada um em
`stats_labels[(eixo, key)]` e o posiciona na `QGridLayout`. Assim,
`atualizar_estatisticas` localiza uma celula por chave em vez de buscar na
arvore de widgets. O metodo nao calcula estatisticas ainda.

### `criar_barra_botoes()` (linhas 320–359)

```python
self.botao_iniciar.clicked.connect(self.iniciar)
self.botao_parar.clicked.connect(self.parar)
self.botao_limpar.clicked.connect(self.limpar_grafico)
self.botao_auto_escala.clicked.connect(self.autoescala)
```

O sinal `clicked` de cada `QPushButton` registra um slot. Nenhum desses slots
recebe explicitamente o argumento do clique; PyQt invoca os metodos ligados e
suas saidas sao efeitos na sessao ou nas curvas. O layout horizontal e anexado
ao layout principal depois dos demais paineis.

### `criar_timer()` (linhas 362–375)

```python
self.timer_grafico = QTimer()
self.timer_grafico.timeout.connect(self.atualizar_grafico)
self.timer_grafico.start(INTERVALO_GRAFICO_MS)
self.timer_stats = QTimer()
self.timer_stats.timeout.connect(self.atualizar_estatisticas)
self.timer_stats.start(INTERVALO_ESTATISTICAS_MS)
```

Os timers sao atributos para que possam ser parados em `closeEvent`. `timeout`
e o sinal periodico; os dois metodos conectados sao slots sem retorno. Como
ambos vivem no loop Qt, eles nao devem executar operacoes longas.

### `iniciar()` (linhas 378–383)

```python
def iniciar(self):
    self.manager.iniciar()
    self.label_status.setText("Status: rodando")
```

Recebe somente `self`, pede a criacao de fila/threads ao [[manager]] e oferece
feedback imediato. Nao confirma que a serial abriu; no refresh seguinte o
status e corrigido pela flag publica do coletor.

### `parar()` (linhas 386–416)

```python
houve_amostras = self.manager.coletor.numero_amostras > 0
encerrou_aquisicao = self.manager.parar()
self.label_status.setText("Status: Parado")
if not encerrou_aquisicao or not houve_amostras:
    return
```

A condicao impede Plotly se nao havia sessao ou dado. No caminho valido, os
imports locais reduzem o custo na abertura normal e `Path(__file__).parents[1]
forma a pasta de dados. `csv_mais_recente` pode levantar `FileNotFoundError`,
tratado com novo status; caso contrario `plotar_csv(arquivo_csv)` abre a
visualizacao externa. O metodo nao retorna valor para o chamador Qt.

### `atualizar_grafico()` (linhas 420–457)

```python
if self.manager.buffer.vazio():
    return
dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)
```

A primeira condicao poupa um snapshot e redesenho sem amostras. O snapshot
retorna dicionario com `contador` e seis vetores alinhados. O mapa seguinte
reune os pares de interface/dados:

```python
curvas = {
    'ax': (self.checkbox_ax, self.curva_ax, dados['ax']),
    'ay': (self.checkbox_ay, self.curva_ay, dados['ay']),
    'az': (self.checkbox_az, self.curva_az, dados['az']),
    'gx': (self.checkbox_gx, self.curva_gx, dados['gx']),
    'gy': (self.checkbox_gy, self.curva_gy, dados['gy']),
    'gz': (self.checkbox_gz, self.curva_gz, dados['gz']),
}
x = self._x_data[:len(dados['contador'])]
```

Por fim, o loop decide por visibilidade:

```python
for _, (check, curva, y) in curvas.items():
    if check.isChecked():
        curva.show()
        curva.setData(x, np.asarray(y), skipFiniteCheck=True)
    else:
        curva.hide()
```

O loop nao pausa dados ocultos: apenas evita sua renderizacao. `x` tem o mesmo
tamanho dos dados e e relativo a janela; `np.asarray` garante uma entrada
adequada a PyQtGraph.

### `autoescala()` (linhas 459–467)

```python
for grafico in (self.grafico_aceleracao, self.grafico_giroscopio):
    grafico.enableAutoRange(x=False, y=True)
```

O `for` aplica a mesma politica aos dois widgets. X permanece estavel, e Y
passa a ser escolhido pelo PyQtGraph nos redraws futuros. O metodo nao retorna
valor e nao modifica amostras.

### `atualizar_estatisticas()` (linhas 469–518)

```python
if self.manager.coletor.rodando:
    self.label_status.setText("Status: Adquirindo")
else:
    self.label_status.setText("Status: Parado")
```

O primeiro bloco deriva o texto do estado real. Os tres blocos seguintes usam
f-strings com duas casas para `hz_medio`, `hz_inst` e `hz_inst_suavizado`; os
outros dois mostram `numero_amostras` e `tamanho_atual()`.

```python
snap = self.manager.buffer.snapshot(PONTOS_GRAFICO)
def fmt(v):
    return "--" if not math.isfinite(v) else f"{v:.4f}"
for eixo in self.eixos:
    dados = snap[eixo]
    est = calcular_estatisticas(dados)
```

O segundo snapshot e propositalmente unico para esta rodada de estatisticas.
`fmt` e funcao local, recebendo um numero e retornando texto. O `for` recebe a
dataclass de [[statistics]] e preenche tres labels por eixo com unidade. Nao ha
retorno: a saida sao os textos atualizados.

### `limpar_grafico()`

```python
self.manager.buffer.limpar()
self.curva_ax.clear()
self.curva_ay.clear()
self.curva_az.clear()
self.curva_gx.clear()
self.curva_gy.clear()
self.curva_gz.clear()
```

`buffer.limpar()` faz um reset lógico thread-safe: a próxima escrita volta ao
início e não há amostras visíveis até uma nova chegada. As seis chamadas
removem os pontos da tela imediatamente. A função não toca na fila, serial,
CSV ou nos contadores da sessão; se a coleta continuar, `atualizar_grafico`
preenche as curvas com o novo trecho de dados.

### `closeEvent()` (linhas 534–549)

```python
self.timer_grafico.stop()
self.timer_stats.stop()
self.manager.parar()
event.accept()
```

Qt fornece `event`; o metodo primeiro elimina novos timeouts, depois bloqueia
na parada coordenada do [[manager]] e finalmente aceita o fechamento. Nao ha
bloco `if __name__ == "__main__"` neste arquivo: a construcao da aplicacao e
responsabilidade de [[main]].

## Insights para outros projetos

- Atualize desenho e calculos textuais em frequencias diferentes.
- Leia varias series relacionadas em um snapshot atomico.
- Reutilize arrays invariantes no caminho de renderizacao.
- Diferencie controles de apresentacao de controles de aquisicao.
- Guarde o caminho concreto do arquivo produzido pela sessao, nao apenas “o mais recente”.

## Resumo mental

`Janela` consome snapshots recentes: desenha seis sinais, calcula estatisticas mais lentamente e delega captura/persistencia ao [[manager]]. Seus botoes mudam ciclo de vida ou apresentacao; nao alteram protocolo serial nem conteudo do buffer.
#PROJETO_SENSOR_VIBRAÇÃO
