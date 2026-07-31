# utils/statistics.py

**Responsabilidade:** Cálculo de estatísticas descritivas para sinais de vibração (eixo único).  
**Tipo:** Módulo puro (funções + dataclass) - **sem side effects**, **thread-safe**  
**Uso:** `realtime/janela.py` para painel de estatísticas do eixo Ax

---

## Interface Pública

```python
from dataclasses import dataclass
from typing import Iterable
import numpy as np

@dataclass(frozen=True, slots=True)
class EstatisticasBasicas:
    """Resultado imutável das estatísticas de um sinal."""
    quantidade: int                    # n amostras válidas
    amostras_invalidas: int            # NaN/inf descartados
    media: float                       # Média aritmética
    mediana: float                     # Mediana (percentil 50)
    minimo: float                      # Valor mínimo
    maximo: float                      # Valor máximo
    amplitude_pico_a_pico: float       # max - min
    variancia: float                   # ddof=0 (população observada)
    desvio_padrao: float               # sqrt(variância)
    rms: float                         # Root Mean Square
    coeficiente_variacao_percentual: float  # (std/|mean|)*100
    assimetria: float                  # Skewness (momento 3 padronizado)
    curtose_excesso: float             # Kurtosis excess (momento 4 - 3)


def calcular_estatisticas(
    valores: Iterable[float],
    *,
    ddof: int = 0
) -> EstatisticasBasicas:
    """
    Calcula estatísticas básicas para uma sequência de amostras.
    
    Args:
        valores: Valores de um único eixo (ex: snapshot["ax"])
        ddof: Graus de liberdade da variância (0=população, 1=amostral)
    
    Returns:
        EstatisticasBasicas com todos os campos (NaN se indefinido)
    
    Notes:
        - NaN, inf, -inf são filtrados (contados em amostras_invalidas)
        - ddof=0 descreve a janela atual do buffer (população observada)
        - ddof=1 para estimar população maior a partir de amostra
    """
```

---

## Algoritmo (`calcular_estatisticas`)

```
┌─────────────────────────────────────────────────────────────┐
│ calcular_estatisticas(valores, ddof=0)                      │
├─────────────────────────────────────────────────────────────┤
│ 1. np.asarray(list(valores), dtype=float).reshape(-1)      │
│    → Vetor 1D NumPy (aceita list, deque, generator, array) │
│                                                             │
│ 2. mascara_valida = np.isfinite(amostras)                  │
│    validas = amostras[mascara_valida]                      │
│    qtd = validas.size                                       │
│    invalidas = amostras.size - qtd                          │
│    → Filtra NaN/inf (protege contra leitura corrompida)    │
│                                                             │
│ 3. if qtd == 0: return _resultado_indefinido(invalidas)    │
│                                                             │
│ 4. Métricas centrais:                                       │
│    media = mean(validas)                                    │
│    mediana = median(validas)                                │
│    minimo = min(validas)                                    │
│    maximo = max(validas)                                    │
│    amplitude = maximo - minimo                              │
│                                                             │
│ 5. RMS (Root Mean Square) - IMPORTANTE p/ vibração:         │
│    rms = sqrt(mean(validas²))                               │
│    → Intensidade energética do sinal, independente de sinal │
│                                                             │
│ 6. Variância/Desvio (ddof=0 por padrão):                    │
│    if qtd > ddof:                                           │
│        var = var(validas, ddof=ddof)                        │
│        std = sqrt(var)                                      │
│    else: var=std=NaN                                        │
│                                                             │
│ 7. Coef. Variação %:                                        │
│    if std finito e media != 0:                              │
│        cv% = (std / |media|) * 100                          │
│    else: cv% = NaN                                          │
│                                                             │
│ 8. Assimetria (Skewness) e Curtose Excesso:                 │
│    if qtd >= 2 e std > 0:                                   │
│        z = (validas - media) / std                          │
│        assimetria = mean(z³)                                │
│        curtose_excesso = mean(z⁴) - 3                       │
│    else: ambos = NaN                                        │
│                                                             │
│ 9. Return EstatisticasBasicas(...)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Métricas e Interpretação para Vibração

| Métrica | Fórmula | Interpretação em Vibração |
|---------|---------|---------------------------|
| **Média** | `Σx/n` | Offset DC / bias do sensor |
| **RMS** | `√(Σx²/n)` | **Intensidade vibracional** (principal indicador) |
| **Desvio Padrão** | `√(Σ(x-μ)²/n)` | Variabilidade em torno da média |
| **Pico-a-Pico** | `max - min` | Amplitude total do sinal |
| **Coef. Variação %** | `(σ/|μ|)×100` | Variabilidade relativa (sem unidade) |
| **Assimetria** | `E[(x-μ)³/σ³]` | Simetria da distribuição (0 = simétrica) |
| **Curtose Excesso** | `E[(x-μ)⁴/σ⁴] - 3` | "Peso das caudas" (0 = Gaussiana) |

**Por que RMS é crítico:** Representa energia do sinal. Em vibração, `RMS ≈ 0.707 × Pico` para senoide pura. Aumento de RMS = degradação mecânica.

---

## Tratamento de Valores Inválidos

```python
# Qualquer NaN, inf, -inf nas amostras:
mascara_valida = np.isfinite(amostras)
validas = amostras[mascara_valida]
invalidas = amostras.size - validas.size

# Contados em resultado.amostras_invalidas
# Não participam de NENHUM cálculo
```

**Proteção:** Uma única leitura corrompida (ex: serial noise) **não contamina** todas as métricas.

---

## ddof (Delta Degrees of Freedom)

| ddof | Uso | Fórmula Variância |
|------|-----|-------------------|
| **0** (padrão) | **Monitoramento tempo real** - descreve janela observada | `Σ(x-μ)² / n` |
| **1** | Estimativa populacional a partir de amostra | `Σ(x-μ)² / (n-1)` |

**Regra:** Use `ddof=0` (padrão) para dashboard tempo real. Use `ddof=1` apenas para relatórios estatísticos formais.

---

## Uso na UI (`realtime/janela.py`)

```python
# Em atualizar_estatisticas() - chamado a cada 500ms
dados_ax = self.manager.buffer.snapshot(PONTOS_GRAFICO)["ax"]  # 250 pontos
est = calcular_estatisticas(dados_ax)

def fmt(v):
    return "--" if not math.isfinite(v) else f"{v:.4f}"

self.label_media_ax.setText(f"Média Ax: {fmt(est.media)} g")
self.label_desvio_ax.setText(f"Desvio Ax: {fmt(est.desvio_padrao)} g")
self.label_rms_ax.setText(f"RMS Ax: {fmt(est.rms)} g")
```

---

## Performance

| Operação | Tempo (250 amostras) |
|----------|---------------------|
| `np.asarray` + `isfinite` | ~50 µs |
| `mean`, `std`, `median` | ~30 µs |
| `momentos` (skew/kurt) | ~20 µs |
| **Total** | **~100-150 µs** |

**Negligível** vs timer 500ms (0.03% CPU).

---

## Testes

```bash
python -c "
import sys; sys.path.insert(0, '.')
from utils.statistics import calcular_estatisticas
import numpy as np

# Teste básico
dados = np.random.normal(0, 1, 1000)
est = calcular_estatisticas(dados)
print(f'Média: {est.media:.4f} (esperado ~0)')
print(f'Std: {est.desvio_padrao:.4f} (esperado ~1)')
print(f'RMS: {est.rms:.4f} (esperado ~1)')
print(f'Assimetria: {est.assimetria:.4f} (esperado ~0)')
print(f'Curtose exc: {est.curtose_excesso:.4f} (esperado ~0)')

# Teste com NaN
dados_nan = np.array([1,2,np.nan,3,4,np.inf,5])
est2 = calcular_estatisticas(dados_nan)
print(f'Válidas: {est2.quantidade}, Inválidas: {est2.amostras_invalidas}')
print(f'Média: {est2.media:.4f} (esperado 3.0)')
"
```

---

## Dependências

- `numpy` ≥ 2.4.6 (todas as operações vetorizadas)
- `dataclasses` (stdlib Python 3.7+)
- `math` (stdlib - `isfinite`)

---

## Referências Cruzadas

| Arquivo | Linha | Uso |
|---------|-------|-----|
| `realtime/janela.py:21` | `from utils.statistics import calcular_estatisticas` | Import |
| `realtime/janela.py:488` | `est = calcular_estatisticas(dados_ax)` | Called @ 500ms |
| `realtime/janela.py:492` | `fmt(est.media)` | Formatação labels |