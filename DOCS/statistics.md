# `utils/statistics.py`

`utils/statistics.py` calcula estatisticas descritivas de um unico sinal sem
ler serial, alterar [[buffers]] ou tocar na interface. A cada 500 ms,
[[janela]] aplica a funcao aos seis eixos de um snapshot recente de 150
amostras e exibe media, desvio padrao e RMS.

## Interface publica

```python
from utils.statistics import EstatisticasBasicas, calcular_estatisticas

resultado = calcular_estatisticas(valores, ddof=0)
```

`EstatisticasBasicas` usa `@dataclass(frozen=True, slots=True)`. `frozen=True`
torna o resultado imutavel depois de construido; `slots=True` fixa os campos e
evita atributos acidentais. O registro contem:

| Campo | Significado |
|---|---|
| `quantidade` | quantidade de valores finitos usados |
| `amostras_invalidas` | quantidade descartada de `nan`, `inf` e `-inf` |
| `media`, `mediana` | medidas de posicao |
| `minimo`, `maximo` | extremos finitos do trecho |
| `amplitude_pico_a_pico` | `maximo - minimo` |
| `variancia`, `desvio_padrao` | dispersao com o `ddof` solicitado |
| `rms` | raiz da media dos quadrados |
| `coeficiente_variacao_percentual` | `desvio / abs(media) * 100` |
| `assimetria` | terceiro momento padronizado |
| `curtose_excesso` | quarto momento padronizado menos 3 |

## Fluxo do calculo

1. `list(valores)` consome uma vez qualquer iteravel, inclusive geradores.
2. `np.asarray(..., dtype=float).reshape(-1)` produz um vetor numerico 1D.
3. `np.isfinite` cria a mascara; somente finitos entram nos calculos, e os
   demais sao contabilizados em `amostras_invalidas`.
4. Se nao restar valor valido, `_resultado_indefinido` devolve contagens
   definidas e `nan` em todos os campos numericos.
5. Media, mediana, minimo, maximo, pico a pico e RMS sao calculados sobre os
   valores validos.
6. Variancia e desvio sao calculados somente quando `quantidade > ddof`.
7. Coeficiente de variacao exige desvio finito e media nao proxima de zero.
8. Assimetria e curtose exigem pelo menos duas amostras e desvio positivo.

Um `ddof` negativo levanta `ValueError`. Com `ddof=0`, o denominador da
variancia descreve toda a janela observada, escolha usada pela UI. Com
`ddof=1`, a variancia amostral exige ao menos duas observacoes. Se a quantidade
nao exceder `ddof`, variancia e desvio ficam indefinidos (`nan`).

## RMS, pico e fator de crista

O RMS implementado e `sqrt(mean(x**2))`; ele resume a magnitude energetica do
sinal sem cancelar valores positivos e negativos. `maximo` e o maior valor
assinado, e `amplitude_pico_a_pico` e a distancia `maximo - minimo`.

A API atual **nao possui** campo de pico absoluto (`max(abs(x))`) nem calcula
fator de crista (`pico absoluto / RMS`). Esses conceitos sao relevantes para
vibracao, mas adiciona-los mudaria a API e o algoritmo; por isso a lacuna foi
somente registrada nesta documentacao.

## Valores indefinidos e exibicao

Resultados matematicamente indisponiveis usam `float("nan")`: entrada sem
finitos, variancia sem graus de liberdade, coeficiente de variacao com media
nula e momentos com desvio nulo. [[janela]] transforma qualquer resultado nao
finito em `--`; as amostras invalidas nao contaminam as demais metricas.

Embora o registro calcule todas as medidas acima, a grade atual mostra apenas
media, desvio padrao e RMS, com `g` para aceleracao e `°/s` para giroscopio. Os
numeros representam as ultimas 150 amostras do tick, nao o historico completo
persistido em [[esquema-csv]].

## Exemplo

```python
est = calcular_estatisticas([1.0, 2.0, float("nan"), 3.0])

assert est.quantidade == 3
assert est.amostras_invalidas == 1
assert est.media == 2.0
assert est.amplitude_pico_a_pico == 2.0
```

## Relacoes

- [[janela]] consome `media`, `desvio_padrao` e `rms` a 2 FPS.
- [[buffers]] fornece os arrays copiados e cronologicos usados como entrada.
- [[coletor]] alimenta o buffer com os seis sinais medidos.
