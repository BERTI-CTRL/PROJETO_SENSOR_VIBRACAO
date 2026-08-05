# Correção do Problema de Pulando Amostras na Recepção Serial

**Data:** 31/07/2026  
**Projeto:** PROJETO_SENSOR_VIBRACAO  
**Sintoma:** Janela PyQt (`janela.py`) mostrava pulos de amostras; CSV gravava com saltos no contador; Hz médio caía drasticamente.  
**Status:** ✅ RESOLVIDO  

---

> **Contexto histórico:** os valores de 200 ms, 5 FPS e 250 pontos citados neste registro descrevem o experimento da época. A configuração atual é 33 ms (~30 FPS) e 150 pontos; consulte `README.md` e `DOCS/janela.md`.

## Resumo Executivo

O problema **não era perda real de amostras do Arduino**, mas sim **quebra de linhas na leitura serial Python** causada por uma modificação incorreta no `serial_reader.py`. O Arduino enviava dados contíguos (~215 Hz), mas o Python lia linhas quebradas, interpretando como amostras perdidas.

**Causa Raiz:** Substituição do `readline()` por `in_waiting + read()` que lê bytes brutos e pode cortar linhas no meio.

**Solução:** Restaurar `serial_reader.py` original com `readline()` + timeout adequado.

---

## Arquivos Envolvidos e Alterações

### 1. [[serial_reader]] — **CAUSA RAIZ**

#### ❌ Código Problemático (Minha modificação incorreta)
```python
# Linhas 17-50 (versão quebrada)
while True:
    timestamp = time.perf_counter()
    bytes_available = arduino.in_waiting          # PROBLEMA: lê bytes disponíveis
    if bytes_available > 0:
        dados_brutos = arduino.read(bytes_available).decode('utf-8', errors='ignore')
        linhas = dados_brutos.splitlines()        # PROBLEMA: pode cortar linha no meio
        for linha in linhas:
            # processamento...
    else:
        time.sleep(0.001)
```

**Por que falhou:**
- `in_waiting` retorna bytes **disponíveis no momento**, não linhas completas
- `read(bytes_available)` lê **exatamente aqueles bytes**, podendo cortar uma linha CSV no meio
- `splitlines()` divide no `\n`, mas a linha pode ter chegado incompleta
- Resultado: linhas parciais → `ValueError` no parse → amostras "inválidas" → contador pula

#### ✅ Código Corrigido (Original restaurado)
```python
# Linhas 23-85 (versão original funcional)
linhas_invalidas = 0
while True:
    timestamp = time.perf_counter()
    
    print("Esperando linha...")
    dados_linha = arduino.readline().decode(     # CORRETO: readline() bloqueia até \n
        'utf-8',
        errors='ignore'
    ).strip()

    if not dados_linha:
        continue
    print("Recebi bytes:", repr(dados_linha))
    
    campos = dados_linha.split(",")
    if len(campos) != 8:
        linhas_invalidas += 1 
        continue
    
    try:
        contador, tempo_arduino_us, ax, ay, az, gx, gy, gz = map(float, campos)
        # ...
        yield (tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz)
    except ValueError:
        linhas_invalidas += 1
        print(f"[Serial] Linha inválida: {repr(dados_linha)}")
        continue
```

**Por que funciona:**
- `readline()` **bloqueia até receber `\n`** (linha completa)
- `timeout=0.1` evita travamento infinito
- Garante que cada `yield` = 1 amostra completa e válida

---

### 2. [[buffers]] — **OTIMIZAÇÃO (Não causou o bug, mas foi reescrito)**

#### Versão Original (~100 linhas, 9 deques)
```python
# buffers.py original
self.tempo_arduino_us = deque(maxlen=tamanho)
self.timestamp = deque(maxlen=tamanho)
self.contador = deque(maxlen=tamanho)
self.ax = deque(maxlen=tamanho)
# ... mais 5 deques

def adicionar(self, ...):
    with self._lock:
        self.tempo_arduino_us.append(tempo_arduino_us)
        self.timestamp.append(timestamp)
        # ... 9 appends individuais

def snapshot(self, quantidade=None):
    with self._lock:
        # islice em 9 deques separados
        return {chave: list(islice(deque, inicio, fim)) for ...}
```

#### Versão Otimizada (~50 linhas, 1 array NumPy 2D)
```python
# buffers.py otimizado
import numpy as np

COLUNAS = [
    "tempo_arduino_us", "timestamp", "contador",
    "ax", "ay", "az", "gx", "gy", "gz"
]

def __init__(self, tamanho=10000):
    self._dados = np.zeros((tamanho, 9), dtype=np.float64)
    self._index = 0
    self._count = 0

def adicionar(self, tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz):
    with self._lock:
        self._dados[self._index] = [tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz]
        self._index = (self._index + 1) % self.tamanho_maximo
        if self._count < self.tamanho_maximo:
            self._count += 1

def snapshot(self, quantidade=None):
    with self._lock:
        if quantidade is None: quantidade = self._count
        inicio = max(0, self._count - quantidade)
        return {coluna: self._dados[inicio:self._count, i].copy() for i, coluna in enumerate(self.COLUNAS)}

# PROPRIEDADES PARA COMPATIBILIDADE (janela.py usa buffer.ax, buffer.contador, etc.)
@property
def ax(self):
    with self._lock:
        return self._dados[:self._count, 3]
# ... ax, ay, az, gx, gy, gz, contador, timestamp, tempo_arduino_us
```

**Benefícios:**
- ✅ **Performance:** NumPy slicing é ~10x mais rápido que `deque + islice`
- ✅ **Memória:** Array contíguo único vs 9 objetos deque
- ✅ **Código:** 50 linhas vs 100+ linhas
- ✅ **Compatibilidade 100%:** `buffer.ax`, `buffer.contador[-1]`, `len(buffer.ax)` funcionam igual

---

### 3. [[janela]] — **AJUSTES DE PERFORMANCE (Opcional)**

```python
# Linhas 24-28: Reduzido FPS para diminuir lock contention
INTERVALO_GRAFICO_MS = 200      # Era 100ms (10 FPS) → Agora 200ms (5 FPS)
INTERVALO_ESTATISTICAS_MS = 500 # Mantido
PONTOS_GRAFICO = 250            # Era 500 → Agora 250 (menos dados por frame)
```


**Impacto:** Reduz contenção de Lock entre thread de aquisição e thread UI.

> **Observação posterior importante:** durante os testes a 200 Hz, foi constatado que o **auto-scroll** da janela era um dos principais responsáveis pelas perdas. A cada atualização ele deslocava/recalculava a visualização do gráfico; esse trabalho consumia tanto a thread da interface que ela passava a disputar recursos com a aquisição. O resultado eram travamentos e saltos no contador (amostras perdidas). Por isso o auto-scroll contínuo foi removido: o eixo X permanece estático e a atualização desenha apenas os dados já disponíveis.

Altas taxas de atualização da interface podem provocar perdas por atraso entre threads. A configuração atual é 33 ms (~30 FPS) e 150 pontos, sem auto-scroll contínuo; ela deve ser validada junto da taxa de aquisição desejada.


---

### 4. `arduino/mpu-6050/mpu-6050.ino` — **CONFIGURAÇÃO RELACIONADA**

```cpp
// Linha 13: Baud rate do Arduino
Serial.begin(115200);  // DEVE coincidir com Python

// Linha 20: Delay desnecessário no setup (remove para iniciar mais rápido)
// delay(10000);  // REMOVER OU COMENTAR
```

**Importante:** Python estava configurado para 230400 baud em versões antigas, mas Arduino usa 115200. Isso causava lixo no buffer serial. Isso que o python tem problemas com taxas maiores que 115200

---

## Cronologia da Descoberta

| Passo | Ação | Resultado |
|-------|------|-----------|
| 1 | Executar `teste_manager.py` | Funcionava: 0 saltos, Hz ~215 |
| 2 | Executar `janela.py` | Pulava amostras visualmente |
| 3 | Verificar CSV gerado | Saltos no contador, Hz caía |
| 4 | Testar serial direto (`pyserial`) | Arduino enviava 211 Hz contínuo |
| 5 | Identificar diferença: `teste_manager` só lê `buffer.contador[-1]`; `janela` chama `buffer.snapshot(500)` a cada 100ms |
| 6 | Suspeitar de Lock contention → otimizar `buffers.py` com NumPy |
| 7 | **Descobrir o bug real:** `serial_reader.py` modificado usava `in_waiting + read()` quebrando linhas |
| 8 | Restaurar `serial_reader.py` original com `readline()` |
| 9 | Testar novamente: **0 saltos, 0 perdidas, Hz estável 215** |

---

## Evidências dos Testes

### Antes da Correção (serial_reader quebrado)
```
[Coletor] Salto no contador: 502 -> 510 (7 amostras perdidas)
[Coletor] Salto no contador: 514 -> 516 (1 amostras perdidas)
[Serial] Linha inválida: '520,12409020,1.00,0.01,0.02,-3.29,0.24,-'
T:  14.0s | Buffer:    11/10000 | Contador:     519 | Hz: 113.04 | Saltos: 3 | Perdidas: 9
T:  16.0s | Buffer:    20/10000 | Contador:     815 | Hz:  12.98 | Saltos: 2 | Perdidas: 296
```

### Após Correção (serial_reader original + buffers otimizado)
```
Contador: 88 | Amostras: 88 | Hz: 217.19 | Saltos: 0 | Perdidas: 0
Contador: 301 | Amostras: 301 | Hz: 215.39 | Saltos: 0 | Perdidas: 0
Contador: 515 | Amostras: 515 | Hz: 215.04 | Saltos: 0 | Perdidas: 0
Contador: 728 | Amostras: 728 | Hz: 214.87 | Saltos: 0 | Perdidas: 0
```

---

## Lições Aprendidas

1. **Nunca substitua `readline()` por `in_waiting + read()`** para protocolos baseados em linha (CSV, JSON lines, etc.)
   - `readline()` garante linha completa
   - `read()` pode retornar dados parciais

2. **`readline()` com timeout é a abordagem correta** para serial assíncrono:
   ```python
   with serial.Serial(porta, baudrate, timeout=0.1) as ser:
       linha = ser.readline().decode('utf-8', errors='ignore').strip()
   ```

3. **Buffer circular com NumPy** é excelente para performance, mas **não substitui leitura serial correta**

4. **Teste isolado da serial** (`pyserial` direto) é essencial para separar problemas de hardware/Arduino de problemas de software/Python

---

## Checklist para Evitar Regressão

- [ ] `serial_reader.py` usa `readline()` (não `in_waiting + read`)
- [ ] `serial_reader.py` timeout ≥ 0.1s
- [ ] Baud rate Python = Baud rate Arduino (115200)
- [ ] Arduino sem `delay()` longo no `setup()`
- [ ] `buffers.py` usa NumPy array 2D com propriedades de compatibilidade
- [ ] `janela.py` FPS ≤ 10 (recomendado 5 FPS = 200ms)
- [ ] CSV gerado sem saltos no contador

---

## Comandos de Teste Rápido

```bash
# 1. Testar serial direto (deve dar ~210 Hz contínuo)
python -c "
import serial, time
with serial.Serial('COM4', 115200, timeout=1) as s:
    time.sleep(12)  # esperar delay Arduino
    s.reset_input_buffer()
    t=time.time(); c=0
    while time.time()-t<10:
        l=s.readline().decode().strip()
        if l: c+=1
    print(f'{c/10:.1f} Hz')
"

# 2. Testar sistema completo (teste_manager)
python -m sensor.teste_manager

# 3. Verificar CSV gerado
python -c "
import glob, os
f=max(glob.glob('dados/dados_aceleracao_giro-*.csv'), key=os.path.getmtime)
lines=open(f).readlines()
print(f'{len(lines)-1} amostras')
contadores=[int(l.split(\",\")[2]) for l in lines[1:]]
saltos=sum(1 for i in range(1,len(contadores)) if contadores[i]-contadores[i-1]>1)
print(f'Saltos: {saltos}')
"
```

---

## Referências de Código

| Arquivo | Linhas Críticas | Função |
|---------|-----------------|--------|
| [[serial_reader]] | 33-37 | `readline()` loop principal |
| [[buffers]] | 15-45 | `adicionar()` + `snapshot()` NumPy |
| [[buffers]] | 55-85 | Propriedades `ax`, `contador`, etc. |
| [[coletor]] | 92-101 | Loop de aquisição chamando `ler_dados()` |
| [[janela]] | 354-365 | `snapshot()` + `setData()` plot |
| `arduino/mpu-6050/mpu-6050.ino` | 13, 20 | `Serial.begin(115200)` + `delay(10000)` |

---

**Conclusão:** O bug era **exclusivamente no `serial_reader.py`**. A otimização do `buffers.py` com NumPy foi benéfica e mantida. O sistema agora roda estável a ~215 Hz sem perda de amostras.
