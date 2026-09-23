# Animação — Sensor de Vibração

Narrativa visual em Manim que acompanha o caminho **vibração → MPU6050 → Arduino → Python → CSV → análise experimental**. O MP4 é salvo diretamente nesta pasta, sem abrir um player automaticamente. A animação não inclui narração nem trilha sonora.

## Renderização no Windows

Execute os comandos no PowerShell, na raiz do repositório. Use um ambiente separado para as dependências da animação:

```powershell
py -3.11 -m venv manim/.venv
.\manim\.venv\Scripts\python.exe -m pip install -r manim/requirements.txt
.\manim\.venv\Scripts\python.exe manim/render.py
```

Se o ambiente foi criado com `uv` sem `pip`, instale com:

```powershell
uv pip install --python manim/.venv/Scripts/python.exe -r manim/requirements.txt
```

O render usa Cairo. As fórmulas são composições vetoriais de texto (fonte Cambria Math), pontos e índices nativos do Manim; não é necessário instalar LaTeX. Não é necessário conectar o Arduino para renderizar.

| Comando/opção | Saída dentro de `manim/` |
| --- | --- |
| `python manim/render.py` | `sensor_vibracao_horizontal.mp4` — 1920 × 1080, 30 fps |
| `python manim/render.py --format vertical` | `sensor_vibracao_vertical.mp4` — 1080 × 1920, 30 fps |
| `python manim/render.py --quality preview` | `sensor_vibracao_horizontal_preview.mp4` — 960 × 540, 15 fps |
| `python manim/render.py --format vertical --quality preview` | `sensor_vibracao_vertical_preview.mp4` — 540 × 960, 15 fps |

Na tabela, `python` deve ser o executável de `manim/.venv`. Repetir a mesma combinação de orientação, qualidade e cena substitui o MP4 correspondente. Arquivos intermediários ficam em `manim/media/`.

## Ajustar o CSV e renderizar por cena

```powershell
# Teste rápido da terceira cena
.\manim\.venv\Scripts\python.exe manim/render.py --quality preview --section 3

# Escolhe outro ensaio, eixo e intervalo
.\manim\.venv\Scripts\python.exe manim/render.py --csv dados/dados_aceleracao_giro-2026-09-07_17-12-29.csv --axis az --start 8 --duration 10

# Todas as opções
.\manim\.venv\Scripts\python.exe manim/render.py --help
```

`--section` aceita de 1 a 6 e acrescenta `_cena_N` ao nome do vídeo. Omita a opção para renderizar a narrativa inteira. `--start` e `--duration` controlam o recorte dos dados, em segundos desde o início da aquisição; não controlam a duração da animação. Um caminho passado em `--csv` é relativo à pasta em que o comando é executado, podendo também ser absoluto. Os eixos disponíveis são `ax`, `ay` e `az`.

## Narrativa e limites científicos

1. **A vibração:** uma estrutura é perturbada e o movimento deixa um rastro.
2. **O sensor:** o MPU6050 converte o movimento em leituras de aceleração.
3. **Do físico aos dados:** pulsos seguem pelo Arduino e se tornam uma sequência temporal e um gráfico.
4. **Python:** os dados chegam pela serial, são armazenados em buffer/CSV e alimentam gráficos e estatísticas.
5. **Movimento do pórtico:** a equação idealizada `M v''(t) + ε v'(t) + K v(t) = P(t)` aparece com a explicação de cada termo.
6. **Fechamento:** o ícone do sensor e o nome do projeto concluem a narrativa.

O sinal experimental padrão usa `dados/dados_aceleracao_giro-2026-09-21_15-13-31.csv`, eixo `ay`, do início da captura até 15 s. As acelerações do firmware estão em `g`; o tempo experimental é derivado de `tempo_arduino_us`. O gráfico reposiciona o início do recorte em `t = 0` e identifica o arquivo usado. A figura do pórtico é esquemática: não documenta uma geometria de bancada identificada no CSV.

O recorte padrão contém **3.213 amostras**: média −0,162 g, desvio padrão populacional 0,843 g e RMS 0,859 g. Os valores são aceleração bruta; não removem gravidade, offset ou ruído.

O vídeo apresenta o sinal bruto do eixo escolhido, em `g`, e as estatísticas do recorte. A equação do pórtico é uma idealização do movimento: `v(t)` representa o deslocamento, `v'(t)` a velocidade e `v''(t)` a aceleração. Os termos representam inércia (`M`), amortecimento (`ε`), rigidez (`K`) e força aplicada (`P(t)`). Os parâmetros não foram ajustados ao ensaio; não há curva simulada nem comparação teórica com o CSV.

Se o CSV padrão estiver ausente, a animação usa uma sequência determinística identificada como **dados sintéticos**. Um `--csv` explícito ausente, um CSV inválido ou um recorte sem amostras suficientes gera erro, sem substituir silenciosamente a medição.

Esta pasta apenas lê os dados existentes para produzir a animação. Não altera a aquisição, o firmware, o processamento ao vivo ou os CSVs originais.

## Arquivos

- `main.py`: cena `SensorVibracao`, organização da narrativa e adaptação de layout.
- `visuals.py`: cores, tipografia, sensor, Arduino, sistema mecânico, fórmulas e gráficos.
- `signal_data.py`: leitura validada do CSV e cálculo das estatísticas do sinal.
- `test_signal_data.py`: 13 testes de integridade dos dados, seleção de intervalo e consistência da EDO.
- `render.py`: opções de render, seleção de dados e nomes dos MP4s.
- `requirements.txt`: dependências do ambiente da animação.
- `PLANO.md`: análise, storyboard, transições e critérios de verificação.
- `assets/`: imagens de referência da animação.
- `data/README.md`: proveniência dos dados e detalhes científicos; o CSV original não é duplicado.
- `media/horizontal/` e `media/vertical/`: caches independentes e arquivos intermediários do Manim.

Para mudar a aparência, edite as cores e as funções em `visuals.py`. Para alterar o ritmo, ajuste `run_time` e `wait` nos seis métodos de `main.py`. Os textos, posições e tamanhos têm adaptações para o formato vertical; o vídeo vertical não é um corte do horizontal.

## Verificação

```powershell
.\manim\.venv\Scripts\python.exe -m unittest discover -s manim -p test_signal_data.py -v
```

Os testes verificam a conversão de microssegundos, a preservação dos valores brutos, a seleção de eixos/intervalos, entradas inválidas, fallback sintético explícito e a identidade `m*a + c*v + k*x = 0`, além de conferir numericamente as derivadas da solução.

As instalações locais devem ter as fontes Segoe UI, Consolas e Cambria Math (presentes no Windows). Em outro sistema, substitua os nomes em `visuals.py` por fontes disponíveis. Referência de instalação: [documentação oficial do Manim](https://docs.manim.community/en/stable/installation/uv.html).

O launcher pode ser chamado de outra pasta: ele resolve a localização de `main.py`, define o diretório de trabalho e mantém os vídeos ao lado deste README.
