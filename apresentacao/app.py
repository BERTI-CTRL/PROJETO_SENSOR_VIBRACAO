"""Apresentação pública do experimento de vibração no pórtico."""

from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PASTA = Path(__file__).resolve().parent
COR_ROXO = "#54247E"
COR_GRAFITE = "#21252B"
COR_LILAS = "#F3EEF8"
COR_PETROLEO = "#167C80"


def analisar_ensaio(caminho: Path, eixo: str) -> dict:
    """Lê uma aceleração, calcula métricas e encontra seu pico espectral."""
    dados = pd.read_csv(caminho)
    obrigatorias = {"tempo_arduino_us", eixo}
    faltantes = obrigatorias - set(dados.columns)
    if faltantes:
        raise ValueError(f"CSV sem as colunas necessárias: {', '.join(sorted(faltantes))}")

    tempo_us = pd.to_numeric(dados["tempo_arduino_us"], errors="coerce").to_numpy()
    sinal = pd.to_numeric(dados[eixo], errors="coerce").to_numpy()
    mascara = np.isfinite(tempo_us) & np.isfinite(sinal)
    tempo_us, sinal = tempo_us[mascara], sinal[mascara]
    intervalos_s = np.diff(tempo_us) / 1_000_000
    if np.any(intervalos_s <= 0):
        raise ValueError("A coluna de tempo precisa ter incremento positivo em todas as amostras.")
    if len(sinal) < 8:
        raise ValueError("São necessárias ao menos 8 amostras válidas para análise.")

    duracao_s = float((tempo_us[-1] - tempo_us[0]) / 1_000_000)
    if duracao_s <= 0:
        raise ValueError("A duração do ensaio precisa ser positiva.")
    taxa_hz = float((len(sinal) - 1) / duracao_s)
    tempo_s = (tempo_us - tempo_us[0]) / 1_000_000

    # Remove tendência linear antes da janela de Hann para evitar que a componente
    # contínua apareça como frequência física dominante.
    tendencia = np.polyval(np.polyfit(tempo_s, sinal, 1), tempo_s)
    sinal_centrado = sinal - tendencia
    espectro = np.abs(np.fft.rfft(sinal_centrado * np.hanning(len(sinal))))
    frequencias = np.fft.rfftfreq(len(sinal), d=float(np.median(intervalos_s)))
    if len(espectro) < 2:
        raise ValueError("Não foi possível calcular o espectro de frequência.")
    indice_pico = int(np.argmax(espectro[1:]) + 1)

    return {
        "tempo_s": tempo_s,
        "sinal_g": sinal,
        "frequencias_hz": frequencias,
        "magnitude": espectro,
        "amostras": int(len(sinal)),
        "duracao_s": duracao_s,
        "frequencia_aquisicao_hz": taxa_hz,
        "frequencia_dominante_hz": float(frequencias[indice_pico]),
        "indice_pico": indice_pico,
    }


def rotulo_frequencia(pico_calculado_hz: float, referencia_poster_hz: float | None = None) -> str:
    """Distingue o pico calculado da referência divulgada no pôster."""
    pico = f"{pico_calculado_hz:.2f}".replace(".", ",")
    if referencia_poster_hz is None:
        return f"Frequência dominante calculada: {pico} Hz."
    referencia = f"{referencia_poster_hz:.2f}".replace(".", ",")
    return (
        f"Frequência dominante apresentada: ≈ {referencia} Hz. "
        f"Pico calculado nesta visualização: {pico} Hz."
    )


def carregar_manifesto() -> list[dict]:
    """Carrega o manifesto em YAML compatível com JSON, sem dependência extra."""
    caminho = PASTA / "data" / "manifesto_ensaios.yaml"
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError as erro:
        raise RuntimeError("Manifesto dos ensaios não encontrado.") from erro
    ensaios = conteudo.get("ensaios", [])
    if not ensaios:
        raise RuntimeError("O manifesto não contém ensaios públicos.")
    return ensaios


def reduzir(x: np.ndarray, y: np.ndarray, maximo: int = 2500) -> tuple[np.ndarray, np.ndarray]:
    """Mantém gráficos responsivos sem alterar a análise completa."""
    passo = max(1, int(np.ceil(len(x) / maximo)))
    return x[::passo], y[::passo]


def figura_temporal(resultado: dict, eixo: str) -> go.Figure:
    tempo, sinal = reduzir(resultado["tempo_s"], resultado["sinal_g"])
    figura = go.Figure(go.Scatter(x=tempo, y=sinal, mode="lines", line={"color": COR_ROXO, "width": 1.7}))
    figura.update_layout(
        template="plotly_white", height=320, margin={"l": 8, "r": 8, "t": 32, "b": 8},
        title="Resposta temporal", xaxis_title="Tempo (s)", yaxis_title=f"Aceleração {eixo.upper()} (g)",
        paper_bgcolor="white", plot_bgcolor="white", font={"color": COR_GRAFITE},
    )
    figura.update_xaxes(showgrid=True, gridcolor="#E8E1EE")
    figura.update_yaxes(showgrid=True, gridcolor="#E8E1EE")
    return figura


def figura_espectro(resultado: dict) -> go.Figure:
    fim = min(12.0, float(resultado["frequencias_hz"][-1]))
    mascara = (resultado["frequencias_hz"] > 0) & (resultado["frequencias_hz"] <= fim)
    frequencias, magnitude = resultado["frequencias_hz"][mascara], resultado["magnitude"][mascara]
    pico = resultado["frequencia_dominante_hz"]
    figura = go.Figure(go.Scatter(x=frequencias, y=magnitude, mode="lines", line={"color": COR_PETROLEO, "width": 2}))
    figura.add_vline(x=pico, line_color=COR_ROXO, line_width=2)
    figura.add_annotation(x=pico, y=float(np.max(magnitude)), text=f"Pico calculado<br>{pico:.2f} Hz", showarrow=True, arrowcolor=COR_ROXO, font={"color": COR_ROXO})
    figura.update_layout(
        template="plotly_white", height=320, margin={"l": 8, "r": 8, "t": 32, "b": 8},
        title="Espectro de frequência", xaxis_title="Frequência (Hz)", yaxis_title="Magnitude relativa",
        paper_bgcolor="white", plot_bgcolor="white", font={"color": COR_GRAFITE},
    )
    figura.update_xaxes(range=[0, fim], showgrid=True, gridcolor="#E8E1EE")
    figura.update_yaxes(showgrid=True, gridcolor="#E8E1EE")
    return figura


def aplicar_estilo() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: #FFFFFF; color: {COR_GRAFITE}; }}
        .block-container {{ max-width: 1120px; padding-top: 1.5rem; padding-bottom: 2rem; }}
        h1, h2, h3 {{ color: {COR_GRAFITE}; letter-spacing: -0.025em; }}
        h2 {{ border-bottom: 2px solid {COR_ROXO}; padding-bottom: .35rem; margin-top: 2.2rem; }}
        .hero {{ background: linear-gradient(135deg, #ffffff 0%, #f4eff8 100%); border-left: 7px solid {COR_ROXO}; border-radius: 18px; padding: 2rem; margin-bottom: 1.5rem; }}
        .eyebrow {{ color: {COR_PETROLEO}; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; font-size: .78rem; }}
        .flow {{ display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; margin: 1rem 0; }}
        .node {{ background:{COR_LILAS}; color:{COR_ROXO}; font-weight:700; padding:.65rem .85rem; border-radius:10px; }}
        .arrow {{ color:{COR_PETROLEO}; font-size:1.3rem; font-weight:800; }}
        .note {{ background:#F7F4FA; border:1px solid #E4DAEC; border-radius:12px; padding:1rem 1.1rem; }}
        .metric-card {{ background:{COR_LILAS}; border-radius:12px; padding:.75rem; text-align:center; }}
        [data-testid="stMetric"] {{ background:{COR_LILAS}; border-radius:12px; padding:.8rem 1rem; }}
        [data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] div {{ color:{COR_GRAFITE} !important; }}
        .ensaio-table {{ width:100%; border-collapse:separate; border-spacing:0; overflow:hidden; border:1px solid #E4DAEC; border-radius:12px; margin:.7rem 0 1.25rem; font-size:.93rem; }}
        .ensaio-table th {{ background:{COR_ROXO}; color:white; padding:.7rem; text-align:left; }}
        .ensaio-table td {{ color:{COR_GRAFITE}; padding:.7rem; border-bottom:1px solid #EDE8F1; vertical-align:top; }}
        .ensaio-table tr:nth-child(even) td {{ background:#FAF8FC; }}
        @media(max-width: 640px) {{ .ensaio-table {{ font-size:.78rem; }} .ensaio-table th, .ensaio-table td {{ padding:.45rem; }} }}
        [data-testid="stImage"] {{ background:#F7F4FA; border:1px solid #E4DAEC; border-radius:18px; margin-top:.75rem; padding:.75rem; overflow:hidden; }}
        [data-testid="stImage"] img {{ border-radius:12px; display:block; object-fit:contain; }}
        [data-testid="stImage"] + div {{ padding-top:.2rem; }}
        .footer {{ border-top:2px solid {COR_ROXO}; margin-top:2.5rem; padding-top:1rem; color:#5E6470; font-size:.9rem; }}
        @media(max-width: 640px) {{ .block-container {{ padding-left: 1rem; padding-right: 1rem; }} .hero {{ padding:1.25rem; }} .arrow {{ transform:rotate(90deg); }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Vibração no pórtico | UNIFAL-MG", page_icon="〰️", layout="wide")
    aplicar_estilo()
    foto = PASTA / "assets" / "foto_portico.png"

    coluna_texto, coluna_foto = st.columns([1.25, 0.75], vertical_alignment="center")
    with coluna_texto:
        st.markdown("<div class='hero'><div class='eyebrow'>XII SIEPE · UNIFAL-MG</div><h1>Análise experimental de frequências de vibração em pórtico com MPU-6050</h1><p><strong>Mateus Almeida Berti</strong><br>Orientadores: Prof. Laos Hirano e Prof. Davidson França<br>UNIFAL-MG | Engenharia Civil</p><p>Uma investigação inicial sobre como instrumentação acessível pode revelar a resposta vibratória de uma estrutura.</p></div>", unsafe_allow_html=True)
    with coluna_foto:
        if foto.exists():
            st.image(str(foto), caption="Pórtico experimental instrumentado com MPU-6050.", width="stretch")

    st.subheader("Como funciona")
    st.markdown("<div class='flow'><span class='node'>Pórtico instrumentado</span><span class='arrow'>→</span><span class='node'>MPU-6050</span><span class='arrow'>→</span><span class='node'>Arduino</span><span class='arrow'>→</span><span class='node'>CSV</span><span class='arrow'>→</span><span class='node'>Processamento</span><span class='arrow'>→</span><span class='node'>Frequência predominante</span></div>", unsafe_allow_html=True)
    st.write("O sensor mede acelerações durante a oscilação; o Arduino registra a sequência temporal em CSV, que é analisada para localizar o pico de frequência do sinal transversal.")

    st.subheader("Ensaios controlados")
    ensaios = carregar_manifesto()
    st.write("Foram incluídos apenas os arquivos com correspondência explícita à tabela de ensaios. Arquivos de calibração, comunicação, depuração ou correspondência ambígua não aparecem aqui.")
    linhas_tabela = "".join(
        f"<tr><td>{escape(item['nome'])}</td><td>{escape(item['massa'])}</td><td>{escape(item['arquivo'])}</td><td>{escape(item['observacoes'])}</td></tr>"
        for item in ensaios
    )
    st.markdown(f"<table class='ensaio-table'><thead><tr><th>Ensaio</th><th>Massa</th><th>CSV</th><th>Observação</th></tr></thead><tbody>{linhas_tabela}</tbody></table>", unsafe_allow_html=True)

    st.subheader("Dados experimentais")
    rotulos = {item["nome"]: item for item in ensaios}
    escolhido = st.selectbox("Selecione um ensaio controlado", list(rotulos))
    ensaio = rotulos[escolhido]
    caminho_csv = PASTA / "data" / "csv" / ensaio["arquivo"]
    try:
        resultado = analisar_ensaio(caminho_csv, ensaio.get("eixo_transversal", "ay"))
    except (OSError, ValueError) as erro:
        st.error(f"Não foi possível analisar este ensaio: {erro}")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("Duração", f"{resultado['duracao_s']:.2f} s")
    m2.metric("Amostras", f"{resultado['amostras']:,}".replace(",", "."))
    m3.metric("Aquisição média", f"{resultado['frequencia_aquisicao_hz']:.1f} Hz")
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(figura_temporal(resultado, ensaio.get("eixo_transversal", "ay")), width="stretch")
    with g2:
        st.plotly_chart(figura_espectro(resultado), width="stretch")
    referencia_poster = ensaio.get("frequencia_poster_hz")
    texto_pico = rotulo_frequencia(resultado["frequencia_dominante_hz"], referencia_poster)
    st.markdown(f"<div class='note'><strong>{texto_pico}</strong> Sinal transversal ({ensaio.get('eixo_transversal', 'ay').upper()}).</div>", unsafe_allow_html=True)
    #if referencia_poster is not None:
        #st.caption("A diferença de 0,01 Hz decorre da resolução da FFT neste registro; o valor divulgado no pôster é 2,02 Hz.")

    st.subheader("Interpretação")
    st.write("Os resultados experimentais apresentam coerência com a solução analítica de referência. Esta é uma investigação em fase inicial: o foco atual é identificar frequências. A estimativa confiável de amplitudes pequenas ainda está em investigação e uma frequência isolada não comprova saúde estrutural.")

    st.subheader("Visualização do fenômeno")
    video = PASTA / "assets" / "videos" / "sensor_vibracao_horizontal.mp4"
    if video.exists():
        st.video(str(video))
        st.caption("A animação mostra o caminho da vibração estrutural até o registro e a interpretação do sinal experimental.")

    st.subheader("Próximos passos")
    st.markdown("- Calibração do sistema de medição\n- Ensaios de repetibilidade\n- Avaliação de sensibilidade\n- Estimativa de amplitudes pequenas\n- Comparação com instrumentos de referência")

    url_publica = os.getenv("PUBLIC_APP_URL", "").strip()
    qr = PASTA / "assets" / "qrcode_apresentacao.png"
    if url_publica and qr.exists():
        st.image(str(qr), width=180, caption="Acesse a apresentação pelo QR code.")

    st.markdown("<div class='footer'><strong>Mateus Almeida Berti</strong> · Prof. Laos Hirano · Prof. Davidson França · UNIFAL-MG<br>Referências: TDK InvenSense (2013); Farrar & Worden (2007); Rao (2007).<br>Os dados exibidos são de ensaios experimentais controlados.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
