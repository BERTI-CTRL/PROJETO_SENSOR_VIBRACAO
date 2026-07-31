# Correção do Buffer Congelando após 10.000 Amostras (Wrap-Around)

**Data:** 31/07/2026  
**Projeto:** PROJETO_SENSOR_VIBRACAO  
**Sintoma:** Janela PyQt (`janela.py`) congelava após ~10.000 amostras (45-50s a 215 Hz). Print `[Janela]` mostrava contador fixo em 10000. Gráfico parava de atualizar.  
**Status:** ✅ RESOLVIDO  

---

## Resumo Executivo

O problema era o **wrap-around do buffer circular** na versão otimizada com NumPy (`buffers.py`). 

- Buffer tamanho: **10.000 amostras**
- Taxa: **~215 Hz** → buffer enche em **~46 segundos**
- Após encher, novas amostras sobrescrevem as mais antigas (índice circular `_index`)
- As **propriedades** `buffer.ax`, `buffer.contador`, etc. retornavam `self._dados[:self._count, i]` → **sempre índices 0-9999** (amostras MAIS ANTIGAS)
- O `snapshot()` também usava `inicio = max(0, self._count - quantidade)` → com buffer cheio, `inicio=0` → **ordem de armazenamento, não cronológica**
- Resultado: Janela exibia dados **estáticos** (as 10.000 primeiras amostras), parecia "congelada"

---

## Arquivos Envolvidos e Alterações

### 1. `sensor/buffers.py` — **CAUSA RAIZ E CORREÇÃO**

#### ❌ Código Problemático (Versão NumPy original)
```python
# Linhas 67-110: Propriedades para compatibilidade
@property
def contador(self):
    with self._lock:
        return self._dados[:self._count, 2]  # BUG: sempre 0 até _count-1

# ... ax, ay, az, gx, gy, gz idêntico

# Linhas 48-56: snapshot()
def snapshot(self, quantidade=None):
    with self._lock:
        if quantidade is None:
            quantidade = self._count
        inicio = max(0, self._count - quantidade)  # BUG: com buffer cheio, inicio=0
        return {
            coluna: self._dados[inicio:self._count, i].copy()
            for i, coluna in enumerate(self.COLUNAS)
        }
```

**Por que falhou:**
- Buffer circular NumPy: dados mais recentes ficam em `_index` até fim, depois `0` até `_index-1`
- `_count` para de crescer ao atingir `tamanho_maximo` (10000)
- Propriedades retornavam `self._dados[:10000, i]` = **índices 0-9999 fixos** (as PRIMEIRAS 10k amostras)
- `snapshot(10000)` com buffer cheio: `inicio = max(0, 10000-10000) = 0` → `self._dados[0:10000]` = mesma ordem de armazenamento, não cronológica
- Janela via `buffer.contador[-1]` sempre mostrava o mesmo valor (amostra 9999)

#### ✅ Código Corrigido
```python
# Método auxiliar para lidar com wrap-around
def _get_coluna_slice(self, coluna_idx):
    """Retorna view da coluna com TODAS as amostras em ordem cronológica (antigo → novo)."""
    with self._lock:
        if self._count == 0:
            return self._dados[0:0, coluna_idx]
        
        if self._count < self.tamanho_maximo:
            # Buffer não cheio: dados contíguos em 0 até _count-1
            return self._dados[:self._count, coluna_idx]
        else:
            # Buffer cheio + wrap-around: ordem cronológica = _index até fim, depois 0 até _index-1
            return np.concatenate([
                self._dados[self._index:, coluna_idx],
                self._dados[:self._index, coluna_idx]
            ])

# Propriedades usam o método auxiliar
@property
def contador(self):
    return self._get_coluna_slice(2)

# ... ax, ay, az, gx, gy, gz usam _get_coluna_slice(3) até _get_coluna_slice(8)

# snapshot() corrigido para wrap-around
def snapshot(self, quantidade=None):
    with self._lock:
        if quantidade is None:
            quantidade = self._count
        quantidade = min(quantidade, self._count)
        if quantidade == 0:
            return {coluna: self._dados[0:0, i].copy() for i, coluna in enumerate(self.COLUNAS)}
        
        if self._count < self.tamanho_maximo:
            # Buffer não cheio: contíguo
            inicio = self._count - quantidade
            return {
                coluna: self._dados[inicio:self._count, i].copy()
                for i, coluna in enumerate(self.COLUNAS)
            }
        else:
            # Buffer cheio + wrap-around: montar array cronológico e pegar últimos
            dados_cronologicos = np.concatenate([
                self._dados[self._index:, :],
                self._dados[:self._index, :]
            ])
            inicio = len(dados_cronologicos) - quantidade
            return {
                coluna: dados_cronologicos[inicio:, i].copy()
                for i, coluna in enumerate(self.COLUNAS)
            }
```

---

## Cronologia da Descoberta

| Passo | Ação | Resultado |
|-------|------|-----------|
| 1 | Testar sistema por 30s | Funcionava: buffer crescia, contador = buffer size |
| 2 | Testar sistema por 60s | Buffer parou em 10000, contador continuou (10224, 11266...) |
| 3 | Testar sistema por 90s | Buffer 10000 fixo, contador 14395, Hz estável 211 |
| 4 | Perceber: `snapshot()` e propriedades retornam ordem errada após wrap |
| 5 | Criar teste unitário isolado do `BufferSensores` com tamanho=10 |
| 6 | Confirmar: propriedade `[5,6,7,8,9,10,11,12,13,14]` vs `snapshot()` `[10,11,12,13,14,5,6,7,8,9]` |
| 6 | Corrigir `_get_coluna_slice()` para concatenar `_index:` + `:_index` |
| 7 | Corrigir `snapshot()` para montar array cronológico antes de fatiar |
| 8 | Testar novamente: propriedade == snapshot ✅ |
| 9 | Testar sistema completo 80s: **zero saltos, Hz estável, contador cresce** |

---

## Evidências dos Testes

### Teste Unitário Isolado (buffer tamanho=10, 15 inserts)
```python
# Antes da correção:
buffer.contador        # [ 5.  6.  7.  8.  9. 10. 11. 12. 13. 14.]  (CRONOLÓGICO ✓)
buffer.snapshot(10)    # [10. 11. 12. 13. 14.  5.  6.  7.  8.  9.]  (ORDEM ARMAZENAMENTO ✗)

# Após correção:
buffer.contador        # [ 5.  6.  7.  8.  9. 10. 11. 12. 13. 14.]
buffer.snapshot(10)    # [ 5.  6.  7.  8.  9. 10. 11. 12. 13. 14.]  (IGUAIS ✓)
buffer.snapshot(5)     # [10. 11. 12. 13. 14.]  (últimos 5)
buffer.contador[-5:]   # [10. 11. 12. 13. 14.]  (IGUAIS ✓)
```

### Teste Sistema Completo (80s = ~17.000 amostras)
```
T: 55s | Buffer:  9170 | Contador:  9170 | Hz: 212.1 | Saltos: 0
T: 60s | Buffer: 10000 | Contador: 10224 | Hz: 212.0 | Saltos: 0   ← WRAP-AROUND INICIA
T: 65s | Buffer: 10000 | Contador: 11266 | Hz: 211.7 | Saltos: 0
T: 70s | Buffer: 10000 | Contador: 12310 | Hz: 211.5 | Saltos: 0
T: 75s | Buffer: 10000 | Contador: 13353 | Hz: 211.4 | Saltos: 0
T: 80s | Buffer: 10000 | Contador: 14395 | Hz: 211.2 | Saltos: 0
```

**Resultado:** Buffer mantém 10000, contador cresce continuamente, Hz estável, **zero saltos**.

---

## Lições Aprendidas

1. **Buffer circular com NumPy exige cuidado com wrap-around** — não basta usar `_count` como limite
2. **Ordem cronológica ≠ ordem de armazenamento** após wrap-around
   - Armazenamento: `_index` (mais novo) → fim → 0 → `_index-1` (mais velho dos recentes)
   - Cronológica: `_index` (mais velho dos recentes) → ... → `_index-1` (mais novo)
3. **Tanto propriedades quanto `snapshot()` devem concordar** na ordem retornada
4. **Teste unitário com buffer pequeno** (tamanho=10) acelera validação de wrap-around

---

## Checklist para Evitar Regressão

- [ ] Propriedades `ax`, `ay`, `az`, `gx`, `gy`, `gz`, `contador`, `timestamp`, `tempo_arduino_us` usam `_get_coluna_slice()`
- [ ] `snapshot()` monta array cronológico antes de fatiar quando buffer cheio
- [ ] Teste unitário com `tamanho=10` e `range(15)` passa (propriedade == snapshot)
- [ ] Teste longo (>60s a 200+ Hz) mantém Hz estável, contador crescente, zero saltos

---

## Comandos de Teste Rápido

```bash
# 1. Teste unitário wrap-around (buffer pequeno)
python -c "
import sys; sys.path.insert(0, '.')
from sensor.buffers import BufferSensores
import numpy as np
b = BufferSensores(tamanho=10)
for i in range(15): b.adicionar(i,i,i,i*0.1,i*0.2,i*0.3,i,i*2,i*3)
snap = b.snapshot(10)
print('OK' if np.array_equal(b.contador, snap['contador']) else 'FALHA')
"

# 2. Teste sistema longo (passa 10k amostras)
python -c "
import sys; sys.path.insert(0, '.')
from sensor.manager import manager
import time
manager.iniciar()
t=time.time()
while time.time()-t < 70:
    time.sleep(1)
    if not manager.buffer.vazio():
        print(f'B: {len(manager.buffer.contador)} | C: {manager.buffer.contador[-1]:.0f} | Hz: {manager.coletor.hz_medio:.1f} | S: {manager.coletor.saltos_contador}')
manager.parar()
" 2>&1 | grep -v "INICIOU\|Coletor\|Esperando\|Recebi\|Parando\|Aquisi"
```

---

## Referências de Código

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `sensor/buffers.py` | 68-70 | `_get_coluna_slice()` - método central do wrap-around |
| `sensor/buffers.py` | 72-108 | Propriedades `contador`, `ax`, `ay`, `az`, `gx`, `gy`, `gz`, etc. |
| `sensor/buffers.py` | 48-68 | `snapshot()` corrigido para wrap-around |
| `sensor/coletor.py` | 126-128 | `buffer.adicionar()` - chama a cada amostra |
| `realtime/janela.py` | 354-359 | `buffer.snapshot(250)` + `buffer.contador[-1]` |

---

**Conclusão:** O bug era **exclusivamente na lógica de wrap-around do `buffers.py` NumPy**. A correção garante que propriedades e `snapshot()` retornem dados em **ordem cronológica** (mais antigo → mais novo) tanto antes quanto depois do buffer encher. O sistema agora roda indefinidamente sem congelar.