# Projeto Sensor de Vibração — MPU6050

Sistema didático para ler um MPU6050 conectado a um Arduino, mostrar aceleração e velocidade angular em tempo real, calcular estatísticas e registrar cada sessão em CSV para análise posterior.

O objetivo é servir tanto para visualizar experimentos quanto para entender o caminho completo de um sinal: **sensor → Arduino → serial → Python → buffer → janela/CSV → análise**.

## O que o projeto faz

- Lê os três eixos do acelerômetro: `ax`, `ay`, `az`, em `g`.
- Lê os três eixos do giroscópio: `gx`, `gy`, `gz`, em `°/s`.
- Mostra dois gráficos PyQt em tempo real, um para cada tipo de medida.
- Mantém um buffer circular de até 10.000 amostras na memória.
- Calcula Hz médio, Hz instantâneo, Hz suavizado, média, desvio padrão e RMS.
- Salva os dados em `dados/dados_aceleracao_giro-AAAA-MM-DD_HH-MM-SS.csv`.
- Abre os CSVs em um gráfico Plotly interativo para análise com calma.

## Visão rápida do fluxo

```text
MPU6050
   │ I²C
   ▼
Arduino (.ino)
   │ Serial USB, 230400 baud, uma linha CSV por amostra
   ▼
sensor/serial_reader.py
   │ generator com uma amostra validada
   ▼
sensor/coletor.py  ──────────────┬────────► BufferSensores (RAM)
                                 │                    │
                                 │                    ├── janela PyQt em tempo real
                                 │                    └── estatísticas das últimas 150 amostras
                                 │
                                 └────────► fila ─► GravadorWorker ─► CSV em dados/
                                                                         │
                                                                         ▼
                                                           grafico/plotar_csv.py (Plotly)
```

## Requisitos

- Python 3.11 ou superior (o projeto usa 3.11).
- Arduino compatível e MPU6050 conectado por I²C.
- Cabo USB de dados.
- Porta serial disponível no Windows, por exemplo `COM4`.

As bibliotecas Python estão declaradas em `pyproject.toml`: PyQt6, pyqtgraph, NumPy, pyserial, pandas e Plotly, entre outras.

## Instalação

No PowerShell, dentro da pasta do projeto:

```powershell
# Cria e ativa um ambiente virtual, se ele ainda não existir
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instala as bibliotecas usadas pelo projeto
python -m pip install --upgrade pip
python -m pip install numpy pandas plotly pyqt6 pyqtgraph pyserial matplotlib streamlit streamlit-autorefresh streamlit-echarts
```

Se você usa o gerenciador `uv`, também pode instalar a partir do `pyproject.toml`:

```powershell
uv sync
```

> Se o PowerShell bloquear a ativação do ambiente virtual, execute os comandos usando diretamente `.\.venv\Scripts\python.exe` ou ajuste a política de execução conforme as regras do seu computador.

## Hardware e firmware Arduino

O firmware está em [arduino/mpu-6050/mpu-6050.ino](arduino/mpu-6050/mpu-6050.ino).

### Ligação do MPU6050

Use a pinagem I²C correspondente à sua placa. Em um Arduino Uno/Nano clássico, normalmente:

| MPU6050 | Arduino Uno/Nano |
|---|---|
| `SDA` | `A4` |
| `SCL` | `A5` |
| `GND` | `GND` |
| `VCC` | conforme a especificação do módulo |

Em placas Mega, Leonardo, ESP32 ou similares, os pinos I²C são diferentes. Consulte a documentação da placa e do módulo. Não assuma que todo módulo aceita a mesma tensão de alimentação.

### O que o `.ino` configura

No `setup()`, o firmware:

1. inicia a serial em `230400` baud;
2. inicia o barramento I²C com `Wire.begin()`;
3. verifica o MPU6050 no endereço padrão `0x68`;
4. acorda o sensor pelo registrador `0x6B`;
5. configura o giroscópio em `±2000 °/s` (`0x1B = 0b00011000`);
6. configura o acelerômetro em `±16 g` (`0x1C = 0b00011000`).

No `loop()`, ele lê os 14 bytes do MPU6050, converte os valores brutos conforme o fundo de escala escolhido e envia uma linha CSV pela serial.

Formato produzido pelo Arduino:

```text
contador,tempo_arduino_us,ax,ay,az,gx,gy,gz
```

Exemplo:

```text
1,10002956,1.00,-0.01,-0.04,-3.48,0.12,-0.24
```

### Unidades e fundo de escala

O firmware usa os divisores abaixo, coerentes com a configuração atual:

| Medida | Fundo de escala configurado | Divisor usado | Unidade enviada |
|---|---:|---:|---|
| Acelerômetro | `±16 g` | `2048` LSB/g | `g` |
| Giroscópio | `±2000 °/s` | `16.4` LSB/(°/s) | `°/s` |

Se alterar os bits de escala no `.ino`, altere também o divisor. Por exemplo, trocar o acelerômetro para `±2 g` exige divisor `16384`, e trocar o giroscópio para `±250 °/s` exige divisor `131`.

> Os valores ainda não passam por uma calibração de offsets. É normal observar gravidade em um eixo parado e pequenos desvios no giroscópio. Para medições mais rigorosas, implemente uma etapa de calibração antes de comparar resultados.

### Cuidados no firmware

- `Serial.begin(230400)` precisa coincidir com `BAUD_RATE` em `sensor/config.py`.
- O firmware contém `delay(10000)` quando o MPU é encontrado; aguarde cerca de 10 segundos após reiniciar o Arduino.
- Não use `Serial.print()` de depuração no mesmo fluxo dos dados, pois qualquer texto extra quebra o formato CSV esperado pelo Python.
- `micros()` e o contador podem sofrer overflow em execuções muito longas. O código atual calcula Hz assumindo que os valores avançam normalmente; experimentos extensos devem tratar esse caso.
- Antes de mudar a quantidade ou a ordem das colunas, leia a seção [Como alterar o protocolo serial](#como-alterar-o-protocolo-serial).

## Configurar a porta serial

A porta e o baud rate usados pelos scripts Python estão centralizados em [sensor/config.py](sensor/config.py):

```python
PORTA_SERIAL = "COM4"
BAUD_RATE = 230400
```

Para usar outra porta, troque somente `PORTA_SERIAL` pela porta mostrada pela Arduino IDE ou pelo Gerenciador de Dispositivos, por exemplo:

```python
PORTA_SERIAL = "COM5"
```

O leitor serial, o coletor e o jogo reutilizam esses dois valores. O baud rate precisa continuar igual ao configurado no Arduino.

No Windows, uma porta ocupada por Serial Monitor, Plotter Serial ou outro programa não pode ser aberta pelo projeto. Feche esse programa antes de iniciar a coleta.

## Executar a interface principal

Com o Arduino conectado, o firmware carregado e o ambiente virtual ativo:

```powershell
python -m realtime.main
```

ou, sem ativar o ambiente:

```powershell
.\.venv\Scripts\python.exe -m realtime.main
```

A janela abre sem iniciar a leitura serial. Clique em **Iniciar** para criar as threads de coleta/gravação e abrir a porta serial. Clique em **Parar** ao final da aquisição; isso descarrega o último lote no CSV e fecha o arquivo corretamente.

## Como funciona a janela

O arquivo principal é [realtime/janela.py](realtime/janela.py). A classe `Janela` executa na thread da interface e nunca lê a serial diretamente.

### Dois gráficos, duas escalas

| Gráfico | Curvas | Unidade | Escala inicial da janela |
|---|---|---|---:|
| Aceleração | `ax`, `ay`, `az` | `g` | -40 a 40 |
| Giroscópio | `gx`, `gy`, `gz` | `°/s` | -50 a 50 |

Separar os gráficos é importante: misturar `g` e `°/s` no mesmo eixo Y faz um grupo esconder visualmente o outro. Os limites da janela são de **visualização**, não são o fundo de escala físico configurado no sensor.

Se um sinal ficar cortado, há duas opções:

1. ajustar `INTERVALO_EIXO_Y_ACELERAÇÃO` ou `INTERVALO_EIXO_Y_GIROSCÓPIO` no topo de `janela.py`;
2. clicar em **Auto Escala**, sabendo que o auto-range contínuo pode custar mais desempenho.

### Timers e quantidade de dados

```python
INTERVALO_GRAFICO_MS = 33
INTERVALO_ESTATISTICAS_MS = 500
PONTOS_GRAFICO = 150
```

- O gráfico tenta atualizar a cada 33 ms, aproximadamente 30 atualizações visuais por segundo.
- As estatísticas atualizam a cada 500 ms, ou 2 vezes por segundo.
- Cada gráfico desenha somente as últimas 150 amostras.

Com uma coleta próxima de 200 Hz, 150 amostras representam aproximadamente 0,75 s de sinal. Isso é adequado para acompanhar vibrações recentes sem redesenhar o histórico inteiro.

Mostrar somente 150 pontos **não apaga** as amostras do buffer nem do CSV; é apenas uma decisão de visualização.

### Controles atuais

- **Iniciar:** chama `manager.iniciar()`.
- **Parar:** chama `manager.parar()`, aguarda o CSV terminar de ser gravado e abre no Plotly o CSV recém-gerado, quando a sessão recebeu ao menos uma amostra.
- **Limpar:** esvazia o histórico em memória e apaga as seis curvas, sem interromper a aquisição nem apagar o CSV. Se a coleta estiver ativa, a tela volta a mostrar apenas as amostras recebidas após o clique.
- **Checkboxes:** mostram ou escondem cada eixo sem parar sua coleta.
- **Auto Escala:** ativa o ajuste contínuo do eixo Y dos dois gráficos. O eixo X continua fixo nas últimas 150 amostras.

O zoom manual é controlado por esta constante:

```python
MOUSE_ATIVADO = False
```

Para habilitar zoom com roda do mouse e deslocamento, troque seu valor para `True`.

O eixo X é relativo às últimas amostras (`0` até `n - 1`) e é reutilizado entre atualizações. Isso evita reposicionar a visualização em todo frame e preserva mais tempo de CPU para a leitura serial. O botão **Auto Escala** chama `autoescala()` para os dois gráficos.

## Pipeline Python, arquivo por arquivo

| Arquivo | Responsabilidade |
|---|---|
| [sensor/serial_reader.py](sensor/serial_reader.py) | Abre a porta serial, lê uma linha por vez, valida 8 campos e produz amostras. |
| [sensor/coletor.py](sensor/coletor.py) | Calcula Hz, detecta saltos no contador, atualiza o buffer e envia linhas para gravação. |
| [sensor/buffers.py](sensor/buffers.py) | Mantém as últimas 10.000 amostras em um array NumPy protegido por `Lock`. |
| [sensor/gravador_worker.py](sensor/gravador_worker.py) | Consome a fila de gravação em uma thread dedicada. |
| [sensor/gravador.py](sensor/gravador.py) | Cria o CSV e escreve em lotes. |
| [sensor/manager.py](sensor/manager.py) | Inicia e encerra a thread de coleta e a thread de gravação. |
| [utils/statistics.py](utils/statistics.py) | Calcula medidas descritivas de uma sequência numérica. |
| [realtime/main.py](realtime/main.py) | Cria `QApplication`, instancia a janela e inicia o loop Qt. |
| [realtime/janela.py](realtime/janela.py) | Mostra os gráficos, os controles e as estatísticas. |
| [grafico/plotar_csv.py](grafico/plotar_csv.py) | Lê um CSV salvo e abre gráficos Plotly no navegador. |
| [calibração/calibrar_vibracao.py](calibração/calibrar_vibracao.py) | Calcula offset e ganho de um eixo usando uma vibração RMS conhecida. |
| [realtime/gráfico.py](realtime/gráfico.py) | Janela mínima de depuração: apenas `ax`, com atualização muito rápida. |

### 1. Leitura serial: `serial_reader.py`

`ler_dados()` abre a porta com `pyserial`, espera uma linha terminada em quebra de linha e aceita somente mensagens com oito campos separados por vírgula. Ela converte os campos para `float` e entrega a tupla abaixo:

```python
(
    tempo_arduino_us,
    timestamp_pc,
    contador,
    ax, ay, az,
    gx, gy, gz,
)
```

O tempo do PC é guardado como referência de recepção. Para as métricas de frequência, o projeto usa `tempo_arduino_us`, que é mais adequado para medir o intervalo real entre amostras.

### 2. Coleta e frequência: `coletor.py`

`Coletor.executar()` consome o generator serial em uma thread chamada `coletor-serial`. A cada amostra, ele:

1. incrementa `numero_amostras`;
2. compara o contador recebido com o anterior;
3. registra saltos e estima quantas amostras foram perdidas;
4. calcula `hz_medio`, `hz_inst` e `hz_inst_suavizado`;
5. adiciona a amostra ao buffer circular;
6. coloca uma cópia da linha na fila de gravação, sem bloquear a serial.

O Hz suavizado é a média das últimas 100 frequências instantâneas.

Ao surgir uma mensagem como a seguir, há indício de perda real antes de a amostra chegar ao Python:

```text
[Coletor] Salto no contador: 1000 -> 1005 (4 amostras perdidas)
```

Não confunda isso com o gráfico mostrar apenas 150 pontos: esse limite é visual e não representa perda de coleta.

### 3. Buffer circular: `buffers.py`

`BufferSensores` usa um único array NumPy de formato `(10000, 9)`. Ao chegar ao limite, ele sobrescreve as amostras mais antigas e mantém as mais recentes.

Para a interface, use preferencialmente:

```python
dados = manager.buffer.snapshot(150)
```

`snapshot()` retorna cópias em ordem cronológica e mantém o `Lock` pelo menor tempo possível. Isso evita que a interface leia um dado parcialmente escrito.

Evite chamar propriedades como `buffer.ax`, `buffer.gx` ou `buffer.contador` repetidamente em caminhos críticos: quando o buffer está cheio, elas podem montar uma cópia maior. Para desenhar ou calcular várias métricas, faça um único `snapshot()` e reutilize o resultado.

### 4. Gravação CSV: `gravador_worker.py` e `gravador.py`

A serial não escreve diretamente no disco. Em vez disso:

```text
Coletor ── put_nowait(linha) ──► Queue(maxsize=50000)
                                      │
                                      ▼
                              GravadorWorker (thread)
                                      │
                                      ▼
                         GravadorCSV escreve lotes de 1000 linhas
```

Essa separação protege a aquisição contra uma escrita lenta no disco. Se a fila lotar, o coletor não para a serial: ele incrementa `amostras_nao_enfileiradas`. Nesse caso, a visualização pode continuar correta, mas algumas amostras não chegarão ao CSV.

O CSV possui cabeçalho:

```text
tempo_arduino_us,tempo_relogio_pc,contador,ax,ay,az,gx,gy,gz
```

> Sempre pare a aquisição de forma normal antes de desligar o programa. O sentinela `None` enviado pelo `manager` permite ao gravador salvar o último lote e fechar o arquivo.

### 5. Estatísticas: `utils/statistics.py`

`calcular_estatisticas(valores)` ignora valores `NaN` e infinitos e retorna uma estrutura `EstatisticasBasicas` com:

- quantidade de amostras válidas e inválidas;
- média, mediana, mínimo, máximo e amplitude pico a pico;
- variância e desvio padrão;
- RMS;
- coeficiente de variação;
- assimetria e excesso de curtose.

A janela mostra apenas **média**, **desvio padrão** e **RMS** para os seis eixos. As demais medidas já estão disponíveis para relatórios, exportação ou novas telas.

O RMS é especialmente útil em vibração porque resume a intensidade do sinal sem depender de ele estar acima ou abaixo de zero.

## Executar cada parte separadamente

### Testar somente a coleta e o manager

```powershell
python -m sensor.teste_manager
```

O terminal deve mostrar o contador e a quantidade de dados presentes no buffer. Interrompa com `Ctrl+C`; o bloco `finally` para a coleta e fecha o CSV.

### Janela principal

```powershell
python -m realtime.main
```

Use esta opção para monitoramento normal, com seis canais e estatísticas.

### Janela mínima de depuração

```powershell
python realtime\gráfico.py
```

Ela plota somente `ax`, atualiza aproximadamente a cada 16 ms e inicia a aquisição automaticamente. É útil para verificar rapidamente se o sensor está enviando dados, mas não é a opção recomendada para a análise completa ou para desempenho sustentado.

### Analisar um CSV com Plotly

```powershell
# Abre o CSV mais recente na pasta dados/
python grafico\plotar_csv.py

# Abre um CSV específico
python grafico\plotar_csv.py dados\dados_aceleracao_giro-2026-08-04_16-17-40.csv
```

O Plotly abre no navegador com dois painéis: aceleração e giroscópio. Use a roda para zoom, arraste para navegar, passe o mouse para ver valores e clique nos itens da legenda para ocultar curvas.

Ele lê o CSV inteiro. Por isso, pode exibir um pico que já saiu da janela PyQt, que desenha somente as últimas 150 amostras.

### Calibrar uma vibração conhecida

Com o sensor fixado na mesma estrutura da referência, informe a vibração conhecida em `g RMS`:

```powershell
# Referência de 0,50 g RMS no eixo Z; usa o último CSV.
python calibração\calibrar_vibracao.py 0.50

# Escolhe o arquivo e o eixo X.
python calibração\calibrar_vibracao.py 0.50 dados\teste_10hz.csv --eixo ax
```

O script salva `offset` e `ganho` em JSON, mas ainda não altera a coleta, a janela ou o CSV. Valide os coeficientes em outro ensaio antes de integrá-los. Consulte [calibração/guia_calibracao_mpu6050.md](calibração/guia_calibracao_mpu6050.md).

## Desempenho: o que pode afetar a coleta

A leitura serial roda em sua própria thread, mas todas as threads Python ainda compartilham CPU. Renderização excessiva pode reduzir o tempo disponível para a aquisição.

Mantenha estas práticas:

- atualize somente uma janela curta de dados; `PONTOS_GRAFICO = 150` é uma escolha intencional;
- evite auto-range contínuo se a interface ficar pesada;
- não faça escrita em disco na thread de leitura serial;
- evite `print()` para cada amostra;
- use um único `snapshot()` por atualização, em vez de obter cada eixo separadamente;
- ao investigar perda, observe saltos no `contador` do Arduino e `amostras_perdidas`, não apenas a aparência do gráfico;
- se diminuir `INTERVALO_GRAFICO_MS`, teste novamente a taxa e os saltos de contador.

## Como alterar o projeto com segurança

### Alterar taxa visual ou quantidade de pontos

Edite somente estas constantes em `realtime/janela.py`:

```python
INTERVALO_GRAFICO_MS = 33
INTERVALO_ESTATISTICAS_MS = 500
PONTOS_GRAFICO = 150
```

Depois, teste a interface e confirme se o terminal não relata saltos no contador. Menor intervalo significa mais redesenhos; não significa aumentar a taxa física do sensor.

### Alterar escalas dos gráficos

Edite as constantes no topo de `realtime/janela.py`:

```python
INTERVALO_EIXO_Y_ACELERAÇÃO = (-40, 40)
INTERVALO_EIXO_Y_GIROSCÓPIO = (-50, 50)
```

Esses limites são apenas visuais. Eles devem ser escolhidos de acordo com o experimento, sem confundir com o fundo de escala configurado no MPU6050.

### Adicionar uma nova estatística à janela

1. Verifique se a medida já existe em `EstatisticasBasicas`.
2. Crie um `QLabel` no painel de estatísticas em `realtime/janela.py`.
3. Atualize o rótulo dentro de `atualizar_estatisticas()` usando o `snapshot` existente.
4. Evite chamar `snapshot()` novamente dentro do mesmo tick.

### Como alterar o protocolo serial

Uma mudança na linha enviada pelo Arduino exige atualização em cadeia. Por exemplo, para adicionar temperatura:

```text
Arduino → serial_reader → coletor → buffers → gravador → janela → plotar_csv
```

Checklist:

1. envie o novo valor no `.ino` mantendo vírgulas e quebra de linha;
2. atualize a validação de quantidade de campos em `serial_reader.py`;
3. desempacote e encaminhe o valor em `coletor.py`;
4. adicione a coluna e o armazenamento em `BufferSensores`;
5. inclua a coluna no cabeçalho e na linha do CSV;
6. crie curva, rótulo ou estatística na janela se necessário;
7. atualize `grafico/plotar_csv.py` caso queira plotar a nova coluna;
8. registre a alteração na documentação em `DOCS/`.

Se apenas uma dessas etapas for esquecida, o leitor pode descartar linhas por número incorreto de campos ou os dados podem ficar desalinhados.

## Diagnóstico rápido

| Sintoma | Verificações iniciais |
|---|---|
| `SerialException` / não abre `COM4` | Confirme a porta, feche Serial Monitor e verifique o cabo USB. |
| Janela abre, mas não há curvas | Clique em **Iniciar**, aguarde o atraso do firmware e confira se os checkboxes estão marcados. |
| Linhas inválidas na serial | Garanta que o Arduino envie somente oito números separados por vírgulas; remova mensagens de depuração. |
| Saltos no contador | Reduza carga de interface, confira baud rate, cabo e produção de dados no Arduino. |
| CSV não possui as últimas linhas | Pare a aquisição normalmente para executar o flush do gravador. |
| Aceleração parece reta | Ajuste a escala do gráfico de aceleração; não misture com a escala do giroscópio. |
| Não há zoom com mouse | Altere `MOUSE_ATIVADO = False` para `True` em `realtime/janela.py`. |
| Eixo parado passa de ~1 g para ~8 g após movimento | Suspeite de reset do MPU6050; confira alimentação, I²C e escalas. |
| Plotly não encontra arquivo | Confirme que existe um CSV não vazio em `dados/` ou informe o caminho manualmente. |

## Estrutura de diretórios

```text
PROJETO_SENSOR_VIBRACAO/
├── arduino/mpu-6050/mpu-6050.ino  # firmware do sensor
├── sensor/                         # configuração, leitura, coleta, buffer, manager e CSV
├── realtime/                       # interface PyQt e ponto de entrada
├── utils/statistics.py             # estatísticas descritivas
├── grafico/plotar_csv.py           # análise interativa de CSV com Plotly
├── calibração/                      # guia e calibração por referência RMS
├── dados/                          # CSVs gerados durante as sessões
├── DOCS/                           # documentação detalhada por componente
├── ERROS/                          # histórico de correções
├── componentes/                    # recursos/componentes auxiliares
├── pages/                          # páginas Streamlit, se utilizadas
└── pyproject.toml                  # dependências Python
```

## Documentação: caminho de leitura

A pasta [DOCS](DOCS) reúne a documentação detalhada e organizada por assunto. Para entender o projeto antes de alterar o código, siga esta ordem:

1. [Índice da documentação](DOCS/INDEX.md) — mapa de navegação e visão do fluxo completo.
2. [Teoria de vibração](DOCS/arquitetura/teoria_vibração.md) — fundamentos físicos, EDOs, amostragem, incerteza e interpretação responsável de medições.
3. [Arquitetura do sistema](DOCS/arquitetura/ARQUITETURA.md) — como uma amostra percorre firmware, serial, Python, buffer, interface e CSV.

### Firmware e MPU6050

- [Firmware `mpu-6050.ino`](DOCS/referencias/arduino_mpu6050.md) — explicação em ordem do código, do I2C ao protocolo serial.
- [Mapa de registradores usado](DOCS/referencias/mpu6050_register_map.md) — somente os registradores e bits efetivamente usados pelo firmware, com páginas do PDF.
- [Especificação técnica usada](DOCS/referencias/mpu6050_product_specification.md) — escalas, sensibilidades, endereço I2C e sequência de leitura relevantes ao `.ino`.

### Aquisição, interface e análise

- [Leitor serial](DOCS/sensor/serial_reader.md), [coletor](DOCS/sensor/coletor.md) e [buffer](DOCS/sensor/buffers.md) — caminho da amostra dentro do Python.
- [Janela em tempo real](DOCS/realtime/janela.md) — gráficos, controles e estatísticas da interface.
- [Validação do CSV](DOCS/analise/testar_dados.md) e [plotagem do CSV](DOCS/analise/plotar_csv.md) — confirme a qualidade da captura antes de interpretar sinais.
- [Estatísticas](DOCS/analise/statistics.md) e [calibração](DOCS/analise/calibrar_vibracao.md) — medidas descritivas e ajuste por referência RMS.
- [Guia de calibração de bancada](calibração/guia_calibracao_mpu6050.md) — procedimento prático complementar.

## Próximos passos possíveis

- calibração automática de offsets do MPU6050;
- FFT e espectro de frequência;
- exportação de relatórios;
- indicadores de anomalia ou alarme de vibração;
- seleção da porta serial diretamente na janela;
- definir explicitamente taxa de amostragem e filtro DLPF conforme a faixa de vibração de interesse;
- testes automatizados para parser serial, buffer e estatísticas.
#PROJETO_SENSOR_VIBRAÇÃO
