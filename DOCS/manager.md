# sensor/manager.py

**Responsabilidade:** Facade/Orquestrador - gerencia ciclo de vida completo do pipeline de aquisição (Coletor + GravadorWorker).  
**Tipo:** Classe `SensorManager` + instância global `manager`  
**Thread:** Cria e gerencia threads `coletor-serial` e `gravador-csv`

---

## Interface Pública

```python
class SensorManager:
    def __init__(self):
        self.coletor = Coletor()              # Instancia coletor
        self.thread = None                    # Thread coletor
        self.fila_gravacao = None             # Queue compartilhada
        self.gravador_thread = None           # Thread gravador
    
    def iniciar(self) -> None:
        """Inicia pipeline completo: fila → gravador → coletor."""
    
    def parar(self) -> None:
        """Para pipeline graciosamente: coletor → fila sentinela → gravador."""
    
    @property
    def buffer(self) -> BufferSensores:
        """Acesso direto ao buffer do coletor (para UI)."""

# Instância global (singleton prático)
manager = SensorManager()
```

---

## Fluxo `iniciar()`

```
┌─────────────────────────────────────────────────────────────┐
│ SensorManager.iniciar()                                     │
├─────────────────────────────────────────────────────────────┤
│ if thread viva: return  # Idempotente                        │
│                                                             │
│ # 1. Fila de gravação (buffer de pico)                     │
│ self.fila_gravacao = Queue(maxsize=50_000)                 │
│ self.coletor.configurar_fila_gravacao(self.fila_gravacao)  │
│                                                             │
│ # 2. Thread gravador (daemon)                              │
│ self.gravador_thread = GravadorWorker(self.fila_gravacao)  │
│ self.gravador_thread.start()  # Inicia run()               │
│                                                             │
│ # 3. Thread coletor (daemon)                               │
│ self.thread = Thread(                                       │
│     target=self.coletor.executar,                           │
│     name="coletor-serial",                                  │
│     daemon=True                                             │
│ )                                                           │
│ self.thread.start()  # Inicia loop de aquisição             │
└─────────────────────────────────────────────────────────────┘
```

---

## Fluxo `parar()`

```
┌─────────────────────────────────────────────────────────────┐
│ SensorManager.parar()                                       │
├─────────────────────────────────────────────────────────────┤
│ self.coletor.parar()       # Seta rodando=False             │
│                                                             │
│ if self.thread:                                          │
│     self.thread.join()     # Aguarda loop terminar         │
│                                                             │
│ # Sentinela para gravador esvaziar fila + fechar arquivo   │
│ if self.fila_gravacao:                                    │
│     self.fila_gravacao.put(None)                          │
│                                                             │
│ if self.gravador_thread:                                 │
│     self.gravador_thread.join()  # Aguarda flush + close   │
│                                                             │
│ # Reset referências                                        │
│ self.thread = None                                        │
│ self.gravador_thread = None                               │
│ self.fila_gravacao = None                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Decisions

| Decisão | Justificativa |
|---------|---------------|
| `Queue(maxsize=50_000)` | Buffer de pico ~3.8 min a 215 Hz; evita OOM se disco lento |
| Threads `daemon=True` | Programa encerra mesmo se join falhar (segurança) |
| `configurar_fila_gravacao()` | Injeção de dependência → Coletor não cria Queue |
| Instância global `manager` | Acesso simples: `from sensor.manager import manager` |
| `parar()` idempotente | Seguro chamar múltiplas vezes |

---

## Uso Típico

```python
# CLI simples (sensor/teste_manager.py)
from sensor.manager import manager
import time

manager.iniciar()
try:
    while True:
        if not manager.buffer.vazio():
            print(f"Contador: {manager.buffer.contador[-1]:.0f} | "
                  f"Amostras: {len(manager.buffer.contador)}")
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    manager.parar()

# UI PyQt (realtime/janela.py)
from sensor.manager import manager

class Janela(QMainWindow):
    def iniciar(self):
        self.manager.iniciar()  # Usa instância global
    
    def parar(self):
        self.manager.parar()
    
    def atualizar_grafico(self):
        dados = self.manager.buffer.snapshot(250)
        # ...
```

---

## Thread Safety

| Recurso | Acesso | Proteção |
|---------|--------|----------|
| `fila_gravacao` | Coletor (put) + Gravador (get) | `Queue` nativo |
| `coletor.buffer` | Coletor (write) + UI (read) | `BufferSensores._lock` |
| `coletor.rodando` | Manager (write) + Coletor (read) | Acesso atômico bool |
| `thread` / `gravador_thread` | Manager apenas | Single-writer |

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Tempo `iniciar()` | ~2.1s (inclui `time.sleep(2)` no serial_reader) |
| Tempo `parar()` | ~0.5s (join threads + flush CSV) |
| Overhead memória | Queue(50k) ≈ 4 MB + threads |
| CPU manager thread | ~0% (apenas coordenação) |

---

## Testes

```bash
# Teste rápido via módulo
python -m sensor.teste_manager

# Teste programático
python -c "
import sys; sys.path.insert(0, '.')
from sensor.manager import manager
import time

manager.iniciar()
time.sleep(5)
print(f'Amostras: {len(manager.buffer.contador)}')
print(f'Hz: {manager.coletor.hz_medio:.1f}')
manager.parar()
"
```

---

## Dependências

- `queue.Queue` (stdlib)
- `threading.Thread` (stdlib)
- `sensor.coletor.Coletor`
- `sensor.gravador_worker.GravadorWorker`

---

## Referências Cruzadas

| Arquivo | Linha | Relação |
|---------|-------|---------|
| `sensor/__init__.py` | - | Exporta `manager` |
| `sensor/coletor.py:12` | `self.coletor = Coletor()` | Composição |
| `sensor/gravador_worker.py:15` | `GravadorWorker(fila)` | Composição |
| `realtime/janela.py:20` | `from sensor.manager import manager` | UI usa global |
| `realtime/janela.py:328` | `self.manager.iniciar()` | Botão Iniciar |
| `realtime/janela.py:333` | `self.manager.parar()` | Botão Parar |
| `realtime/janela.py:354` | `self.manager.buffer.snapshot()` | Leitura UI |
| `sensor/teste_manager.py:3` | `from sensor.manager import manager` | CLI teste |