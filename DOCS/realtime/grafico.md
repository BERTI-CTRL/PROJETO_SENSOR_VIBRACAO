# gráfico.py

`realtime/gráfico.py` é uma interface mínima de diagnóstico para acompanhar somente a aceleração `ax`. Usa o mesmo singleton [[manager]] de [[janela]], porém inicia a aquisição automaticamente e não possui controles, estatísticas nem os outros cinco eixos.

## Resumo, entrada e saída

Execute-o diretamente a partir da raiz do projeto:

```powershell
python realtime\gráfico.py
```

A entrada é `manager.buffer.ax`; a saída é uma única curva amarela. Ao fechar, a janela chama `manager.parar()`, encerrando coleta e gravação conforme [[threads-e-encerramento]].

```text
manager.iniciar()
      ↓
manager.buffer.ax → últimas 500 amostras → curva amarela
      ↓
fechamento → manager.parar()
```

## Dependências e pipeline

- `sys`: argumentos da `QApplication` e código de encerramento.
- `pyqtgraph` e seus adaptadores Qt: gráfico, curva e `QTimer`.
- [[manager]]: singleton também usado pela [[janela]].
- `manager.buffer.ax`: propriedade de compatibilidade de [[buffers]], em ordem cronologica.

Como usa o mesmo manager, abre a mesma porta serial, cria a mesma fila de gravação e gera CSV pela cadeia [[coletor]] → [[gravador_worker]] → [[gravador]]. Não execute junto de `python -m realtime.main`: os processos disputariam a porta serial.

## Classe `Janela`

### `__init__()`

Inicializa `QMainWindow`, define título/tamanho, cria um `PlotWidget` central e a curva:

```python
self.curva = self.grafico.plot(
    pen="y",
    width=2
)
```

Depois configura grade/labels, inicia o pipeline e programa o timer:

```python
manager.iniciar()
self.timer.timeout.connect(self.atualizar)
self.timer.start(16)
```

`16 ms` busca cerca de 60 FPS. A simplicidade reduz custo de composição e é adequada para confirmar rapidamente que `ax` chega ao processo.

### `atualizar()`

Lê o buffer, exige pelo menos dois pontos, mantém no máximo 500 valores e substitui a curva:

```python
dados = manager.buffer
if len(dados.ax) < 2:
    return
ax = list(dados.ax)[-500:]
self.curva.setData(ax)
```

O eixo X é implícito: PyQtGraph usa índices da lista, não tempo/contador do firmware.

> [!warning] Leitura duplicada e custo de cópia
> `dados.ax` é acessado para `len()` e novamente para a lista. Cada acesso passa pela propriedade de compatibilidade de [[buffers]]; entre eles a coleta pode avançar. Além disso, a propriedade pode montar até 10.000 valores antes do corte `[-500:]`. Para diagnóstico rápido isso é aceitável, mas não tem o alinhamento nem a janela limitada de um único `snapshot(500)`.

### `closeEvent(event)`

Chama `manager.parar()` e aceita o evento. A parada aguarda coletor e gravador, usando a mesma sequência segura da aplicação principal.

## Execução no nível do módulo

As linhas finais não usam guarda `if __name__ == "__main__"`:

```python
app = QtWidgets.QApplication(sys.argv)
janela = Janela()
janela.show()
sys.exit(app.exec())
```

> [!danger] Importar abre e bloqueia a GUI
> `import realtime.gráfico` cria uma QApplication, inicia captura, exibe a janela e entra no event loop. Trate este arquivo como script de depuração, não como biblioteca. O acento no nome também torna a importação menos convencional em algumas ferramentas.

## Diferença para a interface principal

| Aspecto | `gráfico.py` | [[janela]] |
|---|---|---|
| Inicio da coleta | automatico no construtor | clique em **Iniciar** |
| Sinais | apenas `ax` | seis eixos |
| Atualizacao | ~60 FPS | ~30 FPS |
| Janela visual | até 500 após ler `ax` | `snapshot(150)` |
| Estatísticas e controles | não | sim |
| Ponto de entrada | efeito no nivel do modulo | [[main]] com guarda |

## Código explicado, na ordem do arquivo

### Importações (linhas 1–10)

```python
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from sensor.manager import manager
```

`sys` fornece argumentos e encerramento. `pg` cria o gráfico; `QtCore` fornece
`QTimer` e `QtWidgets` fornece `QMainWindow`/`QApplication` pela camada Qt do
PyQtGraph. O `manager` importado é a instância global de [[manager]], não uma
nova sessão; por isso esta ferramenta participa do mesmo pipeline de
[[coletor]], [[buffers]] e [[gravador_worker]].

### Classe e construtor (linhas 15–50)

```python
class Janela(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor de Vibração")
        self.resize(1200, 600)
        self.grafico = pg.PlotWidget()
        self.setCentralWidget(self.grafico)
```

A classe não recebe configuração externa: o construtor recebe somente `self` e
retorna `None`. `super().__init__()` inicializa o `QMainWindow`; em seguida, um
único `PlotWidget` se torna seu conteúdo central.

```python
self.curva = self.grafico.plot(
    pen="y",
    width=2
)
self.grafico.showGrid(x=True, y=True)
self.grafico.setLabel("left", "Aceleração (g)")
self.grafico.setLabel("bottom", "Amostras")
```

Esse bloco cria a única saída visual: uma curva amarela de espessura 2 e suas
referencias de unidade. Nao define intervalo Y ou X; o PyQtGraph escolhe a
escala conforme os dados.

```python
manager.iniciar()
self.timer = QtCore.QTimer()
self.timer.timeout.connect(self.atualizar)
self.timer.start(16)
```

`manager.iniciar()` pede a abertura da sessão antes do primeiro redesenho. O
timer pertence à janela e o sinal `timeout` é conectado ao slot
`atualizar`; `start(16)` programa chamadas repetidas no event loop Qt, sem
um `while` na thread da interface.

### Slot `atualizar()` (linhas 52–67)

```python
dados = manager.buffer

if len(dados.ax) < 2:
    return

ax = list(dados.ax)[-500:]
self.curva.setData(ax)
```

O método não recebe argumentos e não retorna valor. `manager.buffer` devolve o
[[buffers]] do coletor. A condição evita desenhar com menos de dois pontos. Se
passar, a propriedade `ax` é convertida em lista, limitada aos 500 últimos
valores e enviada para a curva. `setData` substitui, não acrescenta, os pontos
do frame anterior.

### `closeEvent()` (linhas 69–75)

```python
def closeEvent(self, event):
    manager.parar()
    event.accept()
```

Qt fornece `event`; o método pede o encerramento cooperativo ao manager e
aceita o fechamento. Ele não para explicitamente `self.timer`; com a janela e
o event loop sendo encerrados, o objeto/timer deixam de receber eventos.

### Execução no nível do módulo (linhas 78–85)

```python
app = QtWidgets.QApplication(sys.argv)

janela = Janela()
janela.show()

sys.exit(app.exec())
```

Essas instruções ficam fora de função e de guarda `__main__`. Ao executar como
script, elas criam a aplicação, constroem a janela — que já chama
`manager.iniciar()` — exibem-na e bloqueiam em `app.exec()`. Ao importar o
módulo, o mesmo ocorre, motivo pelo qual ele não é um componente seguro para
reuso programatico.

## Insights para outros projetos

- Ferramentas de diagnóstico podem isolar uma hipótese e um único sinal.
- Declare efeitos colaterais de import mesmo em scripts pequenos.
- Em concorrência, prefira um snapshot limitado e único a propriedades repetidas.
- Não abra um recurso exclusivo, como serial, por dois processos sem compartilhamento explícito.

## Resumo mental

`gráfico.py` é um osciloscópio rápido de `ax`: inicia o pipeline existente, redesenha até 500 pontos e o encerra ao fechar. Para operação normal e análise dos seis sinais, use [[main]] e [[janela]].
#PROJETO_SENSOR_VIBRAÇÃO
