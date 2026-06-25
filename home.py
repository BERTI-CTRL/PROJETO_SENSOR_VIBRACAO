import streamlit as st

import streamlit.components.v1 as components

st.set_page_config(
    page_title="LAPSE - Sistema de Vibração",
    page_icon="📈",
    layout="wide"
)


# CSs


st.markdown("""
<style>

[data-testid="stAppViewContainer"]{
    background: linear-gradient(
        135deg,
        #0f172a 0%,
        #111827 40%,
        #1e293b 100%
    );
}

.hero{
    text-align:center;
    padding-top:40px;
    padding-bottom:50px;
}

.hero-title{
    font-size:4rem;
    font-weight:800;
    background: linear-gradient(
        90deg,
        #38bdf8,
        #06b6d4,
        #22c55e
    );
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.hero-sub{
    font-size:1.3rem;
    color:#cbd5e1;
    margin-top:20px;
}

.card{
    background:rgba(255,255,255,0.05);
    border-radius:20px;
    padding:25px;
    text-align:center;
    backdrop-filter: blur(12px);
    border:1px solid rgba(255,255,255,0.1);
    transition:0.3s;
    min-height:180px;
}

.card:hover{
    transform:translateY(-8px);
    box-shadow:0px 10px 25px rgba(0,255,255,0.2);
}

.footer{
    text-align:center;
    color:#94a3b8;
    margin-top:60px;
    padding-bottom:20px;
}

.section-title{
    text-align:center;
    font-size:2rem;
    margin-bottom:30px;
    font-weight:bold;
}

.flow{
    background:rgba(255,255,255,0.05);
    padding:30px;
    border-radius:20px;
    border:1px solid rgba(255,255,255,0.1);
}

.logo-box{
    border:2px dashed #38bdf8;
    border-radius:20px;
    padding:30px;
    display:inline-block;
    margin-bottom:30px;
    color:#94a3b8;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# HERO
# =====================================================

st.markdown("""
<div class="hero">

<div class="logo-box">
<h2>LOGO LAPSE</h2>
<p>Substitua por sua imagem</p>
</div>

<div class="hero-title">
Sistema Inteligente de Monitoramento de Vibração
</div>

<div class="hero-sub">
Integração entre MPU6050, Arduino, Python, Streamlit e Inteligência Artificial
</div>

</div>
""", unsafe_allow_html=True)




st.divider()

#grafico animaddo
#################################################################

col1,col2,col3 = st.columns([2.5,5,1])
with col2:
    st.image("assets/senoide.gif")


st.divider()



# =====================================================
# NAVEGAÇÃO
# =====================================================

st.markdown(
    "<div class='section-title'>📂 Navegação</div>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:

    st.subheader("📚 Documentação")

    st.write("""
    - MPU6050
    - Comunicação Serial
    - Metodologia
    - Limitações
    """)

    if st.button(
        "Abrir Documentação",
        key="doc",
        use_container_width=True
    ):
        st.switch_page("pages/1_Fundamentos.py")

with col2:

    st.subheader("🧪 Laboratório")

    st.write("""
    - Dados em tempo real
    - Gráficos
    - Estatísticas
    - FFT
    """)

    if st.button(
        "Abrir Laboratório",
        key="lab",
        use_container_width=True
    ):
        st.switch_page("pages/2_Dados.py")

with col3:

    st.subheader("ℹ️ Sobre")

    st.write("""
    - GitHub
    - Tecnologias
    - Licença
    - Contato
    """)

    if st.button(
        "Abrir Sobre",
        key="sobre",
        use_container_width=True
    ):
        st.switch_page("pages/3_Sobre.py")







st.divider()






















# =====================================================
# MÉTRICAS
# =====================================================

st.markdown("## 📊 Tecnologias Utilizadas")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Sensor", "MPU6050")

with m2:
    st.metric("Backend", "Python & C++")

with m3:
    st.metric("Aquisição", "Tempo Real")

with m4:
    st.metric("Dashboard", "Streamlit")

st.divider()

# =====================================================
# FUNCIONALIDADES
# =====================================================

st.markdown(
    "<div class='section-title'>🚀 Funcionalidades</div>",
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="card">
        <h3>📡 Aquisição de Dados</h3>
        <p>
        Leitura contínua dos dados do acelerômetro e giroscópio
        através da comunicação serial com Arduino.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card">
        <h3>📈 Dashboard em Tempo Real</h3>
        <p>
        Visualização instantânea dos sinais de vibração
        com gráficos atualizados continuamente.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card">
        <h3>💾 Armazenamento</h3>
        <p>
        Registro automático dos dados em arquivos CSV
        para análise posterior.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.write("")

c4, c5, c6 = st.columns(3)

with c4:
    st.markdown("""
    <div class="card">
        <h3>📊 Análise Estatística</h3>
        <p>
        Cálculo de médias, máximos, mínimos,
        desvios padrão e indicadores.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown("""
    <div class="card">
        <h3>🧠 Inteligência Artificial</h3>
        <p>
        Futuro suporte para classificação,
        detecção de anomalias e reconhecimento
        de padrões.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown("""
    <div class="card">
        <h3>🎮 Aplicações Interativas</h3>
        <p>
        Integração com jogos e interfaces
        controladas por movimento.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =====================================================
# ARQUITETURA
# =====================================================

st.markdown(
    "<div class='section-title'>⚙️ Arquitetura do Sistema</div>",
    unsafe_allow_html=True
)

col1,col2,col3 = st.columns([12,10,10])

with col2:
    components.html("""
    <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true });
    </script>

    <div class="mermaid">
    graph TD

    A[📡 MPU6050] --> B[🔌 Arduino]
    B --> C[📶 Serial]
    C --> D[🐍 Python]

    D --> E[📈 Dashboard]
    D --> F[📊 Estatísticas]
    D --> G[💾 CSV]

    E --> H[🧠 Análise]                
    F --> H[🧠 Análise]
    G --> H[🧠 Análise]
    </div>
    """, height=500)




st.divider()

























# =====================================================
# SOBRE O PROJETO
# =====================================================

st.markdown(
    "<div class='section-title'>🎯 Objetivo do Projeto</div>",
    unsafe_allow_html=True
)

st.markdown("""
Este projeto tem como objetivo desenvolver uma plataforma para
aquisição, visualização e análise de sinais de vibração utilizando
o sensor **MPU6050**, um **Arduino** e ferramentas desenvolvidas em
**Python**.

O sistema permite:

- Aquisição de dados em tempo real;
- Armazenamento em arquivos CSV;
- Visualização gráfica dos sinais;
- Cálculo de estatísticas descritivas;
- Análise de frequência (FFT);
- Desenvolvimento futuro de modelos de Inteligência Artificial.

A plataforma foi concebida para aplicações acadêmicas,
experimentais e educacionais, servindo como base para estudos
de instrumentação, processamento de sinais e monitoramento de vibrações.
""")

st.divider()

# =====================================================
# RODAPÉ
# =====================================================

st.markdown("""
<div class="footer">

<h3>LAPSE</h3>

Laboratório de Automação e Processamento de Sinais

<br><br>

Sistema de Monitoramento e Análise de Vibração

<br>

MPU6050 • Arduino • Python • Streamlit

<br><br>

Versão 0.1

</div>
""", unsafe_allow_html=True)