# sensor/serial_reader.py

**Responsabilidade:** Leitura bruta da porta serial e parsing de linhas CSV do Arduino.  
**Tipo:** Módulo utilitário (generator function)  
**Thread:** Executa na thread do coletor (`coletor-serial`)

---

## Interface Pública

```python
def ler_dados(porta: str, baudrate: int = 115200, timeout: float = 0.1) -> Generator[Tuple]:
    """
    Generator que lê linhas da serial e yield tuplas parseadas.
    
    Yields:
        (tempo_arduino_us: float, timestamp_pc: float, contador: float,
         ax: float, ay: float, az: float, gx: float, gy: float, gz: float)
    """
```

```python
def ler_dados_fake() -> Generator[Tuple]:
    """Generator de dados sintéticos para teste sem Arduino (~100 Hz)."""
```

---

## Fluxo Interno

```
┌─────────────────────┐
│ serial.Serial()     │  ──▶ Abre porta, configura baudrate/timeout
│ time.sleep(2)       │  ──▶ Aguarda Arduino resetar (DTR/RTS)
│ reset_input_buffer()│  ──▶ Limpa lixo inicial
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ while True:         │
│   timestamp = perf_counter()  (tempo PC alta resolução)
│   linha = readline().decode().strip()
│   if not linha: continue
│   campos = split(",")
│   if len != 8: continue
│   map(float, campos) → 8 variáveis
│   yield (t_arduino, t_pc, contador, ax, ay, az, gx, gy, gz)
└─────────────────────┘
```

---

## Decisões de Design Críticas

| Decisão | Justificativa |
|---------|---------------|
| `readline()` + `timeout=0.1` | Bloqueia até `\n` → **garante linha completa**; timeout evita travamento |
| `errors='ignore'` no decode | Descarta bytes corrompidos sem crashar |
| `strip()` antes do split | Remove `\r\n` e espaços |
| Validação `len(campos) == 8` | Filtra linhas parciais/corrompidas |
| `map(float, ...)` em try/except | Captura `ValueError` de parsing |
| Generator (`yield`) | **Lazy evaluation** - não acumula memória, stream direto para coletor |

---

## ⚠️ Bugs Corrigidos (Histórico)

### Bug: Pulando amostras / linhas inválidas
**Causa:** Substituição de `readline()` por `in_waiting + read()` que lia bytes brutos e cortava linhas no meio.

**Código Problemático (REMOVIDO):**
```python
# NÃO USE - QUEBRA LINHAS
bytes_available = arduino.in_waiting
if bytes_available > 0:
    dados_brutos = arduino.read(bytes_available).decode('utf-8', errors='ignore')
    linhas = dados_brutos.splitlines()  # Pode cortar linha no meio!
```

**Correção:** Restaurar `readline()` original (v1.0)

**Documentação:** `ERROS/correcao-pulos-amostras-serial.md`

---

## Configuração Esperada do Arduino

```cpp
// arduino/mpu-6050/mpu-6050.ino
Serial.begin(115200);  // DEVE COINCIDIR com baudrate=115200 no Python

// Formato de saída (linha CSV terminada em \n):
Serial.print(contador); Serial.print(",");
Serial.print(micros()); Serial.print(",");
Serial.print(ax); Serial.print(",");
Serial.print(ay); Serial.print(",");
Serial.print(az); Serial.print(",");
Serial.print(gx); Serial.print(",");
Serial.print(gy); Serial.print(",");
Serial.println(gz);  // \n no final!
```

---

## Testes

```bash
# Teste direto da serial (sem coletor)
python -c "
import serial, time
with serial.Serial('COM4', 115200, timeout=1) as s:
    time.sleep(12)  # delay Arduino setup
    s.reset_input_buffer()
    t=time.time(); c=0
    while time.time()-t<10:
        l=s.readline().decode().strip()
        if l: c+=1
    print(f'{c/10:.1f} Hz')
"

# Teste via módulo
python -c "
import sys; sys.path.insert(0, '.')
from sensor.serial_reader import ler_dados
for i, dados in enumerate(ler_dados('COM4', 115200)):
    print(dados)
    if i > 5: break
"
```

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Baud rate | 115200 |
| Timeout readline | 0.1s |
| Taxa real | ~215 Hz |
| Bytes/linha | ~50-60 |
| Throughput serial | ~11 KB/s |

---

## Dependências

- `pyserial` ≥ 3.5
- `time` (stdlib)

---

## Referências Cruzadas

| Arquivo | Uso |
|---------|-----|
| `sensor/coletor.py:92` | `for ... in ler_dados(...):` |
| `sensor/teste_manager.py` | Teste indireto via manager |
| `arduino/mpu-6050/mpu-6050.ino` | Produtor dos dados |