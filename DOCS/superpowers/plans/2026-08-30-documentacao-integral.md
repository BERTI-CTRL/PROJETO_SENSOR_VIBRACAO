# Documentação integral do projeto - plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Documentar integralmente o estado atual do projeto, comentar didaticamente todos os scripts, conectar as notas por wikilinks e criar canvases dos fluxos essenciais.

**Architecture:** A documentação será uma base Obsidian centrada em `DOCS/INDEX.md`, com uma nota por script e notas transversais para contratos compartilhados. Os comentários ficarão junto do código que explicam; os arquivos `.canvas` referenciarão as notas em vez de duplicar explicações extensas.

**Tech Stack:** Markdown com wikilinks do Obsidian, JSON Canvas, Python 3.11+, Arduino/C++, PyQt6, PyQtGraph, NumPy, pandas, Plotly e PySerial.

**Spec:** `DOCS/superpowers/specs/2026-08-30-documentacao-integral-design.md`

## Global Constraints

- A fonte de verdade é o working tree de 30 de agosto de 2026, incluindo alterações preexistentes em `sensor/coletor.py` e `sensor/serial_reader.py`.
- Não alterar comportamento, interfaces, constantes, algoritmos ou dados existentes.
- Não sobrescrever nem reverter alterações locais do usuário.
- Comentar toda instrução significativa; não comentar linhas vazias ou fechamentos puramente sintáticos.
- Usar wikilinks no corpo dos Markdown sempre que uma nota depender ou consumir outra.
- Fundamentar a nota InvenSense somente nos dois PDFs locais e somente nos assuntos usados ou relevantes ao projeto.
- Não modificar os PDFs nem os CSVs existentes.
- Não criar commits de implementação automaticamente enquanto os scripts do usuário estiverem modificados; usar diffs e verificações como checkpoints.

---

### Task 1: Baseline de preservação e inventário de cobertura

**Files:**
- Read: todos os arquivos `*.py` e `*.ino`
- Read: `pyproject.toml`, `.gitignore`, `sensor/arq.txt`
- Read: todos os arquivos em `DOCS/` e `ERROS/`
- Temporary baseline: `tmp/documentacao-baseline/`

**Interfaces:**
- Consumes: working tree aprovado na especificação.
- Produces: cópia de comparação e inventário fechado de 17 fontes (`16 .py`, incluindo dois inicializadores de pacote, e `1 .ino`).

- [ ] **Step 1: Confirmar arquivos e alterações preexistentes**

Run:

```powershell
rg --files -g '*.py' -g '*.ino'
git status --short
git diff -- sensor/coletor.py sensor/serial_reader.py
```

Expected: os scripts listados no inventário; somente as alterações já conhecidas e os CSVs do usuário antes dos novos edits.

- [ ] **Step 2: Criar uma cópia temporária dos scripts**

Run:

```powershell
New-Item -ItemType Directory -Force -Path 'tmp/documentacao-baseline' | Out-Null
$arquivos = rg --files -g '*.py' -g '*.ino'
foreach ($arquivo in $arquivos) {
    $destino = Join-Path 'tmp/documentacao-baseline' $arquivo
    New-Item -ItemType Directory -Force -Path (Split-Path $destino) | Out-Null
    Copy-Item -LiteralPath $arquivo -Destination $destino
}
```

Expected: uma cópia com a mesma estrutura relativa e sem editar os originais.

- [ ] **Step 3: Registrar a cobertura documental desejada**

Mapear explicitamente:

```text
sensor/serial_reader.py       -> DOCS/serial_reader.md
sensor/coletor.py             -> DOCS/coletor.md
sensor/buffers.py             -> DOCS/buffers.md
sensor/gravador.py            -> DOCS/gravador.md
sensor/gravador_worker.py     -> DOCS/gravador_worker.md
sensor/manager.py             -> DOCS/manager.md
sensor/teste_manager.py       -> DOCS/teste_manager.md
sensor/__init__.py            -> DOCS/estrutura-do-projeto.md
realtime/main.py              -> DOCS/main.md
realtime/janela.py            -> DOCS/janela.md
realtime/gráfico.py           -> DOCS/grafico.md
realtime/__init__.py          -> DOCS/estrutura-do-projeto.md
utils/statistics.py           -> DOCS/statistics.md
grafico/plotar_csv.py         -> DOCS/plotar_csv.md
dados/testar_dados.py         -> DOCS/testar_dados.md
calibração/calibrar_vibracao.py -> DOCS/calibrar_vibracao.md
arduino/mpu-6050/mpu-6050.ino -> DOCS/arduino_mpu6050.md
```

- [ ] **Step 4: Checkpoint**

Run: `git status --short`

Expected: somente `tmp/` novo além do estado preexistente; nenhuma fonte modificada nesta tarefa.

---

### Task 2: Aquisição serial, frequência e buffer circular

**Files:**
- Modify: `sensor/serial_reader.py`
- Modify: `sensor/coletor.py`
- Modify: `sensor/buffers.py`
- Modify: `DOCS/serial_reader.md`
- Modify: `DOCS/coletor.md`
- Modify: `DOCS/buffers.md`
- Create: `DOCS/protocolo-serial.md`
- Create: `DOCS/tempo-frequencia-e-perdas.md`

**Interfaces:**
- Consumes: linha serial `contador,tempo_arduino_us,ax,ay,az,gx,gy,gz` produzida pelo firmware.
- Produces: tupla de nove valores de `ler_dados()`, métricas do `Coletor` e snapshots do `BufferSensores` consumidos por `[[manager]]`, `[[janela]]` e `[[esquema-csv]]`.

- [ ] **Step 1: Comentar `serial_reader.py` instrução por instrução**

Explicar junto do código: mensagem executada no import, imports, callback `deve_continuar`, context manager da serial, espera após reset, `reset_input_buffer`, timestamp do PC, `readline`, decodificação tolerante, oito campos, conversão numérica, ordem da tupla, contador de linhas inválidas, gerador fake e execução direta. Identificar que o `__main__` usa 115200 enquanto o parâmetro padrão usa 230400, sem alterar nenhum valor.

- [ ] **Step 2: Atualizar `[[serial_reader]]` e criar `[[protocolo-serial]]`**

Incluir assinatura exata, protocolo de parada, efeitos do timeout, tabela dos oito campos, diferença entre linha serial e linha CSV, relação com `[[arduino_mpu6050]]`, `[[coletor]]` e `[[correcao-pulos-amostras-serial]]`.

- [ ] **Step 3: Comentar `coletor.py` instrução por instrução**

Explicar estado da sessão, detecção de saltos, fila não bloqueante, reinicialização de métricas, cálculo de `hz_medio`, `hz_inst`, média móvel de 100 valores, escrita no buffer e enfileiramento para CSV. Preservar exatamente as alterações locais existentes.

- [ ] **Step 4: Atualizar `[[coletor]]` e criar `[[tempo-frequencia-e-perdas]]`**

Documentar as três noções de frequência, por que `micros()` é preferido ao instante de leitura no PC, como saltos são contados e a diferença entre perda na serial e perda por fila cheia.

- [ ] **Step 5: Comentar `buffers.py` instrução por instrução**

Explicar as nove colunas, `float64`, `_index`, `_count`, exclusão mútua, escrita circular, snapshots parciais, dois ramos de wrap-around, cópias entregues à UI, limpeza e propriedades de compatibilidade.

- [ ] **Step 6: Atualizar `[[buffers]]`**

Conectar o buffer a `[[coletor]]`, `[[janela]]`, `[[statistics]]` e `[[correcao-buffer-congelando-wrap-around]]`; distinguir histórico completo no CSV de janela limitada na memória.

- [ ] **Step 7: Verificar sintaxe da aquisição**

Run:

```powershell
python -m py_compile sensor/serial_reader.py sensor/coletor.py sensor/buffers.py
```

Expected: exit code 0, sem abrir COM4.

---

### Task 3: Persistência assíncrona e ciclo de vida

**Files:**
- Modify: `sensor/gravador.py`
- Modify: `sensor/gravador_worker.py`
- Modify: `sensor/manager.py`
- Modify: `sensor/teste_manager.py`
- Modify: `sensor/__init__.py`
- Modify: `DOCS/gravador.md`
- Modify: `DOCS/gravador_worker.md`
- Modify: `DOCS/manager.md`
- Create: `DOCS/teste_manager.md`
- Create: `DOCS/esquema-csv.md`
- Create: `DOCS/threads-e-encerramento.md`

**Interfaces:**
- Consumes: linhas de nove valores enfileiradas pelo `Coletor` e sentinela `None` enviada pelo `SensorManager`.
- Produces: CSV com cabeçalho estável e fechamento/flush garantido ao encerrar uma sessão normal.

- [ ] **Step 1: Comentar `gravador.py` e atualizar `[[gravador]]`**

Explicar nome datado do arquivo, parâmetro `arquivo` atualmente não utilizado para escolher o destino, append, cabeçalho, buffer em memória, escrita em lote e flush final. Não corrigir o parâmetro ignorado; registrá-lo como consideração de modificação.

- [ ] **Step 2: Comentar `gravador_worker.py` e atualizar `[[gravador_worker]]`**

Explicar herança de `Thread`, daemon, bloqueio seguro em `Queue.get`, `task_done`, sentinela `None`, armazenamento de exceção e fechamento no `finally`.

- [ ] **Step 3: Comentar `manager.py` e atualizar `[[manager]]`**

Explicar singleton prático, prevenção de início duplicado, fila de 50.000 itens, ordem de inicialização, `join`, sentinela, limpeza das referências e retorno booleano de `parar()`.

- [ ] **Step 4: Comentar `teste_manager.py`, `sensor/__init__.py` e criar `[[teste_manager]]`**

Explicar que o teste inicia aquisição ao importar/executar o módulo, mostra o último contador a cada segundo e depende de `KeyboardInterrupt` para encerrar. Diferenciá-lo explicitamente de `[[testar_dados]]`.

- [ ] **Step 5: Criar `[[esquema-csv]]`**

Incluir tabela com as nove colunas exatas, tipo conceitual, unidade, origem e consumidores. Registrar que `tempo_relogio_pc` vem de `time.perf_counter()`, que o CSV usa vírgula e que temperatura é lida pelo firmware mas não transmitida.

- [ ] **Step 6: Criar `[[threads-e-encerramento]]`**

Descrever três contextos: event loop da GUI, thread `coletor-serial` e thread `gravador-csv`. Mostrar a sequência `parar flag -> join coletor -> put(None) -> join gravador -> flush/close` e relacionar `[[correcao-controles-parada-e-i2c]]`.

- [ ] **Step 7: Verificar sintaxe da persistência**

Run:

```powershell
python -m py_compile sensor/gravador.py sensor/gravador_worker.py sensor/manager.py sensor/teste_manager.py sensor/__init__.py
```

Expected: exit code 0; não executar `sensor.teste_manager` porque ele abriria a aquisição.

---

### Task 4: Interface em tempo real e estatísticas

**Files:**
- Modify: `realtime/main.py`
- Modify: `realtime/janela.py`
- Modify: `realtime/gráfico.py`
- Modify: `realtime/__init__.py`
- Modify: `utils/statistics.py`
- Modify: `DOCS/main.md`
- Modify: `DOCS/janela.md`
- Modify: `DOCS/grafico.md`
- Modify: `DOCS/statistics.md`

**Interfaces:**
- Consumes: snapshots de `manager.buffer` e métricas públicas de `manager.coletor`.
- Produces: visualização PyQt/PyQtGraph, estatísticas por eixo e abertura opcional do Plotly após uma coleta encerrada.

- [ ] **Step 1: Comentar `main.py` e `realtime/__init__.py`**

Explicar criação única de `QApplication`, construção/exibição de `Janela`, event loop e guarda `__main__`.

- [ ] **Step 2: Comentar `janela.py` por blocos e instruções significativas**

Cobrir imports, configuração global do PyQtGraph, constantes de FPS/pontos/escalas, criação dos widgets, dois gráficos e seis curvas, checkboxes, labels, botões, timers independentes, iniciar/parar, snapshot único, reaproveitamento do eixo X, autoescala, estatísticas, limpeza e `closeEvent`. Registrar o import duplicado de `pyqtgraph` como observação sem removê-lo.

- [ ] **Step 3: Atualizar `[[main]]` e `[[janela]]`**

Explicar os 30 FPS do gráfico versus os 2 FPS das estatísticas, janela de 150 amostras, escalas separadas, ausência de histórico completo na GUI e fluxo que chama `[[plotar_csv]]` após parar.

- [ ] **Step 4: Comentar `gráfico.py` e atualizar `[[grafico]]`**

Explicar que é uma interface mínima de depuração para `ax`, com timer próprio e encerramento pelo manager, não substituta da janela principal.

- [ ] **Step 5: Comentar `statistics.py` e atualizar `[[statistics]]`**

Explicar dataclass imutável, conversão do iterável, máscara de finitos, contagem de inválidos, média, desvio com `ddof`, RMS, pico, pico a pico, fator de crista e resultado indefinido.

- [ ] **Step 6: Verificar sintaxe sem abrir a GUI**

Run:

```powershell
python -m py_compile realtime/main.py realtime/janela.py realtime/gráfico.py realtime/__init__.py utils/statistics.py
```

Expected: exit code 0.

---

### Task 5: Pós-processamento, validação e calibração

**Files:**
- Modify: `grafico/plotar_csv.py`
- Modify: `dados/testar_dados.py`
- Modify: `calibração/calibrar_vibracao.py`
- Modify: `DOCS/plotar_csv.md`
- Replace content: `DOCS/testar_dados.md`
- Modify: `DOCS/calibrar_vibracao.md`
- Modify: `calibração/guia_calibracao_mpu6050.md`
- Create: `DOCS/dependencias.md`
- Create: `DOCS/guia-de-modificacao.md`

**Interfaces:**
- Consumes: CSVs no contrato de `[[esquema-csv]]`.
- Produces: gráfico Plotly, relatório de consistência no terminal e JSON `calibracao_vibracao_<eixo>.json`.

- [ ] **Step 1: Comentar `plotar_csv.py` e atualizar `[[plotar_csv]]`**

Explicar descoberta do CSV mais recente, resolução de caminho, validação de colunas, dois subplots, contador como eixo X, abertura no navegador e CLI.

- [ ] **Step 2: Comentar `dados/testar_dados.py` e reescrever `[[testar_dados]]`**

Explicar leitura manual, contrato do cabeçalho, conversão para NumPy, saltos, Hz, faixas físicas, monotonicidade do PC, NaN/Inf, condição final de sucesso e códigos de saída. A nota passa a representar corretamente este arquivo.

- [ ] **Step 3: Comentar `calibrar_vibracao.py` e atualizar `[[calibrar_vibracao]]`**

Explicar escolha do CSV, descarte inicial, baseline, RMS do componente alternado, ganho, estimativa de perdas, JSON e validação dos argumentos.

- [ ] **Step 4: Atualizar o guia de calibração**

Adicionar wikilinks no corpo para `[[invensense-pontos-utilizados]]`, `[[esquema-csv]]`, `[[tempo-frequencia-e-perdas]]`, `[[testar_dados]]` e `[[calibrar_vibracao]]`; preservar explicações experimentais já válidas.

- [ ] **Step 5: Criar `[[dependencias]]`**

Mapear cada dependência de `pyproject.toml` para os scripts que a utilizam. Identificar bibliotecas declaradas sem uso encontrado no código atual como dependências possivelmente históricas, sem removê-las.

- [ ] **Step 6: Criar `[[guia-de-modificacao]]`**

Incluir roteiros específicos para alterar porta/baud rate, protocolo, escalas do sensor, taxa/filtro, tamanho de buffer, taxa da interface, estatísticas, CSV e calibração. Para cada alteração, listar arquivos acoplados e verificações necessárias.

- [ ] **Step 7: Verificar sintaxe e cálculos sem interface**

Run:

```powershell
python -m py_compile grafico/plotar_csv.py dados/testar_dados.py calibração/calibrar_vibracao.py
python -c "from utils.statistics import calcular_estatisticas; r=calcular_estatisticas([1,2,3]); assert r.quantidade_validas == 3"
```

Expected: exit code 0.

---

### Task 6: Firmware Arduino e síntese da InvenSense

**Files:**
- Modify: `arduino/mpu-6050/mpu-6050.ino`
- Modify: `DOCS/arduino_mpu6050.md`
- Create: `DOCS/invensense-pontos-utilizados.md`
- Read: `arduino/MPU-6000-Register-Map1 (1).pdf`
- Read: `arduino/mpu-6050_datasheet_v3 4.pdf`

**Interfaces:**
- Consumes: registradores e escalas definidos pela InvenSense.
- Produces: linha serial de oito campos consumida por `[[serial_reader]]` e interpretação física usada por `[[calibrar_vibracao]]`.

- [ ] **Step 1: Comentar o firmware instrução por instrução**

Explicar `Wire`, endereço `0x68`, contador, tipos, `setup`, teste I2C, atraso de 10 segundos, `PWR_MGMT_1`, `GYRO_CONFIG`, `ACCEL_CONFIG`, repeated start, leitura de 14 bytes, descarte implícito da temperatura, composição dos valores, sensibilidades e serialização.

- [ ] **Step 2: Atualizar `[[arduino_mpu6050]]`**

Alinhar baud rates e campos com o código atual, indicar divergências entre 115200 no firmware e 230400 em partes do Python, documentar o que está configurado e o que usa valor de reset.

- [ ] **Step 3: Criar `[[invensense-pontos-utilizados]]` a partir do mapa de registradores**

Usar e citar: mapa nas páginas 6–7; `SMPLRT_DIV` nas páginas 11–12; `CONFIG/DLPF` na página 13; `GYRO_CONFIG` na página 14; `ACCEL_CONFIG` na página 15; medições nas páginas 29–31; `PWR_MGMT_1` na página 40.

- [ ] **Step 4: Completar a nota a partir da especificação do produto**

Usar e citar: giroscópio na página 12; acelerômetro na página 13; I2C fast mode na página 18; pinos e `AD0` na página 21; princípios de medição e interface I2C na página 25. Explicar tolerância, offset, cross-axis, ruído e largura de banda apenas na medida em que afetam calibração e interpretação.

- [ ] **Step 5: Delimitar assuntos não usados**

Declarar que DMP, FIFO, interrupções, sensores auxiliares, self-test e temperatura não integram o pipeline atual; citar apenas quando necessário para evitar interpretação errada do código.

- [ ] **Step 6: Verificar preservação do firmware**

Comparar `arduino/mpu-6050/mpu-6050.ino` com a cópia em `tmp/documentacao-baseline/`, conferindo no diff que somente comentários e espaços mudaram.

---

### Task 7: Arquitetura, índice e navegação completa

**Files:**
- Modify: `README.md`
- Modify: `DOCS/INDEX.md`
- Modify: `DOCS/ARQUITETURA.md`
- Create: `DOCS/estrutura-do-projeto.md`
- Modify: `sensor/arq.txt`
- Modify: documentos em `ERROS/` somente para corrigir/adicionar wikilinks e marcar contexto histórico

**Interfaces:**
- Consumes: todas as notas técnicas das Tasks 2–6.
- Produces: caminho de leitura progressivo e mapa completo para manutenção.

- [ ] **Step 1: Atualizar `README.md`**

Manter a introdução executável e adicionar links de entrada para `[[INDEX]]`, `[[ARQUITETURA]]`, `[[guia-de-modificacao]]`, `[[invensense-pontos-utilizados]]` e canvases. Atualizar comandos, fluxo e estrutura conforme o working tree.

- [ ] **Step 2: Reescrever `DOCS/INDEX.md` como índice exaustivo**

Separar: comece aqui, aquisição, persistência, interface, pós-processamento, hardware, guias transversais, canvases e histórico de erros. Incluir todo script e eliminar a associação incorreta entre `testar_dados` e `sensor/teste_manager.py`.

- [ ] **Step 3: Atualizar `DOCS/ARQUITETURA.md`**

Descrever o pipeline `MPU-6050 -> firmware -> serial -> leitor -> coletor -> buffer/fila -> GUI/CSV -> validação/Plotly/calibração`, com contratos e limites de cada fronteira.

- [ ] **Step 4: Criar `[[estrutura-do-projeto]]` e atualizar `sensor/arq.txt`**

Explicar todos os diretórios importantes, os inicializadores, PDFs, CSVs, `pyproject.toml`, `.python-version`, `.gitignore`, arquivos gerados e a função histórica de `sensor/arq.txt`. Atualizar a árvore textual sem torná-la uma fonte concorrente ao índice.

- [ ] **Step 5: Integrar `ERROS/`**

Adicionar wikilinks para as notas técnicas atuais e avisos de que blocos de código/linhas descritos nesses documentos podem representar versões anteriores.

- [ ] **Step 6: Checkpoint de navegação manual**

Partindo de `DOCS/INDEX.md`, confirmar que cada script, tópico transversal, erro histórico e canvas é alcançável em no máximo dois saltos.

---

### Task 8: Canvases dos fluxos principais

**Files:**
- Create: `CANVASES/visao-geral-projeto.canvas`
- Create: `CANVASES/fluxo-aquisicao-dados.canvas`
- Create: `CANVASES/threads-e-encerramento.canvas`
- Create: `CANVASES/analise-e-calibracao.canvas`

**Interfaces:**
- Consumes: caminhos e contratos das notas concluídas.
- Produces: quatro JSON Canvas válidos, ligados a arquivos Markdown reais.

- [ ] **Step 1: Criar canvas de visão geral**

Nós mínimos: MPU-6050, firmware, serial reader, coletor, buffer, fila/worker, CSV, janela, Plotly, teste e calibração. Arestas dirigidas devem informar “lê registradores”, “envia 8 campos”, “produz 9 valores”, “mantém janela”, “persiste” e “analisa”.

- [ ] **Step 2: Criar canvas de aquisição**

Mostrar registradores `0x3B..0x48`, composição `int16`, divisão por `2048`/`16.4`, CSV serial, parser, timestamps, frequência, contador e destinos buffer/fila.

- [ ] **Step 3: Criar canvas de threads e encerramento**

Separar event loop, `coletor-serial` e `gravador-csv`; mostrar `Queue(maxsize=50_000)`, flag `rodando`, dois `join()` e sentinela `None`.

- [ ] **Step 4: Criar canvas de análise e calibração**

Mostrar CSV como fonte comum, ramificando para teste de consistência, Plotly e calibração; terminar em relatório, navegador e JSON de ganho/offset.

- [ ] **Step 5: Validar JSON e referências**

Run:

```powershell
Get-ChildItem CANVASES -Filter *.canvas | ForEach-Object {
    $canvas = Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json
    if (-not $canvas.nodes -or -not $canvas.edges) { throw "Canvas incompleto: $($_.Name)" }
    $canvas.nodes | Where-Object type -eq 'file' | ForEach-Object {
        if (-not (Test-Path -LiteralPath $_.file)) { throw "Arquivo ausente no canvas: $($_.file)" }
    }
}
```

Expected: nenhum erro de JSON, estrutura ou caminho.

---

### Task 9: Verificação final de cobertura e preservação funcional

**Files:**
- Verify: todos os `*.py`, `*.ino`, `*.md` e `*.canvas`
- Remove after verification: `tmp/documentacao-baseline/`

**Interfaces:**
- Consumes: toda a entrega documental.
- Produces: evidência de sintaxe válida, links resolvidos, cobertura total e nenhuma alteração funcional.

- [ ] **Step 1: Compilar todos os scripts Python**

Run:

```powershell
python -m compileall -q sensor realtime utils grafico dados calibração
```

Expected: exit code 0.

- [ ] **Step 2: Comparar a AST Python com o baseline**

Run:

```powershell
$codigoAst = @'
import ast
from pathlib import Path

class SemDocstrings(ast.NodeTransformer):
    def _limpar(self, no):
        self.generic_visit(no)
        if no.body and isinstance(no.body[0], ast.Expr):
            valor = no.body[0].value
            if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
                no.body.pop(0)
        return no

    visit_Module = _limpar
    visit_ClassDef = _limpar
    visit_FunctionDef = _limpar
    visit_AsyncFunctionDef = _limpar

raiz = Path('.')
baseline = raiz / 'tmp' / 'documentacao-baseline'
falhas = []
for original in sorted(baseline.rglob('*.py')):
    relativo = original.relative_to(baseline)
    atual = raiz / relativo
    arvore_original = SemDocstrings().visit(ast.parse(original.read_text(encoding='utf-8-sig')))
    arvore_atual = SemDocstrings().visit(ast.parse(atual.read_text(encoding='utf-8-sig')))
    if ast.dump(arvore_original, include_attributes=False) != ast.dump(arvore_atual, include_attributes=False):
        falhas.append(str(relativo))
if falhas:
    raise SystemExit('AST funcional alterada: ' + ', '.join(falhas))
print('AST funcional preservada em todos os arquivos Python.')
'@
python -c $codigoAst
```

Expected: `AST funcional preservada em todos os arquivos Python.`

- [ ] **Step 3: Comparar o firmware com o baseline**

Run:

```powershell
$codigoIno = @'
import re
from pathlib import Path

def normalizar(caminho):
    texto = Path(caminho).read_text(encoding='utf-8-sig')
    sem_comentarios = re.sub(r'/\*.*?\*/|//[^\n]*', '', texto, flags=re.S)
    return re.sub(r'\s+', ' ', sem_comentarios).strip()

original = normalizar('tmp/documentacao-baseline/arduino/mpu-6050/mpu-6050.ino')
atual = normalizar('arduino/mpu-6050/mpu-6050.ino')
if original != atual:
    raise SystemExit('Conteúdo funcional do firmware foi alterado.')
print('Conteúdo funcional do firmware preservado.')
'@
python -c $codigoIno
```

Expected: `Conteúdo funcional do firmware preservado.`

- [ ] **Step 4: Verificar cobertura dos scripts**

Run:

```powershell
$cobertura = @{
    'sensor/serial_reader.py'='DOCS/serial_reader.md'; 'sensor/coletor.py'='DOCS/coletor.md'
    'sensor/buffers.py'='DOCS/buffers.md'; 'sensor/gravador.py'='DOCS/gravador.md'
    'sensor/gravador_worker.py'='DOCS/gravador_worker.md'; 'sensor/manager.py'='DOCS/manager.md'
    'sensor/teste_manager.py'='DOCS/teste_manager.md'; 'sensor/__init__.py'='DOCS/estrutura-do-projeto.md'
    'realtime/main.py'='DOCS/main.md'; 'realtime/janela.py'='DOCS/janela.md'
    'realtime/gráfico.py'='DOCS/grafico.md'; 'realtime/__init__.py'='DOCS/estrutura-do-projeto.md'
    'utils/statistics.py'='DOCS/statistics.md'; 'grafico/plotar_csv.py'='DOCS/plotar_csv.md'
    'dados/testar_dados.py'='DOCS/testar_dados.md'; 'calibração/calibrar_vibracao.py'='DOCS/calibrar_vibracao.md'
    'arduino/mpu-6050/mpu-6050.ino'='DOCS/arduino_mpu6050.md'
}
$fontes = rg --files -g '*.py' -g '*.ino' | ForEach-Object { $_ -replace '\\','/' }
$semNota = $fontes | Where-Object { -not $cobertura.ContainsKey($_) -or -not (Test-Path -LiteralPath $cobertura[$_]) }
if ($semNota) { throw "Fontes sem documentação: $($semNota -join ', ')" }
```

Expected: nenhum erro; as 17 fontes possuem destino documental existente.

- [ ] **Step 5: Verificar wikilinks internos**

Run:

```powershell
$alvosExistentes = @{}
Get-ChildItem DOCS,ERROS,CANVASES -Recurse -File -Include *.md,*.canvas | ForEach-Object {
    $alvosExistentes[$_.BaseName.ToLowerInvariant()] = $true
}
$quebrados = [System.Collections.Generic.HashSet[string]]::new()
Get-ChildItem -Recurse -File -Include *.md | ForEach-Object {
    $texto = Get-Content -Raw -LiteralPath $_.FullName
    [regex]::Matches($texto, '\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]') | ForEach-Object {
        $alvo = [IO.Path]::GetFileNameWithoutExtension($_.Groups[1].Value.Trim()).ToLowerInvariant()
        if (-not $alvosExistentes.ContainsKey($alvo)) { [void]$quebrados.Add($alvo) }
    }
}
if ($quebrados.Count) { throw "Wikilinks quebrados: $([string]::Join(', ', $quebrados))" }
```

Expected: zero alvos internos ausentes.

- [ ] **Step 6: Revisar o diff completo**

Run:

```powershell
git diff --stat
git diff --check
git status --short
```

Expected: sem whitespace errors; CSVs e PDFs intactos; alterações limitadas a comentários, Markdown, canvases e `sensor/arq.txt`.

- [ ] **Step 7: Remover somente o baseline temporário criado nesta execução**

Verificar primeiro que o caminho resolvido termina em `PROJETO_SENSOR_VIBRACAO\\tmp\\documentacao-baseline`; então remover somente essa pasta.

- [ ] **Step 8: Entregar o mapa de leitura**

Informar ao usuário: entrada principal, quatro canvases, nota da InvenSense, guia de modificação, verificações executadas e quaisquer inconsistências documentadas sem correção funcional.
