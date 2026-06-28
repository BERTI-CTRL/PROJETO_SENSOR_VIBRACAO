import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

from sensor.manager import manager

# =====================================================
# Configuração
# =====================================================

st.set_page_config(
    page_title="Teste de Desempenho",
    layout="wide"
)

st.title("Teste de Desempenho - Sensor MPU6050")

# Atualiza a página a cada 100 ms (10 FPS)
st_autorefresh(interval=50, key="refresh")

# =====================================================
# Botões
# =====================================================

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Iniciar aquisição"):
        manager.iniciar()

with col2:
    if st.button("⏹ Parar aquisição"):
        manager.parar()

# =====================================================
# Buffer
# =====================================================

dados = manager.buffer

st.write(f"Quantidade de amostras: {len(dados.ax)}")

# =====================================================
# Gráfico
# =====================================================

if len(dados.ax) > 10:

    df = pd.DataFrame(
        {
            "Tempo": list(dados.timestamp),
            "AX": list(dados.ax),
        }
    )

    st.line_chart(
        df,
        x="Tempo",
        y="AX",
        use_container_width=True
    )

st.write(f"ID do manager: {id(manager)}")