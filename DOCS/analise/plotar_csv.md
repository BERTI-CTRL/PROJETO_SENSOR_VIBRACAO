# plotar_csv.py — explicação completa, em ordem de linhas

O arquivo [grafico/plotar_csv.py](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\grafico\plotar_csv.py) lê uma captura CSV já salva e abre dois gráficos interativos no navegador: aceleração no primeiro painel e giroscópio no segundo.

Ele não lê o Arduino e não altera o CSV. É uma ferramenta de análise posterior. A janela também o chama quando você clica em **Parar**, depois que manager termina o gravador.

```text
Clique em Parar na janela
          ↓
manager encerra Coletor e GravadorWorker
          ↓
GravadorCSV fecha o CSV
          ↓
Janela chama plotar_csv(arquivo)
          ↓
Plotly abre o navegador
```

| Termo | Significado simples |
|---|---|
| CSV | Tabela de texto com colunas separadas por vírgula. |
| pandas | Biblioteca que lê a tabela em um DataFrame. |
| DataFrame | Tabela pandas: linhas são amostras, colunas têm nomes. |
| Plotly | Biblioteca que cria gráficos interativos no navegador. |
| trace | Uma curva adicionada a uma figura Plotly. |
| subplot | Um painel dentro de uma mesma figura. |
| Path | Objeto que representa um caminho de arquivo. |
| argumento | Informação opcional passada pelo terminal. |

## Linhas 1 a 18: docstring e imports

```python
"""Plota um arquivo CSV de sensores usando Plotly.

Uso pelo terminal:
    python grafico/plotar_csv.py
    python grafico/plotar_csv.py caminho/para/arquivo.csv
"""
import argparse
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
```

A docstring explica dois modos de uso pelo terminal. Sem caminho, o script procura o arquivo CSV mais recente. Com caminho, usa aquele arquivo específico.

argparse interpreta argumentos digitados no terminal. Path trata caminhos. pandas, com apelido pd, lê CSV. plotly.graph_objects, com apelido go, fornece Scatter para curvas. make_subplots cria uma figura com mais de um painel.

## Linhas 20 a 28: localizar o projeto e definir os eixos

```python
PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "dados"
COLUNAS_ACELERACAO = ("ax", "ay", "az")
COLUNAS_GIRO = ("gx", "gy", "gz")
```

__file__ é o caminho deste próprio script. resolve o transforma em caminho absoluto. parent sobe um diretório:

```text
.../PROJETO_SENSOR_VIBRACAO/grafico/plotar_csv.py
                              ↑ parent: grafico
                    ↑ parent.parent: PROJETO_SENSOR_VIBRACAO
```

O operador / entre Paths forma o caminho dados. Isso é preferível a concatenar barras manualmente.

As duas tuplas agrupam as três colunas de aceleração e as três do giroscópio. Elas permitem criar as seis curvas com dois loops.

## Linhas 31 a 39: escolher o CSV mais recente

```python
def csv_mais_recente(pasta: Path = PASTA_DADOS) -> Path:
    arquivos = list(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo CSV encontrado em: {pasta}"
        )
    return max(
        arquivos,
        key=lambda arquivo: arquivo.stat().st_mtime
    )
```

csv_mais_recente recebe uma pasta; se ninguém passar uma, usa PASTA_DADOS. A anotação -> Path diz que o retorno esperado é um caminho.

glob("*.csv") encontra somente arquivos cujo nome termina em .csv. list materializa o resultado para permitir verificar e escolher o maior.

```python
if not arquivos:
```

Uma lista vazia é falsa em Python. not a transforma em verdadeira quando não existem CSVs. raise interrompe a função e informa claramente o motivo.

max escolhe o maior conforme key. lambda é uma função pequena. arquivo.stat().st_mtime é a data/hora da última modificação do arquivo. Portanto, o retorno é o CSV modificado mais recentemente.

## Linhas 42 a 56: receber e validar o caminho

```python
def plotar_csv(caminho: str | Path | None = None) -> None:
```

A função aceita três tipos:

- str, por exemplo dados/teste.csv;
- Path, um caminho já criado em Python;
- None, que significa “procure o CSV mais recente”.

-> None informa que a função não devolve dado: seu resultado é abrir a figura.

```python
arquivo = csv_mais_recente() if caminho is None else Path(caminho)
arquivo = arquivo.resolve()
if not arquivo.is_file():
    raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
```

A primeira linha é uma expressão condicional. Se caminho for None, chama csv_mais_recente. Caso contrário, transforma caminho em Path.

resolve transforma um caminho relativo em absoluto. Por exemplo, dados/teste.csv passa a apontar para o local completo a partir do diretório atual do terminal.

is_file verifica se o caminho existe e é um arquivo, não uma pasta. Se falhar, FileNotFoundError aparece antes de pandas tentar carregar algo inválido.

## Linhas 58 a 68: ler a tabela e exigir as colunas

```python
dados = pd.read_csv(arquivo)
coluna_x = "contador"
colunas_necessarias = {
    coluna_x,
    *COLUNAS_ACELERACAO,
    *COLUNAS_GIRO,
}
colunas_faltantes = colunas_necessarias - set(dados.columns)
```

read_csv lê cabeçalho e linhas, devolvendo um DataFrame. dados.columns contém os nomes de coluna lidos.

O asterisco em *COLUNAS_ACELERACAO expande a tupla dentro do conjunto:

```python
{"contador", "ax", "ay", "az", "gx", "gy", "gz"}
```

A subtração de conjuntos encontra nomes obrigatórios que não aparecem no CSV.

```python
if colunas_faltantes:
    faltantes = ", ".join(sorted(colunas_faltantes))
    raise ValueError(f"Colunas ausentes no CSV: {faltantes}")
```

Se há qualquer coluna faltante, sorted as coloca em ordem estável e join cria um texto separado por vírgulas. ValueError interrompe antes de tentar acessar uma coluna inexistente.

O programa valida só as colunas necessárias para desenhar. Ele não verifica aqui se há NaN, se o contador possui saltos ou se os valores são fisicamente plausíveis.

## Linhas 70 a 78: criar os dois painéis

```python
figura = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.12,
    subplot_titles=("Aceleração", "Giroscópio"),
)
```

rows=2 e cols=1 criam dois painéis um acima do outro. shared_xaxes=True faz ambos compartilharem o eixo horizontal: zoom e deslocamento horizontais ficam alinhados. vertical_spacing controla o espaço entre painéis. subplot_titles define os títulos internos.

A separação é importante porque aceleração usa g e giroscópio usa graus por segundo. Uma escala compartilhada poderia esconder variações menores de um dos grupos.

## Linhas 80 a 104: adicionar as seis curvas

```python
for eixo in COLUNAS_ACELERACAO:
    figura.add_trace(
        go.Scatter(
            x=dados[coluna_x],
            y=dados[eixo],
            mode="lines",
            name=eixo.upper(),
        ),
        row=1,
        col=1,
    )
```

O loop ocorre três vezes: eixo vale ax, depois ay e depois az.

dados[coluna_x] seleciona a coluna contador e fornece X. dados[eixo] seleciona a coluna atual e fornece Y. Scatter cria uma série Plotly. mode="lines" desenha linhas sem marcadores. upper transforma ax em AX para a legenda. add_trace coloca a curva na linha 1, coluna 1, isto é, no painel superior.

```python
for eixo in COLUNAS_GIRO:
    figura.add_trace(
        go.Scatter(
            x=dados[coluna_x],
            y=dados[eixo],
            mode="lines",
            name=eixo.upper(),
        ),
        row=2,
        col=1,
    )
```

O segundo loop é igual, mas percorre gx, gy e gz e adiciona ao segundo painel.

O eixo X é contador, não tempo em segundos. Isso mostra ordem e pode tornar lacunas de contador visíveis, mas a distância horizontal não deve ser interpretada como duração física exata.

## Linhas 106 a 121: aparência, mensagens e navegador

```python
figura.update_yaxes(
    title_text="Aceleração (g)",
    row=1,
    col=1,
)
figura.update_yaxes(
    title_text="Velocidade angular (°/s)",
    row=2,
    col=1,
)
figura.update_xaxes(title_text="Amostra", row=2, col=1)
```

As duas primeiras linhas nomeiam cada eixo Y e deixam explícitas suas unidades. update_xaxes nomeia o eixo X no painel inferior; como X é compartilhado, um rótulo basta.

```python
figura.update_layout(
    title=f"Dados do sensor — {arquivo.name}",
    template="plotly_white",
    hovermode="x unified",
    height=1200,
)
```

arquivo.name usa somente o nome final do arquivo no título. plotly_white escolhe visual claro. hovermode="x unified" faz o cursor mostrar, em uma única caixa, valores das várias curvas na mesma posição X. height define uma figura alta o bastante para dois painéis.

```python
print(f"Plotando: {arquivo}")
print(f"Amostras: {len(dados)}")
figura.show()
```

Os dois prints informam no terminal o caminho absoluto e a quantidade de linhas do DataFrame. len(dados) conta linhas, isto é, amostras. show abre a figura interativa no navegador padrão.

## Linhas 124 a 138: uso pelo terminal

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plota um CSV do sensor com Plotly."
    )
    parser.add_argument(
        "caminho",
        nargs="?",
        help="caminho do CSV; se omitido, usa o CSV mais recente da pasta dados",
    )
    argumentos = parser.parse_args()
    plotar_csv(argumentos.caminho)
```

main adapta argumentos do terminal para a função principal. ArgumentParser define a ajuda. add_argument cria o argumento posicional caminho.

nargs="?" faz caminho ser opcional. Se omitido, argumentos.caminho vale None e plotar_csv busca o CSV mais recente. Se fornecido, vale o texto digitado.

```python
if __name__ == "__main__":
    main()
```

Esse bloco só roda ao executar o arquivo diretamente. Quando Janela importa csv_mais_recente e plotar_csv após clicar em Parar, main não executa e nenhum argumento do terminal é analisado.

## Relação com o botão Parar

Na janela, o fluxo relevante é:

```python
houve_amostras = self.manager.coletor.numero_amostras > 0
encerrou_aquisicao = self.manager.parar()
if not encerrou_aquisicao or not houve_amostras:
    return

arquivo_csv = csv_mais_recente(pasta_dados)
plotar_csv(arquivo_csv)
```

manager.parar espera o Coletor terminar, envia None ao GravadorWorker e espera o CSV ser fechado. Só depois Janela procura o arquivo mais recente e o entrega a plotar_csv.

## Resumo mental

plotar_csv é a lupa do ensaio salvo. Ele encontra ou recebe um CSV, verifica colunas, carrega tudo com pandas, monta dois painéis Plotly e abre uma análise interativa no navegador.
