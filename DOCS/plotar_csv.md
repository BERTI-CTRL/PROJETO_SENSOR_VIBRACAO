# `grafico/plotar_csv.py`

**Responsabilidade:** abrir um gráfico Plotly interativo para analisar com calma os dados já salvos em CSV.

O script não acessa a porta serial e não altera os CSVs. Ele lê um arquivo existente e abre o resultado no navegador.

## Uso

```powershell
# Usa automaticamente o CSV mais recente da pasta dados/
python grafico\plotar_csv.py

# Usa um arquivo escolhido
python grafico\plotar_csv.py dados\dados_aceleracao_giro-2026-08-04_16-17-40.csv
```

Também pode ser usado por outro script Python:

```python
from grafico.plotar_csv import plotar_csv

plotar_csv()                    # CSV mais recente
plotar_csv("dados/arquivo.csv") # caminho escolhido
```

## Gráfico criado

O eixo X é a coluna `contador`, que mantém a ordem das amostras. O Plotly cria dois painéis com zoom, arraste, tooltip e possibilidade de ocultar curvas pela legenda:

| Painel | Sinais | Unidade |
|---|---|---|
| Aceleração | `ax`, `ay`, `az` | `g` |
| Giroscópio | `gx`, `gy`, `gz` | `°/s` |

Os sinais são separados para que valores do giroscópio não diminuam visualmente as variações da aceleração.

## Formato esperado do CSV

O arquivo gerado por `sensor/gravador.py` possui estas colunas:

```text
tempo_arduino_us, tempo_relogio_pc, contador, ax, ay, az, gx, gy, gz
```

O script valida se `contador` e os seis eixos estão presentes antes de criar o gráfico.

## Dependências

- `pandas`
- `plotly`

Ambas já estão declaradas em `pyproject.toml`.
