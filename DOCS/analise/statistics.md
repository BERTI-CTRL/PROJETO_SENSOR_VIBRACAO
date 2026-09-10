# statistics.py — explicação completa, em ordem de linhas

O arquivo [utils/statistics.py](C:\Users\berti\Documents\FACULDADE\projeto_sensor_vibracao\PROJETO_SENSOR_VIBRACAO\utils\statistics.py) calcula estatísticas descritivas para **um eixo por vez**. Ele recebe uma sequência numérica, como as últimas amostras de ax, e devolve um objeto com média, RMS, desvio padrão e outras medidas.

Ele não abre serial, não altera BufferSensores e não desenha a tela. Janela chama essa função para cada eixo do snapshot recente.

```text
BufferSensores.snapshot(150)
          ↓
ax, ay, az, gx, gy, gz
          ↓
calcular_estatisticas(um eixo)
          ↓
EstatisticasBasicas
          ↓
Janela mostra média, desvio e RMS
```

| Termo | Significado simples |
|---|---|
| média | Soma dos valores dividida pela quantidade. |
| mediana | Valor central após ordenar os dados. |
| variância | Medida de espalhamento em torno da média. |
| desvio padrão | Raiz quadrada da variância. |
| RMS | Raiz da média dos quadrados; mede intensidade de sinal alternado. |
| NaN | Número indefinido, “not a number”. |
| infinito | Valor maior que qualquer número finito. |
| ddof | Ajuste do denominador da variância. |
| dataclass | Forma prática de criar uma estrutura de dados nomeada. |

## Linhas 1 a 35: responsabilidade, imports e API pública

A docstring inicial explica que o módulo recebe uma sequência de um sinal e devolve medidas. Ela também define ddof=0 como padrão para descrever a janela atual do buffer.

```python
from dataclasses import dataclass
from typing import Iterable
import numpy as np

__all__ = ["EstatisticasBasicas", "calcular_estatisticas"]
```

dataclass cria automaticamente o construtor do resultado. Iterable aceita listas, tuplas, deques, arrays NumPy e geradores. NumPy executa cálculos numéricos vetorizados.

__all__ declara os dois nomes pensados como públicos. _resultado_indefinido não aparece nessa lista porque é um auxiliar interno.

## Linhas 38 a 61: a estrutura de resultado

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

@dataclass faz Python criar um objeto com esses campos e nomes.

frozen=True torna o resultado imutável depois de criado. Por exemplo, tentar alterar est.media gera erro. slots=True reduz memória e impede adicionar atributos inventados.

| Campo | Significado |
|---|---|
| quantidade | Quantidade de valores finitos usados. |
| amostras_invalidas | Quantidade de NaN, inf e -inf descartados. |
| media e mediana | Duas medidas de centro. |
| minimo e maximo | Extremos assinados. |
| amplitude_pico_a_pico | maximo menos minimo. |
| variancia e desvio_padrao | Dispersão. |
| rms | Intensidade quadrática média. |
| coeficiente_variacao_percentual | Dispersão relativa à média. |
| assimetria e curtose_excesso | Forma da distribuição. |

## Linhas 66 a 89: assinatura e validação de ddof

```python
def calcular_estatisticas(
    valores: Iterable[float],
    *,
    ddof: int = 0,
) -> EstatisticasBasicas:
```

valores é uma sequência de um único eixo. O asterisco significa que ddof só pode ser passado por nome:

```python
calcular_estatisticas(valores, ddof=1)
```

O retorno é um objeto EstatisticasBasicas.

```python
if ddof < 0:
    raise ValueError("ddof deve ser maior ou igual a zero")
```

ddof negativo não representa a variância aceita pela função, então ValueError interrompe antes dos cálculos.

## Linhas 91 a 105: conversão e limpeza de dados inválidos

```python
amostras = np.asarray(list(valores), dtype=float).reshape(-1)
```

list consome o iterável uma vez. np.asarray o transforma em array de floats. reshape(-1) garante uma sequência plana, mesmo se a entrada tiver forma diferente.

```python
mascara_valida = np.isfinite(amostras)
validas = amostras[mascara_valida]
quantidade = int(validas.size)
amostras_invalidas = int(amostras.size - validas.size)
```

isfinite produz uma máscara booleana: True para valores normais e False para NaN, inf e -inf. Usar a máscara como índice seleciona somente valores válidos.

quantidade conta os valores usados. amostras_invalidas conta os removidos. Assim um dado corrompido não transforma toda a estatística em NaN, mas continua registrado.

```python
if quantidade == 0:
    return _resultado_indefinido(amostras_invalidas)
```

Sem nenhum número finito, não há média, RMS ou extremos possíveis. A função retorna cedo com métricas NaN e a contagem de inválidos preservada.

## Linhas 107 a 118: centro, extremos e RMS

```python
media = float(np.mean(validas))
mediana = float(np.median(validas))
minimo = float(np.min(validas))
maximo = float(np.max(validas))
amplitude_pico_a_pico = maximo - minimo
```

mean calcula média. median encontra o centro após ordenar. min e max encontram extremos. Pico a pico mede a distância entre os extremos.

```python
rms = float(np.sqrt(np.mean(np.square(validas))))
```

O cálculo de RMS segue três etapas:

```text
valores → quadrado de cada valor → média dos quadrados → raiz quadrada
```

Para uma oscilação simétrica, a média pode ser próxima de zero, mas RMS continua mostrando a intensidade.

## Linhas 120 a 127: variância e desvio padrão

```python
if quantidade > ddof:
    variancia = float(np.var(validas, ddof=ddof))
    desvio_padrao = float(np.sqrt(variancia))
else:
    variancia = float("nan")
    desvio_padrao = float("nan")
```

Com ddof=0, uma amostra já basta para variância zero. Com ddof=1, é preciso pelo menos duas amostras. Se a matemática não permite a medida, NaN comunica “indefinida”; não confunda isso com zero.

## Linhas 129 a 136: coeficiente de variação

```python
if np.isfinite(desvio_padrao) and not np.isclose(media, 0.0):
    coeficiente_variacao_percentual = float(
        (desvio_padrao / abs(media)) * 100
    )
else:
    coeficiente_variacao_percentual = float("nan")
```

Esse percentual compara o tamanho do desvio à magnitude da média. abs evita um percentual negativo quando a média é negativa. Se média é zero ou quase zero, a divisão seria instável e a função devolve NaN.

Em vibração centrada em zero, esse coeficiente pode ser indefinido mesmo que RMS e desvio sejam úteis.

## Linhas 138 a 146: assimetria e curtose

```python
if quantidade >= 2 and np.isfinite(desvio_padrao) and desvio_padrao > 0:
    valores_padronizados = (validas - media) / desvio_padrao
    assimetria = float(np.mean(np.power(valores_padronizados, 3)))
    curtose_excesso = float(
        np.mean(np.power(valores_padronizados, 4)) - 3
    )
else:
    assimetria = float("nan")
    curtose_excesso = float("nan")
```

Padronizar subtrai a média e divide pelo desvio. A terceira potência forma assimetria; a quarta potência, menos três, forma excesso de curtose. Uma distribuição normal ideal tem curtose_excesso igual a zero.

Se a série é constante, desvio padrão é zero; não existe forma padronizada útil, por isso ambas recebem NaN.

## Linhas 148 a 163: montar o retorno

```python
return EstatisticasBasicas(
    quantidade=quantidade,
    amostras_invalidas=amostras_invalidas,
    media=media,
    mediana=mediana,
    minimo=minimo,
    maximo=maximo,
    amplitude_pico_a_pico=amplitude_pico_a_pico,
    variancia=variancia,
    desvio_padrao=desvio_padrao,
    rms=rms,
    coeficiente_variacao_percentual=coeficiente_variacao_percentual,
    assimetria=assimetria,
    curtose_excesso=curtose_excesso,
)
```

Essa chamada cria um registro imutável com todos os resultados calculados. A janela lê três campos:

```python
est.media
est.desvio_padrao
est.rms
```

Os outros campos ficam disponíveis para análises, relatórios ou futuras telas.

## Linhas 166 a 185: resultado sem valores válidos

```python
def _resultado_indefinido(
    amostras_invalidas: int,
) -> EstatisticasBasicas:
    nan = float("nan")
    return EstatisticasBasicas(
        quantidade=0,
        amostras_invalidas=amostras_invalidas,
        media=nan,
        mediana=nan,
        minimo=nan,
        maximo=nan,
        amplitude_pico_a_pico=nan,
        variancia=nan,
        desvio_padrao=nan,
        rms=nan,
        coeficiente_variacao_percentual=nan,
        assimetria=nan,
        curtose_excesso=nan,
    )
```

O nome começa com _, indicando método interno. nan é criado uma vez e preenchido em todos os campos numéricos. As duas contagens continuam úteis:

```python
quantidade = 0
amostras_invalidas = quantidade_de_dados_descartados
```

## Como Janela usa esse módulo

```python
snap = self.manager.buffer.snapshot(PONTOS_GRAFICO)
for eixo in self.eixos:
    dados = snap[eixo]
    est = calcular_estatisticas(dados)
    # atualiza média, desvio e RMS
```

O snapshot contém as últimas 150 amostras de todos os eixos. O loop chama a função seis vezes, uma para cada série. Isso não altera o snapshot, o buffer ou a coleta.

## Exemplo simples

```python
est = calcular_estatisticas([1.0, 2.0, float("nan"), 3.0])

est.quantidade            # 3
est.amostras_invalidas    # 1
est.media                 # 2.0
est.amplitude_pico_a_pico # 2.0
```

## Resumo mental

statistics.py transforma uma série numérica em um retrato estatístico. Ele converte a entrada, separa valores utilizáveis de NaN/infinito, calcula medidas quando são matematicamente possíveis e usa NaN quando a medida é indefinida. A janela usa média, desvio e RMS para monitorar os seis sinais.
