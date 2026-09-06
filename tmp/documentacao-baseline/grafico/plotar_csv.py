"""Plota um arquivo CSV de sensores usando Plotly.

Uso pelo terminal:

    python grafico/plotar_csv.py
    python grafico/plotar_csv.py caminho/para/arquivo.csv

Sem informar um caminho, o script usa o CSV mais recente da pasta dados.
So para analsiar com mais calma
"""

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# A pasta do projeto: .../PROJETO_SENSOR_VIBRACAO
PASTA_PROJETO = Path(__file__).resolve().parent.parent

# Pasta padrão onde o gravador salva os arquivos.
PASTA_DADOS = PASTA_PROJETO / "dados"

# Colunas esperadas pelo gravador do projeto.
COLUNAS_ACELERACAO = ("ax", "ay", "az")
COLUNAS_GIRO = ("gx", "gy", "gz")


def csv_mais_recente(pasta: Path = PASTA_DADOS) -> Path:
    """Retorna o CSV modificado mais recentemente na pasta informada."""

    arquivos = list(pasta.glob("*.csv"))

    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em: {pasta}")

    return max(arquivos, key=lambda arquivo: arquivo.stat().st_mtime)


def plotar_csv(caminho: str | Path | None = None) -> None:
    """Lê um CSV e abre seu gráfico interativo no navegador.

    Args:
        caminho: caminho do CSV. Se for None, usa o CSV mais recente.
    """

    # Quando nenhum caminho é recebido, escolhemos o último CSV salvo.
    arquivo = csv_mais_recente() if caminho is None else Path(caminho)

    # Permite informar um caminho relativo ao diretório atual do terminal.
    arquivo = arquivo.resolve()

    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    # O gravador usa vírgula como separador e a primeira linha como cabeçalho.
    dados = pd.read_csv(arquivo)

    # O contador é usado como eixo X porque representa a ordem das amostras.
    coluna_x = "contador"
    colunas_necessarias = {coluna_x, *COLUNAS_ACELERACAO, *COLUNAS_GIRO}
    colunas_faltantes = colunas_necessarias - set(dados.columns)

    if colunas_faltantes:
        faltantes = ", ".join(sorted(colunas_faltantes))
        raise ValueError(f"Colunas ausentes no CSV: {faltantes}")

    # Cria dois painéis para que a escala do giroscópio não esconda
    # as variações menores dos sinais de aceleração.
    figura = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Aceleração", "Giroscópio"),
    )

    # Adiciona os três eixos de aceleração no primeiro painel.
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

    # Adiciona os três eixos do giroscópio no segundo painel.
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

    # Define títulos, unidades e uma legenda comum aos dois painéis.
    figura.update_yaxes(title_text="Aceleração (g)", row=1, col=1)
    figura.update_yaxes(title_text="Velocidade angular (°/s)", row=2, col=1)
    figura.update_xaxes(title_text="Amostra", row=2, col=1)
    figura.update_layout(
        title=f"Dados do sensor — {arquivo.name}",
        template="plotly_white",
        hovermode="x unified",
        height=1200,
    )

    print(f"Plotando: {arquivo}")
    print(f"Amostras: {len(dados)}")

    # Abre o gráfico interativo no navegador padrão.
    figura.show()


def main() -> None:
    """Lê o caminho opcional informado no terminal e plota o CSV."""

    parser = argparse.ArgumentParser(description="Plota um CSV do sensor com Plotly.")
    parser.add_argument(
        "caminho",
        nargs="?",
        help="caminho do CSV; se omitido, usa o CSV mais recente da pasta dados",
    )
    argumentos = parser.parse_args()
    plotar_csv(argumentos.caminho)


if __name__ == "__main__":
    main()
