import streamlit as st


st.set_page_config(page_title="Projeto Sensor Vibração",page_icon=":bar_chart:",layout="wide", height=800)

st.title("Projeto Acelerômetro/Giroscópio")

#sidebar --> páginas

Tab_df_acelerometro, Tab_df_giro, Tab_graf_acelerometro, Tab_graf_giro = st.tabs([
    "Dataframe Acelerômetro",
    "Dataframe Giroscópio",
    "Grafico Acelerômetro",
    "Grafico Giroscópio"
])

with Tab_df_acelerometro:

    df_acelerometro = pd.DataFrame({
        "Aceleração em X",
        "Aceleração em Y",
        "Aceleração em Z",
        "Escala",
        "Resolução",
        "Frequência",
        "status"
    })

    df_acelerometro = st.data_editor(
        [
            ["Aceleração em y"]
        ]
    )

with Tab_df_giro:

with Tab_graf_acelerometro:

with Tab_graf_giro: