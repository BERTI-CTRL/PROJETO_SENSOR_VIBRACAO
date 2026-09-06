"""Calibra um eixo do acelerômetro usando uma vibração RMS conhecida.

Exemplo mais simples:
    python calibração/calibrar_vibracao.py 0.50

O comando acima usa o CSV mais recente de dados/, o eixo Z e uma referência
de 0,50 g RMS. Para escolher outro arquivo ou eixo:
    python calibração/calibrar_vibracao.py 0.50 dados/teste.csv --eixo ax
"""

# Use este script quando o MPU6050 estiver fixado em uma bancada/máquina cuja
# vibração RMS seja conhecida. Ele calibra somente o eixo excitado; não use
# para giro, impactos sem referência RMS ou dados coletados com o sensor solto.

# argparse lê os valores que o usuário escreve no terminal.
import argparse

# json salva os dois coeficientes calculados para uso futuro.
import json

# Path facilita trabalhar com caminhos de arquivos no Windows.
from pathlib import Path

# pandas lê o CSV gravado pelo projeto.
import pandas as pd


# A pasta do projeto fica um nível acima desta pasta "calibração".
PASTA_PROJETO = Path(__file__).resolve().parent.parent

# Esta é a pasta padrão onde o projeto grava as medições.
PASTA_DADOS = PASTA_PROJETO / "dados"


def ultimo_csv() -> Path:
    """Retorna o CSV mais recente para evitar digitar o caminho no teste rápido."""

    # Procura somente arquivos .csv dentro da pasta dados.
    arquivos = list(PASTA_DADOS.glob("*.csv"))

    # Sem CSV não existe medição para comparar com a referência conhecida.
    if not arquivos:
        raise FileNotFoundError(f"Nenhum CSV encontrado em: {PASTA_DADOS}")

    # O arquivo com maior data de modificação é o último ensaio salvo.
    return max(arquivos, key=lambda arquivo: arquivo.stat().st_mtime)


def rms(valores: pd.Series) -> float:
    """Calcula RMS: a intensidade equivalente de um sinal variável."""

    # Eleva ao quadrado, faz a média e tira a raiz: definição de RMS.
    return float((valores**2).mean() ** 0.5)


def calibrar(referencia_rms_g: float, caminho_csv: str | None, eixo: str, descartar_inicio_s: float) -> Path:
    """Compara a vibração medida no eixo escolhido com a referência conhecida."""

    # Sem caminho informado, o script usa a captura mais recente.
    arquivo_csv = ultimo_csv() if caminho_csv is None else Path(caminho_csv).resolve()

    # Interrompe antes da leitura quando o caminho escolhido não é um arquivo válido.
    if not arquivo_csv.is_file():
        raise FileNotFoundError(f"CSV não encontrado: {arquivo_csv}")

    # Lê todas as linhas do CSV criado por sensor/gravador.py.
    dados = pd.read_csv(arquivo_csv)

    # O eixo, o tempo e o contador são necessários para este cálculo básico.
    colunas = {"tempo_arduino_us", "contador", eixo}
    # Detecta antecipadamente contratos de CSV incompatíveis com a calibração.
    faltantes = colunas - set(dados.columns)
    if faltantes:
        raise ValueError(f"CSV sem as colunas necessárias: {', '.join(sorted(faltantes))}")

    # Converte os valores para números; linhas inválidas viram NaN.
    dados[eixo] = pd.to_numeric(dados[eixo], errors="coerce")
    dados["tempo_arduino_us"] = pd.to_numeric(dados["tempo_arduino_us"], errors="coerce")
    dados["contador"] = pd.to_numeric(dados["contador"], errors="coerce")
    dados = dados.dropna(subset=[eixo, "tempo_arduino_us", "contador"]).copy()

    # Sem números válidos, não existe baseline nem RMS para comparar à referência.
    if dados.empty:
        raise ValueError("O CSV não possui dados numéricos válidos.")

    # O início costuma conter o momento de posicionar o sensor na bancada.
    tempo_s = (dados["tempo_arduino_us"] - dados["tempo_arduino_us"].iloc[0]) / 1_000_000
    dados = dados.loc[tempo_s >= descartar_inicio_s].copy()

    # Impede gerar coeficientes de um recorte temporal que não contém amostras.
    if dados.empty:
        raise ValueError("O descarte inicial removeu todas as amostras.")

    # A média é o baseline: gravidade, inclinação fixa e pequeno offset do sensor.
    offset = float(dados[eixo].mean())

    # Subtrair o baseline deixa somente a parte alternada da vibração.
    vibracao_medida = dados[eixo] - offset

    # Compara RMS com RMS: as duas amplitudes precisam usar a mesma convenção.
    rms_medido = rms(vibracao_medida)

    # Evita divisão por zero quando o eixo não apresenta componente alternado.
    if rms_medido == 0:
        raise ValueError("RMS medido é zero; não é possível calcular o ganho.")

    # Se a referência é maior que a medida, ganho fica maior que 1 e vice-versa.
    ganho = referencia_rms_g / rms_medido

    # Diferença maior que 1 no contador indica uma ou mais amostras ausentes.
    diferencas = dados["contador"].diff().dropna()
    perdidas = int((diferencas[diferencas > 1] - 1).sum())

    # Reúne metadados e coeficientes necessários para reproduzir a análise posterior.
    resultado = {
        "eixo": eixo,
        "unidade": "g",
        "arquivo_csv": str(arquivo_csv),
        "amostras_usadas": int(len(dados)),
        "descarte_inicial_s": descartar_inicio_s,
        "referencia_rms_g": referencia_rms_g,
        "rms_medido_g": rms_medido,
        "offset": offset,
        "ganho": ganho,
        "amostras_perdidas_estimadas": perdidas,
        "formula": "valor_corrigido = ganho * (valor_medido - offset)",
    }

    # Um nome fixo deixa fácil encontrar a calibração mais recente daquele eixo.
    destino = Path(__file__).resolve().parent / f"calibracao_vibracao_{eixo}.json"

    # indent=2 deixa o JSON legível para quem está aprendendo o projeto.
    with destino.open("w", encoding="utf-8") as arquivo_saida:
        json.dump(resultado, arquivo_saida, indent=2, ensure_ascii=False)

    print("\n=== CALIBRAÇÃO POR VIBRAÇÃO CONHECIDA ===")
    print(f"CSV: {arquivo_csv.name}")
    print(f"Eixo: {eixo}")
    print(f"Referência: {referencia_rms_g:.6f} g RMS")
    print(f"RMS medido: {rms_medido:.6f} g")
    print(f"Offset: {offset:+.6f} g")
    print(f"Ganho: {ganho:.6f}")
    print(f"Amostras perdidas estimadas: {perdidas}")
    print(f"JSON salvo em: {destino}")

    return destino


def main() -> None:
    """Monta o comando simples usado no terminal."""

    # Define a descrição exibida pela ajuda da interface de linha de comando.
    parser = argparse.ArgumentParser(
        description="Calibra um eixo do acelerômetro com uma referência em g RMS."
    )
    parser.add_argument("referencia_rms_g", type=float, help="vibração conhecida em g RMS, por exemplo 0.50")
    parser.add_argument("csv", nargs="?", help="CSV do ensaio; se omitido, usa o mais recente")
    parser.add_argument("--eixo", choices=("ax", "ay", "az"), default="az", help="eixo excitado; padrão: az")
    parser.add_argument(
        "--descartar-inicio",
        type=float,
        default=2.0,
        help="segundos iniciais a ignorar; padrão: 2",
    )
    # Converte e valida os argumentos antes de iniciar qualquer leitura ou escrita.
    argumentos = parser.parse_args()

    # A referência RMS precisa ser positiva para que o ganho tenha significado físico.
    if argumentos.referencia_rms_g <= 0:
        raise ValueError("A referência RMS deve ser maior que zero.")
    # Um intervalo de descarte negativo não corresponde a um recorte temporal válido.
    if argumentos.descartar_inicio < 0:
        raise ValueError("O descarte inicial não pode ser negativo.")

    # Executa o cálculo com os parâmetros finais recebidos do terminal.
    calibrar(
        argumentos.referencia_rms_g,
        argumentos.csv,
        argumentos.eixo,
        argumentos.descartar_inicio,
    )


# Permite importar a função calibrar em testes sem executar o terminal inteiro.
if __name__ == "__main__":
    main()
