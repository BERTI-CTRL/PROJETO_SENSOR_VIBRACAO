# Script de Teste de Dados - `dados/testar_dados.py`

**Localização:** `dados/testar_dados.py`  
**Finalidade:** Validação automatizada de consistência dos CSVs gerados pelo sensor MPU6050.

---

## Uso

```bash
# Pega o CSV mais recente em dados/ (padrão)
python dados/testar_dados.py

# Especifica arquivo manualmente
python dados/testar_dados.py dados/dados_aceleracao_giro-2026-08-01_12-22-42.csv

# Com venv ativado (recomendado)
.\.venv\Scripts\python dados/testar_dados.py [arquivo]
```

---

## O que o script verifica

| # | Teste | Descrição |
|---|-------|-----------|
| **1** | **Contador sequencial** | Detecta saltos (`contador` não sequencial) e conta amostras perdidas |
| **2** | **Taxa de amostragem (Hz)** | Média, instantânea (média/std/min/max) via `micros()` do Arduino |
| **3** | **Sensores (range físico)** | Verifica se `ax,ay,az` ∈ [-16,16]g e `gx,gy,gz` ∈ [-2000,2000]°/s; mostra média, std, RMS |
| **4** | **Tempo PC** | Monotonicidade (sem deltas negativos) + duração total |
| **5** | **Valores inválidos** | Conta NaN/Inf |

---

## Saída esperada (exemplo)

```
============================================================
TESTANDO: dados\dados_aceleracao_giro-2026-08-01_12-22-42.csv
============================================================
Total de amostras: 14930

1. CONTADOR:
   Início: 1 | Fim: 14930
   Saltos: 0 | Amostras perdidas: 0

2. TAXA (Hz):
   Média: 211.14
   Inst. média: 211.15 | std: 1.72
   Min: 207.81 | Max: 221.83

3. SENSORES (range físico):
   ax : [   0.910,    1.090] media=  1.001 std=  0.007 rms=  1.001 OK
   ay : [  -0.040,    0.030] media= -0.004 std=  0.005 rms=  0.006 OK
   az : [  -0.090,    0.010] media= -0.038 std=  0.006 rms=  0.039 OK
   gx : [  -4.330,   -3.110] media= -3.649 std=  0.134 rms=  3.651 OK
   gy : [  -4.270,    3.350] media=  0.214 std=  0.310 rms=  0.376 OK
   gz : [  -1.160,    1.040] media= -0.344 std=  0.148 rms=  0.374 OK

4. TEMPO PC:
   Deltas negativos: 0 (esperado 0)
   Duração total: 71.2s

5. VALORES INVÁLIDOS:
   NaN/Inf: 0 (esperado 0)

============================================================
RESULTADO: PASSOU
============================================================
```

---

## Códigos de saída

| Código | Significado |
|--------|-------------|
| `0` | PASSOU (todos testes OK) |
| `1` | FALHOU (arquivo não existe, erro de parsing, ou algum teste falhou) |

Útil para automação/CI:
```bash
if python dados/testar_dados.py; then
    echo "Dados OK"
else
    echo "Dados com problemas"
fi
```

---

## Retorno programático

A função `testar_arquivo(caminho)` retorna `dict`:

```python
{
    "arquivo": "dados/...csv",
    "amostras": 14930,
    "saltos": 0,
    "perdidas": 0,
    "hz_medio": 211.14,
    "hz_std": 1.72,
    "fora_range": {"ax": 0, "ay": 0, "az": 0, "gx": 0, "gy": 0, "gz": 0},
    "negativos_pc": 0,
    "nan_inf": 0,
    "ok": true
}
```

---

## Dependências

- `numpy` ≥ 2.4.6
- Python 3.11+

---

## Estrutura esperada do CSV

```csv
tempo_arduino_us,tempo_relogio_pc,contador,ax,ay,az,gx,gy,gz
10002952,1722345678.123456,1,1.00,0.00,0.01,-3.48,0.61,-0.30
...
```

- **Header obrigatório** com 9 colunas exatas
- **Dados** numéricos (float/int)
- **Uma amostra por linha**

---

## Referências

- [[ARQUITETURA]] - Fluxo completo dos dados
- [[buffers]] - Buffer circular que alimenta o CSV
- [[gravador]] - Geração do CSV
- [[coletor]] - Aquisição que detecta saltos no contador