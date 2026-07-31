# sensor/gravador.py

**Responsabilidade:** Escrita de arquivos CSV com buffer interno (batch write) para performance de disco.  
**Tipo:** Classe `GravadorCSV`  
**Thread:** Usada pela thread `GravadorWorker` (não thread-safe por si só)

---

## Interface Pública

```python
class GravadorCSV:
    def __init__(self, arquivo: str = "dados/dados_aceleracao_giro.csv", tamanho_buffer: int = 1000):
        """
        Args:
            arquivo: Caminho base (timestamp é adicionado automaticamente)
            tamanho_buffer: Linhas acumuladas antes de flush no disco
        """
    
    def salvar(self, linha: list) -> None:
        """Adiciona linha ao buffer interno. Flush automático ao atingir tamanho_buffer."""
    
    def fechar(self) -> None:
        """Flush final do buffer restante e fecha arquivo. Deve ser chamado ao encerrar."""
```

---

## Fluxo Interno

```
┌─────────────────────────────────────────────────────────────┐
│ GravadorCSV.__init__()                                      │
├─────────────────────────────────────────────────────────────┤
│ timestamp = now() → "YYYY-MM-DD_HH-MM-SS"                   │
│ arquivo_final = f"dados/dados_aceleracao_giro-{timestamp}.csv" │
│ open(arquivo, mode="a", newline="", encoding="utf-8")       │
│ csv.writer(arquivo)                                         │
│ if arquivo_novo: writeheader([t_arduino, t_pc, contador,   │
│                               ax, ay, az, gx, gy, gz])      │
│ self.buffer = []  # Lista Python para batch                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ salvar(linha)                                               │
├─────────────────────────────────────────────────────────────┤
│ self.buffer.append(linha)                                   │
│ if len(self.buffer) >= self.tamanho_buffer:                 │
│     self.writer.writerows(self.buffer)  # Batch write       │
│     self.buffer.clear()                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ fechar()                                                    │
├─────────────────────────────────────────────────────────────┤
│ if self.buffer:                                             │
│     self.writer.writerows(self.buffer)  # Flush final       │
│     self.buffer.clear()                                     │
│ self.f.close()                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Formato CSV Gerado

```csv
tempo_arduino_us,tempo_relogio_pc,contador,ax,ay,az,gx,gy,gz
10002952,1722345678.123456,1,1.00,0.00,0.01,-3.48,0.61,-0.30
10007644,1722345678.123498,2,0.99,0.00,0.02,-3.41,0.49,-0.06
...
```

| Coluna | Tipo | Origem | Unidade |
|--------|------|--------|---------|
| `tempo_arduino_us` | int | `micros()` Arduino | µs |
| `tempo_relogio_pc` | float | `time.perf_counter()` Python | s (epoch) |
| `contador` | int | Incremental Arduino | - |
| `ax, ay, az` | float | Acelerômetro MPU6050 | g |
| `gx, gy, gz` | float | Giroscópio MPU6050 | °/s |

---

## Configuração de Performance

| Parâmetro | Valor Padrão | Impacto |
|-----------|--------------|---------|
| `tamanho_buffer` | 1000 linhas | Batch size (I/O calls) |
| `newline=""` | Python 3 | Evita linhas em branco no Windows |
| `encoding="utf-8"` | Padrão | Compatibilidade |

**Por que batch write?**
- Escrita síncrona linha-a-linha = ~1000 syscalls/s a 215 Hz (lento)
- Batch 1000 = ~0.2 syscalls/s (rápido)
- Tradeoff: até 1000 linhas em memória se crash (aceitável)

---

## Uso pelo `GravadorWorker`

```python
# sensor/gravador_worker.py
class GravadorWorker(Thread):
    def run(self):
        gravador = GravadorCSV(tamanho_buffer=1000)
        while True:
            linha = self.fila.get()
            if linha is None: break  # Sentinela
            gravador.salvar(linha)
            self.fila.task_done()
        gravador.fechar()  # Flush final
```

---

## Ciclo de Vida do Arquivo

```
Início aquisição          Durante                    Parada
─────────────            ─────────                  ───────
1. Cria arquivo         1. Acumula em buffer       1. Sentinela None
2. Escreve header       2. A cada 1000 linhas:     2. gravador.fechar()
3. Buffer = []            writerows() + clear()      - Flush buffer
                                                   - Close file
                                                   3. Arquivo completo
```

**Nome do arquivo:** `dados/dados_aceleracao_giro-2026-07-31_15-39-17.csv`

---

## Tratamento de Erros

```python
# Em GravadorWorker.run()
try:
    gravador = GravadorCSV(...)
    while True:
        linha = self.fila.get()
        if linha is None: break
        gravador.salvar(linha)
        self.fila.task_done()
except Exception as erro:
    self.erro = erro  # Disponível para UI/Manager
    print(f"[Gravador] Erro: {erro}")
finally:
    if gravador:
        try: gravador.fechar()
        except Exception as e: self.erro = self.erro or e
```

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Batch size | 1000 linhas |
| Taxa flush | ~0.2/s (a 215 Hz) |
| Tamanho arquivo/hora | ~50 MB (215 Hz × 3600 × ~60 bytes) |
| Overhead CPU | Negligível (<0.1%) |
| Latência escrita | Assíncrona (não bloqueia aquisição) |

---

## Testes

```bash
# Teste standalone
python -c "
import sys; sys.path.insert(0, '.')
from sensor.gravador import GravadorCSV
import time

g = GravadorCSV(tamanho_buffer=5)
for i in range(12):
    g.salvar([i, time.time(), i, 0.1, 0.2, 0.3, 1, 2, 3])
    time.sleep(0.01)
g.fechar()
print('CSV criado - verificar em dados/')
"
```

---

## Dependências

- `csv` (stdlib)
- `pathlib.Path` (stdlib)
- `datetime` (stdlib)

---

## Referências Cruzadas

| Arquivo | Linha | Relação |
|---------|-------|---------|
| `sensor/gravador_worker.py:15` | `GravadorCSV(tamanho_buffer=1000)` | Instanciação |
| `sensor/gravador_worker.py:34` | `gravador.salvar(linha)` | Escrita loop |
| `sensor/gravador_worker.py:45` | `gravador.fechar()` | Cleanup |
| `sensor/manager.py:26` | `GravadorWorker(fila)` | Thread launch |
| `sensor/coletor.py:130` | `fila_gravacao.put_nowait([...])` | Produtor |
| `sensor/teste_manager.py` | - | Teste indireto |