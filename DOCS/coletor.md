# sensor/coletor.py

**Responsabilidade:** Thread de aquisição - consome `serial_reader`, processa amostras, detecta anomalias, alimenta buffer e fila de gravação.  
**Tipo:** Classe `Coletor` + função `executar()` (roda em thread `coletor-serial`)  
**Thread:** Thread dedicada daemon (`coletor-serial`)

---

## Interface Pública

```python
class Coletor:
    def __init__(self, porta="COM4", baudrate=115200, fila_gravacao=None):
        # Configuração
        self.porta = porta
        self.baudrate = baudrate
        self.fila_gravacao = fila_gravacao  # Queue para GravadorWorker
        
        # Estado
        self.rodando = False
        self.buffer = BufferSensores()      # Buffer circular compartilhado
        
        # Métricas
        self.numero_amostras = 0
        self.contador_anterior = None
        self.saltos_contador = 0
        self.amostras_perdidas = 0
        self.amostras_nao_enfileiradas = 0
        
        self.hz_medio = 0
        self.hz_inst = 0
        self.hz_inst_suavizado = 0
        self.tempo_arduino_inicial_us = 0
        self.tempo_arduino_anterior_us = 0
        self.historico_hzs_inst = deque(maxlen=100)
    
    def executar(self) -> None:
        """Loop principal de aquisição. Roda em thread separada."""
    
    def parar(self) -> None:
        """Sinaliza parada (seta self.rodando = False)."""
    
    def configurar_fila_gravacao(self, fila_gravacao) -> None:
        """Permite injeção de dependência da fila (usado pelo SensorManager)."""
```

---

## Fluxo Interno (`executar()`)

```
┌─────────────────────────────────────────────────────────────┐
│ Coletor.executar()                                          │
├─────────────────────────────────────────────────────────────┤
│ self.rodando = True                                         │
│ Reset contadores/métricas                                   │
│                                                             │
│ for t_arduino, t_pc, contador, ax, ay, az, gx, gy, gz      │
│     in ler_dados(porta, baudrate):                          │
│                                                             │
│     if not self.rodando: break         # Sinal de parada    │
│                                                             │
│     self.numero_amostras += 1                                  │
│     self._registrar_salto(contador)       # Detecta gaps     │
│                                                             │
│     # Cálculo Hz (usa tempo do Arduino = micros())          │
│     if self.numero_amostras == 1:                                  │
│         self.tempo_arduino_inicial_us = t_arduino              │
│         self.tempo_arduino_anterior_us = t_arduino             │
│     else:                                                      │
│         dt_total = (t_arduino - self.tempo_arduino_inicial_us) / 1e6 │
│         self.hz_medio = (self.numero_amostras - 1) / dt_total          │
│                                                             │
│         dt_inst = (t_arduino - self.tempo_arduino_anterior_us) / 1e6   │
│         self.hz_inst = 1 / dt_inst                                    │
│         self.historico_hzs_inst.append(self.hz_inst)                 │
│         self.hz_inst_suavizado = mean(historico)                    │
│         self.tempo_arduino_anterior_us = t_arduino                  │
│                                                             │
│     # Armazenamento                                           │
│     self.buffer.adicionar(t_arduino, t_pc, contador, ax, ay, az, gx, gy, gz) │
│     self._enfileirar_gravacao([t_arduino, t_pc, contador, ax, ay, az, gx, gy, gz]) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Métodos Privados

### `_registrar_salto(contador)`
```python
def _registrar_salto(self, contador):
    if self.contador_anterior is not None and contador > self.contador_anterior + 1:
        perdidas = int(contador - self.contador_anterior - 1)
        self.saltos_contador += 1
        self.amostras_perdidas += perdidas
        print(f"[Coletor] Salto: {self.contador_anterior:.0f} -> {contador:.0f} ({perdidas} perdidas)")
    self.contador_anterior = contador
```
- Detecta **contador não sequencial** → amostras perdidas na serial
- Usa `contador` do Arduino (inteiro incremental)

### `_enfileirar_gravacao(linha)`
```python
def _enfileirar_gravacao(self, linha):
    if self.fila_gravacao is None: return
    try:
        self.fila_gravacao.put_nowait(linha)  # Non-blocking!
    except Full:
        self.amostras_nao_enfileiradas += 1
        if self.amostras_nao_enfileiradas % 1000 == 1:
            print("[Coletor] Fila de gravação cheia; amostras não salvas no CSV.")
```
- **Non-blocking** (`put_nowait`) → nunca trava a thread serial
- Se fila cheia, **descarta e conta** (prioridade: aquisição contínua)

---

## Métricas Calculadas

| Métrica | Fórmula | Uso |
|---------|---------|-----|
| `hz_medio` | `(n-1) / (t_atual - t_inicial)` | Health check geral |
| `hz_inst` | `1 / (t_atual - t_anterior)` | Jitter detector |
| `hz_inst_suavizado` | `mean(últimos 100 hz_inst)` | UI statistics |
| `saltos_contador` | Contador de gaps > 1 | Qualidade sinal |
| `amostras_perdidas` | Soma de gaps | Total lost |

---

## Thread Safety

| Recurso | Proteção |
|---------|----------|
| `BufferSensores` | Lock interno (`_lock`) |
| `fila_gravacao` | `Queue` thread-safe nativo |
| Variáveis de métricas | Acesso apenas na thread coletor (sem concorrência) |

---

## Inicialização e Parada

```python
# Início (via SensorManager)
manager.iniciar()
# 1. Cria Queue(50000)
# 2. Inicia GravadorWorker (thread)
# 3. Coletor.configurar_fila_gravacao(fila)
# 4. Inicia Thread(target=coletor.executar, daemon=True)

# Parada
manager.parar()
# 1. coletor.parar() → self.rodando = False
#    (o leitor serial consulta esse estado entre leituras)
# 2. thread.join() → aguarda loop terminar
# 3. fila.put(None) → sentinela para GravadorWorker
# 4. gravador_thread.join() → flush CSV final
```

---

## Testes

```bash
# Teste standalone (com gravação)
python -c "
import sys; sys.path.insert(0, '.')
from sensor.coletor import Coletor
from sensor.gravador_worker import GravadorWorker
from queue import Queue

fila = Queue(50000)
g = GravadorWorker(fila); g.start()
c = Coletor(fila_gravacao=fila)
try: c.executar()
except KeyboardInterrupt: c.parar()
finally: fila.put(None); g.join()
"

# Teste rápido (sem gravação)
python -m sensor.teste_manager
```

---

## Métricas de Performance

| Métrica | Valor |
|---------|-------|
| Taxa loop | ~215 Hz |
| Overhead por amostra | ~50 µs |
| CPU thread coletor | ~1-2% |
| Memória | Buffer (10k × 9 × 8 bytes ≈ 720 KB) |

---

## Dependências

- `sensor.serial_reader` - `ler_dados()`
- `sensor.buffers` - `BufferSensores`
- `sensor.gravador_worker` - `GravadorWorker` (via Queue)
- `collections.deque` - histórico Hz
- `queue.Queue` / `queue.Full` - fila gravação
- `threading.Thread` - execução paralela

---

## Referências Cruzadas

| Arquivo | Linha | Relação |
|---------|-------|---------|
| `sensor/manager.py:12` | `self.coletor = Coletor()` | Instanciação |
| `sensor/manager.py:29` | `Thread(target=self.coletor.executar)` | Thread launch |
| [[gravador_worker]] | - | Consumidor fila |
| [[serial_reader]] | - | Produtor dados |
| [[buffers]] | - | Armazenamento |
