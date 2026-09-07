# Dependências Python

As dependências declaradas em `pyproject.toml` são listadas abaixo com os consumidores encontrados no código atual. Esta página descreve o estado observado; não remove dependências.

| Dependência declarada | Uso encontrado | Scripts/módulos | Situação |
|---|---|---|---|
| `numpy` | matriz de amostras, diferenças, finitude e estatísticas | [[statistics]], [[buffers]], [[janela]], [[testar_dados]] | usada |
| `pandas` | leitura tabular de CSV | [[plotar_csv]], [[calibrar_vibracao]] | usada |
| `plotly` | traços e subgráficos interativos | [[plotar_csv]] | usada |
| `pyqt6` | aplicação, janela, timers e widgets | [[main]], [[janela]] | usada |
| `pyqtgraph` | curvas em tempo real | [[janela]], `realtime/gráfico.py` | usada |
| `pyserial` | abertura e leitura da porta serial | [[serial_reader]] | usada |
| `matplotlib` | nenhuma importação no código executável encontrada | — | possivelmente histórica |
| `py` | nenhuma importação no código executável encontrada | — | possivelmente histórica |
| `streamlit` | nenhuma importação no código executável encontrada | — | possivelmente histórica |
| `streamlit-autorefresh` | nenhuma importação no código executável encontrada | — | possivelmente histórica |
| `streamlit-echarts` | nenhuma importação no código executável encontrada | — | possivelmente histórica |

`dados/testar_dados.py` só precisa de NumPy; `grafico/plotar_csv.py` precisa de pandas e Plotly; `calibração/calibrar_vibracao.py` precisa de pandas. A interface ao vivo requer ainda PyQt6, pyqtgraph, NumPy e pyserial por meio do pipeline de aquisição.

As dependências marcadas como possivelmente históricas podem estar associadas a experiências anteriores, documentação ou uso manual fora dos arquivos atuais. Antes de removê-las, procure também ferramentas de desenvolvimento, automações e ambientes dos usuários; a ausência de importação não prova que sejam dispensáveis.

Consulte [[guia-de-modificacao]] ao alterar uma biblioteca ou o modo como os dados são adquiridos e visualizados.
#PROJETO_SENSOR_VIBRAÇÃO
