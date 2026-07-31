# sensor/buffers.py

**Responsabilidade:** Buffer circular thread-safe para armazenar histórico de amostras do MPU6050 com acesso otimizado via NumPy.  
**Tipo:** Classe `BufferSensores`  
**Thread-Safety:** Lock interno (`threading.Lock`) em todas as operações públicas

---

## Interface Pública

```python
class BufferSensores:
    def __init__(self, tamanho: int = 10000):
        """Cria buffer para 'tamanho' amostras (padrão 10.000)."""
    
    def adicionar(self, t_arduino_us, t_pc, contador, ax, ay, az, gx, gy, gz) -> None:
        """Adiciona uma amostra (thread-safe)."""
    
    def vazio(self) -> bool:
        """True se buffer não tem amostras."""
    
    def tamanho_atual(self) -> int:
        """Quantidade de amostras armazenadas (≤ tamanho_maximo)."""
    
    def snapshot(self, quantidade: int = None) -> dict:
        """
        Retorna janela das últimas 'quantidade' amostras em ORDEM CRONOLÓGICA.
        
        Returns:
            dict com chaves: tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz
            Cada valor é np.ndarray (cópia) com shape (quantidade,)
        """
    
    def limpar(self) -> None:
        """Remove todas as amostras (reset índice/contador)."""
    
    # PROPRIEDADES DE COMPATIBILIDADE (janela.py usa buffer.ax, buffer.contador, etc.)
    @property
    def tempo_arduino_us(self) -> np.ndarray: ...
    @property
    def timestamp(self) -> np.ndarray: ...
    @property
    def contador(self) -> np.ndarray: ...
    @property
    def ax(self) -> np.ndarray: ...
    @property
    def ay(self) -> np.ndarray: ...
    @property
    def az(self) -> np.ndarray: ...
    @property
    def gx(self) -> np.ndarray: ...
    @property
    def gy(self) -> np.ndarray: ...
    @property
    def gz(self) -> np.ndarray: ...
```

---

## Estrutura Interna (NumPy 2D)

```python
# Array único contíguo: (tamanho_maximo, 9 colunas)
# Colunas: 0=t_arduino_us, 1=t_pc, 2=contador, 3=ax, 4=ay, 5=az, 6=gx, 7=gy, 8=gz
self._dados = np.zeros((tamanho, 9), dtype=np.float64)

self._index = 0      # Próxima posição de escrita (circular)
self._count = 0      # Total amostras escritas (cresce até tamanho_maximo)
self._lock = Lock()  # Thread safety
```

---

## Lógica de Wrap-Around (CRÍTICO)

### Escrita (`adicionar`)
```
┌─────────────────────────────────────────────────────────────┐
│ self._dados[self._index] = [t_arduino, t_pc, contador,     │
│                              ax, ay, az, gx, gy, gz]        │
│ self._index = (self._index + 1) % self.tamanho_maximo       │
│ if self._count < self.tamanho_maximo: self._count += 1      │
└─────────────────────────────────────────────────────────────┘

Exemplo (tamanho=5):
  Inserção 0: index=0, count=1  → [0] _ _ _ _
  Inserção 1: index=1, count=2  → [0,1] _ _ _
  Inserção 4: index=4, count=5  → [0,1,2,3,4] (CHEIO)
  Inserção 5: index=0, count=5  → [5,1,2,3,4] (sobrescreve 0)
  Inserção 6: index=1, count=5  → [5,6,2,3,4] (sobrescreve 1)
```

### Leitura Cronológica (`_get_coluna_slice`)

```python
def _get_coluna_slice(self, coluna_idx):
    with self._lock:
        if self._count == 0:
            return self._dados[0:0, coluna_idx]  # array vazio
        
        if self._count < self.tamanho_maximo:
            # Buffer NÃO cheio: dados contíguos em 0 até _count-1
            return self._dados[:self._count, coluna_idx]
        else:
            # Buffer CHEIO + wrap: ordem cronológica = _index até fim, depois 0 até _index-1
            return np.concatenate([
                self._dados[self._index:, coluna_idx],   # Parte 1: mais antigos dos recentes
                self._dados[:self._index, coluna_idx]    # Parte 2: mais recentes
            ])
```

**Visualização wrap-around (tamanho=5, count=5, index=2):**
```
Armazenamento físico:     [5, 6, 2, 3, 4]
                          ↑         ↑
                          index=2   fim
                          
Ordem cronológica (retornada):
  Parte 1: _dados[2:]  → [2, 3, 4]   (amostras 2,3,4)
  Parte 2: _dados[:2]  → [5, 6]     (amostras 5,6 - mais recentes)
  Resultado: [2, 3, 4, 5, 6]  ✓ (antigo → novo)
```

### `snapshot(quantidade)` com Wrap-Around

```python
def snapshot(self, quantidade=None):
    with self._lock:
        if quantidade is None: quantidade = self._count
        quantidade = min(quantidade, self._count)
        if quantidade == 0: return {col: empty_array ...}
        
        if self._count < self.tamanho_maximo:
            # Contíguo: fatia direta
            inicio = self._count - quantidade
            return {col: self._dados[inicio:self._count, i].copy() ...}
        else:
            # Cheio: monta array cronológico completo, pega últimos 'quantidade'
            dados_cron = np.concatenate([
                self._dados[self._index:, :],
                self._dados[:self._index, :]
            ])
            inicio = len(dados_cron) - quantidade
            return {col: dados_cron[inicio:, i].copy() ...}
```

---

## Propriedades de Compatibilidade

```python
@property
def contador(self): return self._get_coluna_slice(2)
@property
def ax(self): return self._get_coluna_slice(3)
# ... ay(4), az(5), gx(6), gy(7), gz(8), t_arduino(0), t_pc(1)
```

**Por que existem:** `realtime/janela.py` acessa `buffer.contador[-1]`, `len(buffer.ax)`, `buffer.ax` diretamente. As propriedades mantêm **100% compatibilidade** com API de `deque` (retornam `np.ndarray` que suporta indexação, `len()`, `[-1]`).

---

## ⚠️ Bugs Corrigidos

### Bug: Buffer congelando após 10.000 amostras
**Causa:** Propriedades e `snapshot()` retornavam ordem de **armazenamento físico** (0..9999) em vez de **ordem cronológica** após wrap-around.

**Sintoma:** Janela mostrava contador fixo em 10000, gráfico parado.

**Correção:** Implementar `_get_coluna_slice()` com `np.concatenate([_index:, :_index])` e `snapshot()` montar array cronológico antes de fatiar.

**Documentação:** `ERROS/correcao-buffer-congelando-wrap-around.md`

---

## Performance

| Operação | Complexidade | Tempo típico |
|----------|--------------|--------------|
| `adicionar()` | O(1) | ~0.5 µs |
| `vazio()` | O(1) | ~0.1 µs |
| `tamanho_atual()` | O(1) | ~0.1 µs |
| `snapshot(k)` | O(k) copy | ~50 µs (k=250) |
| Propriedades (ex: `buffer.ax`) | O(n) copy | ~200 µs (n=10000) |

**Nota:** Propriedades fazem cópia completa (`np.ndarray.copy()`). Para UI frequente, prefira `snapshot(quantidade)` que copia só o necessário.

---

## Uso na UI (`realtime/janela.py`)

```python
# Atualização gráfica (5 FPS = 200ms)
dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)  # 250 pontos
contadores = np.arange(len(dados['contador']))        # Eixo X relativo 0..249
self.curva_ax.setData(contadores, np.asarray(dados["ax"]), skipFiniteCheck=True)

# Estatísticas (0.5 Hz = 500ms)
dados_ax = self.manager.buffer.snapshot(PONTOS_GRAFICO)["ax"]
est = calcular_estatisticas(dados_ax)
```

---

## Testes

```bash
# Teste unitário wrap-around
python -c "
import sys; sys.path.insert(0, '.')
from sensor.buffers import BufferSensores
import numpy as np

b = BufferSensores(tamanho=10)
for i in range(15): b.adicionar(i,i,i,i*0.1,i*0.2,i*0.3,i,i*2,i*3)
snap = b.snapshot(10)
print('OK' if np.array_equal(b.contador, snap['contador']) else 'FALHA')
print('contador:', b.contador)
print('snapshot:', snap['contador'])
"
```

---

## Métricas de Memória

| Configuração | Memória (aprox) |
|--------------|-----------------|
| 10.000 amostras × 9 × float64 | 720 KB |
| 100.000 amostras × 9 × float64 | 7.2 MB |
| Overhead Lock + índices | < 1 KB |

---

## Dependências

- `numpy` ≥ 2.4.6 (array 2D, concat, slice, copy)
- `threading.Lock` (stdlib) - sincronização

---

## Referências Cruzadas

| Arquivo | Linha | Uso |
|---------|-------|-----|
| `sensor/coletor.py:15` | `self.buffer = BufferSensores()` | Instanciação |
| `sensor/coletor.py:126` | `self.buffer.adicionar(...)` | Escrita (215 Hz) |
| `sensor/manager.py:53` | `return self.coletor.buffer` | Acesso via property |
| `realtime/janela.py:342` | `if self.manager.buffer.vazio():` | Check vazio |
| `realtime/janela.py:354` | `dados = self.manager.buffer.snapshot(250)` | Leitura UI |
| `realtime/janela.py:483` | `len(self.manager.buffer.ax)` | Property compat |
| `realtime/janela.py:488` | `snapshot(250)["ax"]` | Estatísticas |