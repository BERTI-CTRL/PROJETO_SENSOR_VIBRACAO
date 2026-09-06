# `grafico/plotar_csv.py`

**Responsabilidade:** abrir um gráfico Plotly interativo para analisar com calma os dados já salvos em CSV conforme [[esquema-csv]].

O script não acessa a porta serial e não altera os CSVs. Ele lê um arquivo existente e abre o resultado no navegador.

> **Importante:** ele lê o CSV inteiro. Já a janela PyQt mostra somente as últimas 150 amostras. Portanto, um pico que já saiu da janela pode aparecer no Plotly; isso não significa que o Plotly criou um novo valor.

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

O layout tem altura de 1200 px para que os dois painéis tenham espaço para zoom e inspeção.

## Formato esperado do CSV

O arquivo gerado por `sensor/gravador.py` possui estas colunas:

```text
tempo_arduino_us, tempo_relogio_pc, contador, ax, ay, az, gx, gy, gz
```

O script valida se `contador` e os seis eixos estão presentes antes de criar o gráfico. Ele encontra o CSV padrão pela data de modificação, resolve qualquer caminho informado em relação ao terminal e interrompe com erro se o resultado não for um arquivo.

`tempo_arduino_us` e `tempo_relogio_pc` não formam o eixo visual: o contador deixa lacunas e ordem explícitas, inclusive quando a discussão de taxa e perdas em [[tempo-frequencia-e-perdas]] indicar uma anomalia.

## Dependências

- `pandas`
- `plotly`

Ambas já estão declaradas em `pyproject.toml`.

## Relação com validação e calibração

Rode [[testar_dados]] antes quando a continuidade e as faixas físicas importarem para a conclusão do ensaio. O gráfico pode desenhar um CSV que passou apenas na verificação mínima de colunas; ele não rejeita saltos, `NaN` ou dados fora da faixa por conta própria.

Para ensaios de vibração com referência conhecida, [[calibrar_vibracao]] produz coeficientes em JSON sem modificar a captura. O Plotly continua exibindo os valores originais do CSV.
