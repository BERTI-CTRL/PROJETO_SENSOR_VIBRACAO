# statistics.py

## Visão geral

`utils/statistics.py` concentra as estatísticas descritivas de **um único eixo** de vibração. Ele não lê a serial, não altera [[buffers]] e não atualiza widgets: recebe uma sequência numérica e devolve um registro imutável com medidas prontas para consumo.

Na integração atual, [[janela]] chama `calcular_estatisticas` para `ax`, `ay`, `az`, `gx`, `gy` e `gz`, usando um *snapshot* recente de 150 amostras. A função, porém, funciona também para listas, `deque`, arrays NumPy e geradores de qualquer tamanho.

## Papel no projeto

| Entrada | Processamento | Saída |
| --- | --- | --- |
| Valores de apenas um sinal, como `snapshot["ax"]`. | Conversão para vetor, descarte contabilizado de não finitos e cálculo vetorizado. | `EstatisticasBasicas`, com contagens, posição, dispersão, RMS e forma da distribuição. |

O módulo é deliberadamente puro: a mesma entrada e o mesmo `ddof` produzem o mesmo resultado, sem efeitos colaterais. Isso o torna simples de reutilizar em painel, análise offline ou testes.

## Fluxo mental

```text
iterável de um eixo
       │
       ▼
list(valores) → np.asarray(..., float) → vetor 1D
       │
       ▼
np.isfinite
       │
       ├─ nenhum valor finito ───► resultado com contagens e métricas NaN
       │
       ▼
posição e extremos → média, mediana, mínimo, máximo, pico a pico
       │
       ├─► RMS
       ├─► variância e desvio, respeitando ddof
       ├─► coeficiente de variação, se média não for zero
       └─► assimetria e curtose, se houver dispersão
       │
       ▼
EstatisticasBasicas imutável
```

## Interface pública e dependências

```python
from utils.statistics import EstatisticasBasicas, calcular_estatisticas

resultado = calcular_estatisticas(valores, ddof=0)
```

O módulo importa somente `dataclass`, `Iterable` e `numpy`. A exportação explícita abaixo delimita a API pretendida:

```python
__all__ = ["EstatisticasBasicas", "calcular_estatisticas"]
```

`_resultado_indefinido` começa com sublinhado justamente porque é um detalhe interno, usado para criar uma resposta coerente quando não há amostras válidas.

## Código explicado, na ordem do arquivo

### Docstring: responsabilidade e escolha de `ddof`

A docstring abre estabelecendo os limites do módulo: ele não conversa com serial, buffer ou interface. Também diferencia duas leituras de variância:

- `ddof=0` é o padrão e descreve a janela inteira observada agora — apropriado para monitoramento em tempo real;
- `ddof=1` trata a janela como amostra usada para estimar uma população maior.

### `EstatisticasBasicas`: contrato do resultado

```python
@dataclass(frozen=True, slots=True)
class EstatisticasBasicas:
    quantidade: int
    amostras_invalidas: int
    media: float
    mediana: float
    minimo: float
    maximo: float
    amplitude_pico_a_pico: float
    variancia: float
    desvio_padrao: float
    rms: float
    coeficiente_variacao_percentual: float
    assimetria: float
    curtose_excesso: float
```

`@dataclass` evita construir manualmente um objeto para cada atualização. `frozen=True` impede alterar uma estatística pronta; `slots=True` restringe os atributos declarados e reduz overhead por instância.

| Campo | Interpretação |
| --- | --- |
| `quantidade` / `amostras_invalidas` | Valores finitos que entraram no cálculo e valores `nan`, `inf` ou `-inf` descartados. |
| `media` / `mediana` | Nível central; a mediana é mais resistente a picos isolados. |
| `minimo`, `maximo`, `amplitude_pico_a_pico` | Extremos finitos e a distância entre eles (`maximo - minimo`). |
| `variancia`, `desvio_padrao` | Dispersão com o `ddof` solicitado. |
| `rms` | `sqrt(mean(x²))`, intensidade que não se anula quando o sinal alterna entre positivo e negativo. |
| `coeficiente_variacao_percentual` | `desvio_padrao / abs(media) * 100`, somente quando a média permite divisão estável. |
| `assimetria`, `curtose_excesso` | Terceiro e quarto momentos padronizados; normal ideal tem curtose de excesso zero. |

> [!warning] Pico a pico não é pico absoluto
>
> `maximo` é o maior valor assinado e `amplitude_pico_a_pico` é `maximo - minimo`. A API não calcula `max(abs(x))` nem fator de crista (`pico absoluto / RMS`). Eles podem ser úteis para vibração, mas não devem ser inferidos como se já existissem no resultado.

### Validação de `ddof` e conversão do iterável

```python
if ddof < 0:
    raise ValueError("ddof deve ser maior ou igual a zero")

amostras = np.asarray(list(valores), dtype=float).reshape(-1)
```

`ddof` negativo não é aceito. `list(valores)` consome o iterável uma única vez, o que preserva suporte a geradores; `np.asarray(..., dtype=float)` padroniza o tipo e `reshape(-1)` força uma sequência plana. O custo é que uma janela muito grande é materializada antes do cálculo — adequado aos pequenos *snapshots* da interface, mas relevante em análises massivas.

### Valores não finitos são removidos, mas não escondidos

```python
mascara_valida = np.isfinite(amostras)
validas = amostras[mascara_valida]
quantidade = int(validas.size)
amostras_invalidas = int(amostras.size - validas.size)

if quantidade == 0:
    return _resultado_indefinido(amostras_invalidas)
```

Uma leitura inválida não contamina toda a janela com `NaN`: ela é excluída dos cálculos e fica registrada em `amostras_invalidas`. Se nenhum número finito restar, a função retorna imediatamente; as contagens continuam definidas, e todas as métricas ficam como `nan`.

Essa escolha permite que [[janela]] mostre `--` para medidas indisponíveis, sem perder o sinal de que houve entrada corrompida.

### Medidas de posição, extremos e RMS

```python
media = float(np.mean(validas))
mediana = float(np.median(validas))
minimo = float(np.min(validas))
maximo = float(np.max(validas))
amplitude_pico_a_pico = maximo - minimo
rms = float(np.sqrt(np.mean(np.square(validas))))
```

Todas as métricas usam apenas `validas`. Converter cada valor NumPy para `float` nativo melhora a interoperabilidade com formatação, JSON e demais consumidores Python. RMS é especialmente útil em vibração por representar intensidade energética, ao contrário da média, que pode ficar próxima de zero em oscilações simétricas.

### Variância e desvio respeitam graus de liberdade

```python
if quantidade > ddof:
    variancia = float(np.var(validas, ddof=ddof))
    desvio_padrao = float(np.sqrt(variancia))
else:
    variancia = float("nan")
    desvio_padrao = float("nan")
```

NumPy requer mais observações que graus de liberdade. Por isso, com `ddof=1`, uma janela com só uma amostra devolve `nan` em vez de um valor matematicamente enganoso. Com `ddof=0`, uma única amostra tem variância e desvio iguais a zero.

### Dispersão relativa e forma da distribuição

```python
if np.isfinite(desvio_padrao) and not np.isclose(media, 0.0):
    coeficiente_variacao_percentual = float(
        (desvio_padrao / abs(media)) * 100
    )
else:
    coeficiente_variacao_percentual = float("nan")
```

O coeficiente de variação compara dispersão e nível médio, mas se torna instável quando a média é zero ou quase zero — uma situação comum em sinais de vibração centrados. Nesses casos, `nan` é mais honesto que um percentual enorme e pouco interpretável.

```python
if quantidade >= 2 and np.isfinite(desvio_padrao) and desvio_padrao > 0:
    valores_padronizados = (validas - media) / desvio_padrao
    assimetria = float(np.mean(np.power(valores_padronizados, 3)))
    curtose_excesso = float(np.mean(np.power(valores_padronizados, 4)) - 3)
```

Assimetria indica desequilíbrio entre caudas; curtose de excesso indica concentração/caudas comparadas a uma normal. Ambas dependem de desvio positivo: uma janela constante não possui forma distribucional útil, portanto recebe `nan`.

> [!warning] Momentos não são diagnóstico isolado
>
> Em janelas curtas, assimetria e curtose variam bastante. Use-as como pistas junto a RMS, pico a pico, frequência e o gráfico — não como prova independente de falha mecânica.

### Montagem do retorno e `_resultado_indefinido`

A função reúne todos os valores nomeados em `EstatisticasBasicas`. Quando não há finitos, `_resultado_indefinido(amostras_invalidas)` repete um único `float("nan")` em todas as métricas numéricas e mantém `quantidade=0`. Isso estabelece um contrato importante: ausência de medida é representada por `nan`, não por zero.

## Estratégia de uso

```python
from utils.statistics import calcular_estatisticas

est = calcular_estatisticas([1.0, 2.0, float("nan"), 3.0])

assert est.quantidade == 3
assert est.amostras_invalidas == 1
assert est.media == 2.0
assert est.amplitude_pico_a_pico == 2.0
```

Para a interface, capture o snapshot uma vez, calcule uma estrutura por eixo e formate apenas números finitos. Para análise offline de um CSV, primeiro execute [[testar_dados]]: esta função protege métricas individuais, mas não verifica cabeçalho, contador, frequência nem escalas físicas do arquivo completo.

## Insights para outros projetos

- **Separe estatística de transporte e UI.** Uma função pura é mais testável e reutilizável que uma rotina que lê serial e atualiza tela ao mesmo tempo.
- **Não silencie dados inválidos.** Filtrar `NaN` preserva as métricas úteis, e contar descartes preserva a evidência do problema.
- **`ddof` expressa uma decisão analítica.** População observada e amostra estatística não têm o mesmo denominador.
- **`nan` comunica “indefinido”; zero comunica “medido e nulo”.** Misturar esses estados cria interpretações erradas.
- **RMS e média respondem a perguntas diferentes.** Para sinal alternado, RMS representa intensidade; a média pode esconder atividade relevante.

## Resumo mental

`statistics.py` transforma uma janela de um eixo em um retrato estatístico imutável. Ele normaliza a entrada, separa números utilizáveis de dados inválidos, calcula medidas somente quando são matematicamente definidas e devolve `nan` quando não são. [[janela]] usa uma parte do resultado para monitoramento ao vivo; análises mais completas devem combinar essas métricas com [[testar_dados]], [[plotar_csv]] e o contexto físico da medição.
#PROJETO_SENSOR_VIBRAÇÃO
