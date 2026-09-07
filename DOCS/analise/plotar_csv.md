# plotar_csv.py

> [!abstract] Em uma frase
> Lê uma captura CSV e abre no navegador dois gráficos Plotly interativos: aceleração e giroscópio.

## Papel no projeto

`grafico/plotar_csv.py` pertence à análise posterior. Ele não abre serial, não cria threads e não modifica o CSV: lê o histórico produzido por [[gravador]] e o apresenta de modo explorável. Ao encerrar uma sessão com dados, [[janela]] importa e chama `plotar_csv()`; o mesmo arquivo também pode ser chamado diretamente no terminal.

```text
[[gravador]] → CSV em dados/ → plotar_csv.py → navegador
                                      ↑
                         chamada opcional de [[janela]]
```

## Entrada e saída

| Item | Contrato real |
|---|---|
| Entrada | Caminho opcional (`str`, `Path` ou `None`). Sem caminho, procura o CSV mais recente. |
| Colunas exigidas | `contador`, `ax`, `ay`, `az`, `gx`, `gy`, `gz`; o contrato maior está em [[esquema-csv]]. |
| Saída | Figura Plotly no navegador e mensagens com caminho e número de amostras. |
| Efeito persistente | Nenhum; o arquivo é somente lido. |

## Dependências

| Biblioteca | Por que aparece aqui |
|---|---|
| `argparse` | Aceita um caminho opcional no terminal. |
| `pathlib.Path` | Localiza a raiz, lista candidatos e resolve caminhos. |
| `pandas` | Converte o CSV em `DataFrame` com colunas nomeadas. |
| `plotly.graph_objects` | Cria cada curva `Scatter`. |
| `plotly.subplots` | Separa aceleração e giro em painéis com X compartilhado. |

## Código explicado, na ordem do arquivo

### Importações, raiz e canais

```python
import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "dados"
COLUNAS_ACELERACAO = ("ax", "ay", "az")
COLUNAS_GIRO = ("gx", "gy", "gz")
```

`Path(__file__).resolve()` encontra este script independentemente de onde o terminal foi aberto. Os dois `.parent` sobem de `grafico/plotar_csv.py` até a raiz; o operador `/` monta `dados/` sem concatenar strings.

`pandas` será usado para `pd.read_csv()`: o resultado é um `DataFrame`, tabela com nomes de coluna. As tuplas agrupam sinais por unidade física e permitem criar as seis curvas com dois loops, em vez de repetir código. Elas precisam acompanhar os nomes produzidos por [[gravador]].

### `csv_mais_recente()`

```python
def csv_mais_recente(pasta: Path = PASTA_DADOS) -> Path:
    arquivos = list(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em: {pasta}")
    return max(arquivos, key=lambda arquivo: arquivo.stat().st_mtime)
```

O *type hint* informa que recebe e devolve `Path`. `.glob("*.csv")` cria candidatos; `list(...)` os materializa para `max()`. A `lambda` é uma função curta usada como chave: `arquivo.stat().st_mtime` é a data de modificação. O retorno é, portanto, o CSV modificado por último.

> [!warning] “Mais recente” não significa “da sessão atual”
> Qualquer CSV mais novo na pasta vence a comparação. Se outro processo escrever na mesma pasta, o padrão sem argumento pode abrir uma captura diferente da esperada.

### Escolha e validação do caminho

```python
def plotar_csv(caminho: str | Path | None = None) -> None:
    arquivo = csv_mais_recente() if caminho is None else Path(caminho)
    arquivo = arquivo.resolve()
    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
```

`str | Path | None` documenta os três usos permitidos. A expressão condicional usa o mais recente apenas para `None`; um caminho informado vira `Path`. `.resolve()` transforma caminho relativo em absoluto a partir do terminal, e `.is_file()` rejeita diretórios ou caminhos inexistentes antes da leitura.

### Leitura e contrato mínimo

```python
dados = pd.read_csv(arquivo)
coluna_x = "contador"
colunas_necessarias = {coluna_x, *COLUNAS_ACELERACAO, *COLUNAS_GIRO}
colunas_faltantes = colunas_necessarias - set(dados.columns)

if colunas_faltantes:
    faltantes = ", ".join(sorted(colunas_faltantes))
    raise ValueError(f"Colunas ausentes no CSV: {faltantes}")
```

`pd.read_csv()` interpreta o cabeçalho e carrega as colunas. `{...}` cria um conjunto; `*COLUNAS_ACELERACAO` e `*COLUNAS_GIRO` expandem as tuplas. A subtração encontra nomes obrigatórios ausentes. `sorted()` estabiliza a mensagem e `join()` a torna legível.

> [!warning] Visualizar não é validar
> O contrato aqui é suficiente para desenhar. Ele não confere ordem completa, saltos, `NaN`, infinito nem limites físicos. Use [[testar_dados]] antes de concluir que um ensaio é consistente.

### Dois painéis e seis curvas

```python
figura = make_subplots(
    rows=2, cols=1, shared_xaxes=True,
    vertical_spacing=0.12,
    subplot_titles=("Aceleração", "Giroscópio"),
)
```

`make_subplots()` retorna uma `Figure` única com dois painéis. `shared_xaxes=True` mantém zoom e navegação horizontais alinhados. A separação é importante: `g` e `°/s` têm escalas e significado diferentes.

```python
for eixo in COLUNAS_ACELERACAO:
    figura.add_trace(
        go.Scatter(
            x=dados[coluna_x], y=dados[eixo],
            mode="lines", name=eixo.upper(),
        ),
        row=1, col=1,
    )
```

O `for` percorre `ax`, `ay` e `az`. Em cada volta, `dados[coluna_x]` fornece X e `dados[eixo]` fornece Y; `Scatter(..., mode="lines")` cria linha e `eixo.upper()` cria legenda. O segundo loop do arquivo repete a mesma estratégia com `COLUNAS_GIRO`, em `row=2`.

> [!tip] Estratégia reutilizável
> Agrupar canais em tuplas e percorrê-los reduz duplicação e mantém uma regra visual consistente. É útil para telemetria, sensores biomédicos e séries financeiras.

### Layout e abertura

```python
figura.update_yaxes(title_text="Aceleração (g)", row=1, col=1)
figura.update_yaxes(title_text="Velocidade angular (°/s)", row=2, col=1)
figura.update_xaxes(title_text="Amostra", row=2, col=1)
figura.update_layout(
    title=f"Dados do sensor — {arquivo.name}",
    template="plotly_white",
    hovermode="x unified",
    height=1200,
)
figura.show()
```

Os rótulos preservam as unidades. A *f-string* mostra somente `arquivo.name` no título. `hovermode="x unified"` reúne valores das curvas na mesma amostra em um único tooltip; `height=1200` dá espaço aos painéis. `figura.show()` abre a figura interativa no navegador padrão.

> [!warning] Escala de dados
> O script carrega o CSV inteiro em memória. Capturas grandes podem demorar. O eixo X é `contador`, não tempo: lacunas aparecem visualmente, mas distância horizontal não é duração em segundos.

### Terminal e guarda de execução

```python
parser = argparse.ArgumentParser(description="Plota um CSV do sensor com Plotly.")
parser.add_argument("caminho", nargs="?", help="caminho do CSV; se omitido, usa o CSV mais recente da pasta dados")
argumentos = parser.parse_args()
plotar_csv(argumentos.caminho)

if __name__ == "__main__":
    main()
```

`nargs="?"` torna o argumento posicional opcional: sem ele, `argumentos.caminho` é `None`. `main()` adapta a CLI e delega o trabalho à função reutilizável. A guarda `__main__` impede que o parser execute quando [[janela]] importa `csv_mais_recente` e `plotar_csv` ao terminar uma sessão.

## Estratégias usadas

> [!tip] Separar aquisição de análise
> A visualização pesada roda depois da captura. Isso preserva CPU e responsividade do caminho de aquisição em tempo real.

> [!tip] Validar antes de usar uma biblioteca complexa
> Checar colunas antes de Plotly gera uma mensagem de domínio compreensível, em vez de uma falha interna difícil de diagnosticar.

## Insights para outros projetos

- Use `Path(__file__).resolve()` para localizar recursos do projeto.
- Compare conjuntos para validar colunas obrigatórias.
- Use subgráficos quando séries têm unidades diferentes.
- Separe a função reutilizável do parser de linha de comando.

## Resumo mental

`plotar_csv.py` é a **lupa da sessão gravada**: recebe ou encontra um CSV, verifica as colunas necessárias, carrega tudo em `DataFrame` e abre aceleração e giro em Plotly. Para julgar se a captura é confiável antes de interpretá-la, consulte [[testar_dados]].
#PROJETO_SENSOR_VIBRAÇÃO
