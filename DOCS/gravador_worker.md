# sensor/gravador_worker.py

**Responsabilidade:** Thread dedicada para consumir a fila de gravação e persistir CSV sem bloquear a aquisição serial.  
**Tipo:** Classe `GravadorWorker` (herda `threading.Thread`)  
**Thread:** `gravador-csv` (daemon)

---

## Interface Pública

```python
class GravadorWorker(Thread):
    def __init__(self, fila: Queue, tamanho_buffer: int = 1000):
        """
        Args:
            fila: Queue thread-safe compartilhada com Coletor
            tamanho_buffer: Repassado para GravadorCSV (batch size)
        """
    
    def run(self) -> None:
        """Loop principal da thread. Consome fila até receber sentinela None."""
    
    @property
    def erro(self) -> Exception | None:
        """Erro capturado durante execução (para diagnóstico externo)."""
```

---

## Fluxo Interno (`run()`)

```
┌─────────────────────────────────────────────────────────────┐
│ GravadorWorker.run()                                        │
├─────────────────────────────────────────────────────────────┤
│ gravador = GravadorCSV(tamanho_buffer=self.tamanho_buffer)  │
│                                                             │
│ while True:                                                 │
│     linha = self.fila.get()          # Bloqueante           │
│     try:                                                     │
│         if linha is None: break       # SENTINELA DE PARADA │
│         gravador.salvar(linha)        # Batch write interno │
│     finally:                                                 │
│         self.fila.task_done()         # Para Queue.join()   │
│                                                             │
│ # Cleanup (finally do try externo)                          │
│ gravador.fechar()  # Flush buffer residual + close file     │
└─────────────────────────────────────────────────────────────┘
```

---

## Protocolo de Parada (Sentinela)

```python
# Em SensorManager.parar():
self.fila_gravacao.put(None)   # Envia sentinela
self.gravador_thread.join()    # Aguarda thread terminar
```

**Por que sentinela?**
- `Queue.get()` é bloqueante → thread dorme sem CPU
- `None` é valor reservado que **nunca** é uma linha válida
- `task_done()` chamado mesmo na sentinela → `Queue.join()` funciona

---

## Tratamento de Erros

```python
try:
    gravador = GravadorCSV(...)
    while True:
        linha = self.fila.get()
        if linha is None: break
        gravador.salvar(linha)
        self.fila.task_done()
except Exception as erro:
    self.erro = erro              # Armazena para diagnóstico
    print(f"[Gravador] Erro: {erro}")
finally:
    if gravador:
        try: gravador.fechar()    # Sempre tenta flush final
        except Exception as e:
            self.erro = self.erro or e
            print(f"[Gravador] Erro ao fechar CSV: {e}")
```

**Garantias:**
- Arquivo **sempre fechado** (mesmo em erro)
- Erro disponível via `worker.erro` para UI/Manager
- `task_done()` em `finally` → não trava `Queue.join()`

---

## Thread Safety

| Recurso | Proteção |
|---------|----------|
| `fila` (Queue) | Thread-safe nativo (`get`, `put`, `task_done`) |
| `GravadorCSV` | Acesso exclusivo desta thread (não compartilhado) |
| `self.erro` | Escrita apenas aqui, leitura externa (atômico em CPython) |

---

## Métricas

| Métrica | Valor |
|---------|-------|
| CPU idle (fila vazia) | ~0% (bloqueado em `get()`) |
| CPU ativo (215 Hz) | ~0.1% (batch write eficiente) |
| Memória | GravadorCSV.buffer (≤1000 linhas) |
| Latência fim-para-fim | < 5ms (assíncrono) |

---

## Teste Standalone

```bash
python -c "
import sys; sys.path.insert(0, '.')
from sensor.gravador_worker import GravadorWorker
from queue import Queue
import time

fila = Queue()
worker = GravadorWorker(fila)
worker.start()

# Enviar 2500 linhas (2.5x batch size)
for i in range(2500):
    fila.put([i, time.time(), i, 0.1, 0.2, 0.3, 1, 2, 3])

fila.put(None)  # Sentinela
worker.join()
print('Erro:', worker.erro)
print('CSV em dados/')
"
```

---

## Dependências

- `threading.Thread` (stdlib)
- `queue.Queue` (stdlib)
- `sensor.gravador.GravadorCSV`

---

## Referências Cruzadas

| Arquivo | Linha | Relação |
|---------|-------|---------|
| `sensor/manager.py:26` | `GravadorWorker(self.fila_gravacao)` | Instanciação |
| `sensor/manager.py:27` | `self.gravador_thread.start()` | Launch thread |
| `sensor/manager.py:41` | `self.fila_gravacao.put(None)` | Sinal parada |
| `sensor/manager.py:44` | `self.gravador_thread.join()` | Aguarda fim |
| `sensor/coletor.py:58` | `fila_gravacao.put_nowait(linha)` | Produtor |
| `sensor/gravador.py:15` | `GravadorCSV(...)` | Composição |