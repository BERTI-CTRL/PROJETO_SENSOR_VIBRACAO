# Documentação do Projeto - Sensor de Vibração MPU6050

**Versão:** 1.0  
**Data:** 31/07/2026  
**Projeto:** PROJETO_SENSOR_VIBRACAO  

---

## Visão Geral da Arquitetura

```
┌─────────────┐     Serial (115200 baud)      ┌──────────────────────────────────────┐
│   Arduino   │ ─────────────────────────────▶ │           Python Backend             │
│  (MPU6050)  │  contador, micros(), ax,ay,az, │  ┌────────────────────────────────┐  │
│             │  gx,gy,gz (CSV linha)          │  │ serial_reader.py               │  │
└─────────────┘                                │  │  - readline() + parse CSV      │  │
                                               │  │  - yield (t_arduino, t_pc, ...)│  │
                                               │  └──────────────┬─────────────────┘  │
                                               │             ▼                        │
                                               │  ┌────────────────────────────────┐  │
                                               │  │ coletor.py (Thread)            │  │
                                               │  │  - Consome serial_reader       │  │
                                               │  │  - Detecta saltos no contador  │  │
                                               │  │  - Calcula Hz médio/instant    │  │
                                               │  │  - buffer.adicionar()          │  │
                                               │  │  - fila_gravacao.put()         │  │
                                               │  └──────┬──────────────┬──────────┘  │
                                               │       ▼              ▼              │
                                               │ ┌────────────┐  ┌───────────────┐  │
                                               │ │ buffers.py │  │gravador_worker│  │
                                               │ │ BufferSensores     │  (Thread)     │  │
                                               │ │ (NumPy 2D)       │  GravadorCSV  │  │
                                               │ └────────────┘  └───────────────┘  │
                                               └──────────────┬─────────────────────┘
                                                              ▼
                                               ┌────────────────────────────────┐
                                               │       Interface (PyQt6)        │
                                               │  realtime/janela.py            │
                                               │  - Timer 200ms (5 FPS)         │
                                               │  - buffer.snapshot(250)        │
                                               │  - pyqtgraph PlotWidget        │
                                               └────────────────────────────────┘
```

---

## Fluxo de Dados Completo

### 1. Arduino (`arduino/mpu-6050/mpu-6050.ino`)
- Inicializa MPU6050 via I2C (endereço 0x68)
- Configura: Acelerômetro ±16g, Giroscópio ±2000°/s
- Loop: Lê 14 bytes I2C → converte → envia linha CSV serial
- Formato: `contador,micros(),ax,ay,az,gx,gy,gz\n`
- Baud rate: **115200**
- Taxa real: **~215 Hz**

### 2. Leitura Serial (`sensor/serial_reader.py`)
```python
def ler_dados(porta, baudrate=115200, timeout=0.1):
    with serial.Serial(porta, baudrate, timeout=timeout) as arduino:
        time.sleep(2)           # Reset Arduino
        arduino.reset_input_buffer()
        while True:
            timestamp = time.perf_counter()
            linha = arduino.readline().decode('utf-8', errors='ignore').strip()
            if not linha: continue
            campos = linha.split(",")
            if len(campos) != 8: continue
            contador, t_arduino, ax, ay, az, gx, gy, gz = map(float, campos)
            yield (t_arduino, timestamp, contador, ax, ay, az, gx, gy, gz)
```
- **`readline()`** bloqueia até `\n` → garante linha completa
- **timeout=0.1s** evita travamento
- **errors='ignore'** descarta bytes inválidos
- Retorna **generator** com tuplas tipadas

### 3. Coleta (`sensor/coletor.py` - Thread `coletor-serial`)
```python
def executar(self):
    for t_arduino, t_pc, contador, ax, ay, az, gx, gy, gz in ler_dados(...):
        if not self.rodando: break
        self._registrar_salto(contador)      # Detecta contador não sequencial
        self._calcular_hz(t_arduino)         # Hz médio + instantâneo
        self.buffer.adicionar(...)           # Thread-safe
        self._enfileirar_gravacao([...])     # Non-blocking para CSV
```
- Roda em **thread separada** (daemon)
- Detecta **saltos no contador** → amostras perdidas na serial
- Calcula **Hz médio** (desde início) e **Hz instantâneo** (entre amostras)
- **Non-blocking** para gravação CSV (usa `Queue.put_nowait()`)

### 4. Buffer Circular (`sensor/buffers.py` - `BufferSensores`)
```python
class BufferSensores:
    # Array 2D NumPy: (10000, 9) [t_arduino, t_pc, contador, ax, ay, az, gx, gy, gz]
    def adicionar(self, ...):
        with self._lock:
            self._dados[self._index] = [...]
            self._index = (self._index + 1) % self.tamanho_maximo
            if self._count < self.tamanho_maximo: self._count += 1
    
    def _get_coluna_slice(self, idx):  # WRAP-AROUND CORRETO
        if self._count < self.tamanho_maximo:
            return self._dados[:self._count, idx]
        return np.concatenate([self._dados[self._index:, idx], self._dados[:self._index, idx]])
    
    @property
    def contador(self): return self._get_coluna_slice(2)
    # ... ax, ay, az, gx, gy, gz, t_arduino, t_pc
    
    def snapshot(self, qtd=None):      # Ordem cronológica sempre
        if self._count < self.tamanho_maximo:
            inicio = self._count - qtd
            return {col: self._dados[inicio:self._count, i].copy() ...}
        # Buffer cheio: monta array cronológico antes de fatiar
        dados_cron = np.concatenate([self._dados[self._index:], self._dados[:self._index]])
        return {col: dados_cron[-qtd:, i].copy() ...}
```
- **Array 2D NumPy** único (performance + memória)
- **Thread-safe** com `Lock`
- **Wrap-around correto**: propriedades e `snapshot()` retornam ordem **cronológica** (antigo → novo)
- **Compatível** com código existente: `buffer.ax`, `buffer.contador[-1]`, `len(buffer.ax)`

### 5. Gravação CSV (`sensor/gravador_worker.py` + `sensor/gravador.py`)
```python
class GravadorWorker(Thread):          # Thread daemon 'gravador-csv'
    def run(self):
        gravador = GravadorCSV()
        while True:
            linha = self.fila.get()
            if linha is None: break    # Sentinela de parada
            gravador.salvar(linha)     # Buffer interno 1000 linhas
            self.fila.task_done()

class GravadorCSV:
    def salvar(self, linha):
        self.buffer.append(linha)
        if len(self.buffer) >= self.tamanho_buffer:
            self.writer.writerows(self.buffer)
            self.buffer.clear()
    def fechar(self):                  # Flush final
        if self.buffer: self.writer.writerows(self.buffer)
        self.f.close()
```
- **Thread dedicada** → nunca bloqueia aquisição serial
- **Batch write** (1000 linhas) → performance de disco
- **Arquivo único por sessão**: `dados/dados_aceleracao_giro-YYYY-MM-DD_HH-MM-SS.csv`

### 6. Gerenciador (`sensor/manager.py` - `SensorManager`)
```python
class SensorManager:
    def iniciar(self):
        self.fila_gravacao = Queue(maxsize=50_000)
        self.coletor.configurar_fila_gravacao(self.fila_gravacao)
        self.gravador_thread = GravadorWorker(self.fila_gravacao)
        self.gravador_thread.start()
        self.thread = Thread(target=self.coletor.executar, name="coletor-serial", daemon=True)
        self.thread.start()
    
    def parar(self):
        self.coletor.parar()
        self.thread.join()
        self.fila_gravacao.put(None)    # Sentinela
        self.gravador_thread.join()
```
- **Facade** para iniciar/parar todo o pipeline
- Instância global: `manager = SensorManager()`

### 7. Interface PyQt (`realtime/janela.py` - `Janela`)
```python
class Janela(QMainWindow):
    INTERVALO_GRAFICO_MS = 200    # 5 FPS
    PONTOS_GRAFICO = 250          # Pontos por frame
    
    def criar_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_grafico)
        self.timer.timeout.connect(self.atualizar_estatisticas)
        self.timer.start(INTERVALO_GRAFICO_MS)
    
    def atualizar_grafico(self):
        if self.manager.buffer.vazio(): return
        dados = self.manager.buffer.snapshot(PONTOS_GRAFICO)
        contadores = np.arange(len(dados['contador']))  # 0,1,2... (relativo)
        if self.checkbox_ax.isChecked():
            self.curva_ax.setData(contadores, np.asarray(dados["ax"]), skipFiniteCheck=True)
        # ... ay, az, gx, gy, gz
    
    def atualizar_estatisticas(self):
        self.label_hz_medio.setText(f"Hz Médio: {self.manager.coletor.hz_medio:.2f}")
        self.label_hz_instantaneo.setText(f"Hz Inst: {self.manager.coletor.hz_inst:.2f}")
        self.label_amostras.setText(f"Amostras: {self.manager.coletor.numero_amostras}")
        # Estatísticas Ax via utils.statistics.calcular_estatisticas()
```
- **5 FPS** (200ms) → balanceia fluidez vs CPU
- **250 pontos** por frame → janela ~1.2s a 215 Hz
- **Eixo X relativo** (0..249) → evita "pulo" visual do contador absoluto
- **pyqtgraph** → rendering GPU acelerado

---

## Estrutura de Diretórios

```
PROJETO_SENSOR_VIBRACAO/
├── arduino/
│   └── mpu-6050/
│       └── mpu-6050.ino          # Firmware Arduino
├── sensor/
│   ├── __init__.py
│   ├── serial_reader.py          # Leitura serial (generator)
│   ├── coletor.py                # Thread de aquisição
│   ├── buffers.py                # Buffer circular NumPy (thread-safe)
│   ├── gravador.py               # CSV writer com batch
│   ├── gravador_worker.py        # Thread de gravação
│   ├── manager.py                # Facade SensorManager
│   └── teste_manager.py          # Teste CLI simples
├── realtime/
│   ├── __init__.py
│   ├── janela.py                 # UI PyQt6 principal
│   ├── main.py                   # Entry point UI
│   └── gráfico.py                # UI alternativa simples
├── utils/
│   └── statistics.py             # Estatísticas descritivas (NumPy)
├── pages/                        # Streamlit pages (docs/dashboard)
├── dados/                        # CSVs gerados (gitignored)
├── assets/                       # Imagens/GIFs
├── ERROS/                        # Documentação de bugs corrigidos
├── DOCS/                         # ESTA DOCUMENTAÇÃO
├── home.py                       # Streamlit home
├── pyproject.toml                # Dependências
└── README.md
```

---

## Dependências Principais (`pyproject.toml`)

| Pacote | Versão | Uso |
|--------|--------|-----|
| `pyserial` | ≥3.5 | Comunicação serial Arduino |
| `numpy` | ≥2.4.6 | Arrays, matemática, buffer |
| `pyqt6` | ≥6.11 | Interface gráfica |
| `pyqtgraph` | ≥0.14 | Gráficos tempo real performáticos |
| `pandas` | ≥3.0 | Análise de dados (futuro) |
| `streamlit` | ≥1.57 | Dashboard web (páginas) |

---

## Como Executar

### Interface PyQt (Tempo Real)
```bash
# Ativar venv
.\.venv\Scripts\activate

# Executar janela principal
python -m realtime.main
```

### Teste CLI (Sem UI)
```bash
python -m sensor.teste_manager
# Ctrl+C para parar
```

### Streamlit Dashboard
```bash
streamlit run home.py
```

---

## Configuração do Arduino

1. Carregar `arduino/mpu-6050/mpu-6050.ino` no Arduino IDE
2. Verificar: **Tools > Port** = COM correto (ex: COM4)
3. Verificar: **Tools > Board** = Arduino Uno/Nano
4. **Baud rate no código**: `Serial.begin(115200)` → deve coincidir com Python
5. **Remover/Comentar** `delay(10000)` no `setup()` para início imediato

---

## Problemas Conhecidos e Correções

| Problema | Arquivo | Documentação |
|----------|---------|--------------|
| Pulando amostras na serial | `serial_reader.py` | [[correcao-pulos-amostras-serial]] |
| Buffer congelando após 10k | `buffers.py` | [[correcao-buffer-congelando-wrap-around]] |

> **Regra:** Sempre que alterar um script, atualize a documentação correspondente em `DOCS/` e `ERROS/` se for bug fix.

---

## Métricas de Performance

| Métrica | Valor | Observação |
|---------|-------|------------|
| Taxa aquisição | ~215 Hz | Limitado por I2C + Serial |
| Buffer circular | 10.000 amostras | ~46s de histórico |
| FPS interface | 5 FPS (200ms) | Configurável em `janela.py` |
| Pontos/frame | 250 | ~1.16s de janela visual |
| Batch CSV | 1.000 linhas | Escrita assíncrona |
| Fila gravação | 50.000 itens | Buffer de pico |
| Uso CPU (UI) | ~2-5% | pyqtgraph otimizado |
| Uso RAM | ~50 MB | Buffer + arrays NumPy |

---

## Próximos Passos / Roadmap

- [ ] FFT em tempo real (análise frequência)
- [ ] Detecção de anomalias (IA)
- [ ] Múltiplos sensores (sincronização)
- [ ] Calibração automática offsets
- [ ] Exportação de relatórios PDF
- [ ] Dashboard Streamlit completo