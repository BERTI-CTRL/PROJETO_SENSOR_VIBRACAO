# testar_dados.py

## Visão geral

`testar_dados.py` audita os CSVs já gravados pelo projeto. Ele verifica o contrato do arquivo, converte as amostras para números e identifica sintomas de aquisição problemática: linhas inválidas, saltos no contador, regressões no relógio do PC, `NaN`/infinito e valores fora da escala configurada do MPU6050.

É uma etapa de **validação**, não de visualização. O fluxo recomendado é: gravar com [[gravador]], validar com este script e, se aprovado, explorar o mesmo arquivo em [[plotar_csv]].

## Papel no projeto

| Aspecto | Comportamento |
| --- | --- |
| Entrada | Caminho de um CSV ou, sem argumento, o CSV mais recente que siga `dados_aceleracao_giro-*.csv` na pasta `dados`. |
| Saída | Relatório no terminal, dicionário de resultados e código de processo `0` (aprovado) ou `1` (falha). |
| Dependências | Biblioteca padrão do Python e `numpy`. |
| Não faz | Não modifica o CSV, não recupera amostras perdidas e não desenha gráficos. |

Ele complementa [[teste_manager]], que exercita a aquisição ao vivo. Aqui a pergunta é outra: “o arquivo que já foi salvo é internamente confiável para análise?”

## Fluxo mental

```text
arquivo informado ──────► confirmar existência
       │
sem argumento ──────────► localizar CSV mais recente em dados/
                                  │
                                  ▼
                         ler arquivo e validar cabeçalho
                                  │
                                  ▼
                      validar 9 campos numéricos por linha
                                  │
                                  ▼
                         matriz NumPy: tempos, contador, eixos
                                  │
          ┌───────────────┬────────┴─────────┬───────────────┐
          ▼               ▼                  ▼               ▼
      perdas         frequência          limites físicos   NaN/Inf
          └───────────────┴────────┬─────────┴───────────────┘
                                   ▼
                       consolidar `resultado["ok"]`
                                   │
                            processo 0 ou 1
```

## Dependências e contrato do CSV

```python
import sys
import glob
import os

try:
    import numpy as np
except ImportError:
    print("ERRO: numpy não está instalado.")
    sys.exit(1)
```

`sys` fornece argumentos e código de saída; `glob`/`os` procuram arquivos; `numpy` permite calcular diferenças, estatísticas e valores não finitos de forma vetorizada.

> [!warning] Importar este módulo exige NumPy
>
> Caso `numpy` falte, o `sys.exit(1)` acontece já durante a importação. Isso é aceitável para um script de terminal, mas limita o reuso de `testar_arquivo` por outro programa. Uma evolução seria checar a dependência dentro de `main()` ou lançar uma exceção.

O cabeçalho é exigido exatamente nesta ordem:

```python
esperadas = [
    "tempo_arduino_us", "tempo_relogio_pc", "contador",
    "ax", "ay", "az", "gx", "gy", "gz",
]
```

O contrato é gerado por [[gravador]] e descrito em [[esquema-csv]]. A checagem rígida impede que um arquivo com colunas parecidas, mas semanticamente incompatíveis, seja aceito silenciosamente.

## Código explicado, na ordem do arquivo

### `testar_arquivo(caminho)`: leitura e estrutura

```python
with open(caminho, "r") as arquivo:
    linhas = arquivo.readlines()

if not linhas:
    return {"erro": "Arquivo vazio"}

cabecalho = linhas[0].strip().split(",")
if cabecalho != esperadas:
    return {"erro": f"Cabeçalho inválido: {cabecalho}"}
```

O `with` assegura o fechamento do arquivo. Antes de cálculos, o script recusa arquivo vazio e cabeçalho diferente. Erros são retornados em um dicionário; o ponto de entrada os transforma em falha do processo.

> [!warning] Leitura integral
>
> `readlines()` simplifica o número da linha no diagnóstico, mas carrega tudo na memória. Para coletas muito longas, iterar diretamente sobre o arquivo mantém a validação e reduz esse custo.

### Cada amostra deve conter nove números

```python
dados = []
for numero_linha, linha in enumerate(linhas[1:], 1):
    linha = linha.strip()
    if not linha:
        continue
    partes = linha.split(",")
    if len(partes) != 9:
        return {"erro": f"Linha {numero_linha}: esperado 9 campos"}
    try:
        dados.append([float(valor) for valor in partes])
    except ValueError:
        return {"erro": f"Linha {numero_linha}: valor não numérico"}
```

Linhas vazias são ignoradas. Toda outra linha precisa ter nove campos que `float` consiga converter; gravação truncada, coluna deslocada ou texto no sinal param a análise com a linha responsável. Um arquivo que possui apenas cabeçalho também é rejeitado.

### A matriz separa as responsabilidades de cada coluna

```python
arr = np.array(dados)
tempo_arduino = arr[:, 0]
tempo_pc = arr[:, 1]
contador = arr[:, 2]
sensores = arr[:, 3:]
```

Cada linha representa uma amostra. `tempo_arduino` é a base para cadência, `tempo_pc` detecta regressão de relógio, `contador` revela lacunas e `sensores` contém os seis eixos. Essa separação evita confundir perda de pacote com variação normal de tempo.

### Saltos no contador estimam amostras perdidas

```python
diffs = np.diff(contador)
saltos = np.where(diffs > 1)[0]
total_perdidas = int(np.sum(diffs[saltos] - 1)) if len(saltos) else 0
```

Em uma sequência contínua, o contador cresce de um em um. A transição de `104` para `108` representa três amostras ausentes. O relatório mostra tanto a quantidade de saltos quanto a soma das perdas estimadas.

> [!warning] Cobertura parcial da sequência
>
> A regra detecta apenas `diff > 1`. Repetições, regressões e um reinício/overflow do contador não são classificados como salto. Se tais casos importarem, adicione teste para `diff <= 0` e defina o tratamento de rollover conforme o firmware.

### Frequência usa o relógio do Arduino

```python
dt_arduino = np.diff(tempo_arduino) / 1e6
dt_arduino = dt_arduino[dt_arduino > 0]
hz_inst = 1.0 / dt_arduino
hz_medio = (n - 1) / ((tempo_arduino[-1] - tempo_arduino[0]) / 1e6)
```

O script converte microssegundos em segundos, calcula a frequência instantânea nos deltas positivos e produz média, desvio padrão, mínimo e máximo. Assim, além da taxa geral, fica visível o *jitter* da aquisição.

> [!warning] Séries curtas e deltas inválidos
>
> Com uma única amostra, ou se todos os deltas forem não positivos, não existe frequência instantânea válida e as estatísticas podem falhar. Uma versão mais defensiva deve exigir `n >= 2` e `dt_arduino` não vazio antes de usar mínimo ou máximo.

O relógio do PC recebe uma verificação diferente:

```python
dt_pc = np.diff(tempo_pc)
negativos_pc = int(np.sum(dt_pc < 0))
```

Ela encontra regressões de tempo, mas não mede latência exata de chegada. No leitor serial, o timestamp do PC é produzido antes da leitura bloqueante; portanto, ele marca o ciclo de aquisição, não o instante preciso em que o pacote chegou.

### Os eixos passam por estatísticas e limites físicos

```python
nomes = ["ax", "ay", "az", "gx", "gy", "gz"]
limites = [16, 16, 16, 2000, 2000, 2000]

for indice, (nome, limite) in enumerate(zip(nomes, limites)):
    valores = sensores[:, indice]
    fora = int(np.sum(np.abs(valores) > limite))
```

Para cada eixo, o relatório apresenta mínimo, máximo, média, desvio padrão e RMS. A regra aceita acelerômetros até ±16 g e giroscópios até ±2000 °/s. Os limites devem acompanhar a escala configurada no MPU6050: mudar o firmware sem ajustar esta lista produz falsos alarmes ou deixa leituras inviáveis passarem.

`np.sum(~np.isfinite(arr))` também conta `NaN` e infinitos. Qualquer valor não finito impede aprovação para proteger cálculos posteriores e gráficos.

### Resultado, seleção automática e CLI

`ok` só é verdadeiro quando não há perdas detectadas, regressão de tempo do PC, valores não finitos nem leituras fora dos limites. O dicionário retornado reúne os indicadores em `int` e `float` nativos, uma base prática para futura integração com outros scripts.

Sem caminho explícito, a função abaixo procura o CSV mais novo:

```python
def encontrar_mais_recente(diretorio="dados"):
    padrao = os.path.join(diretorio, "dados_aceleracao_giro-*.csv")
    arquivos = glob.glob(padrao)
    return max(arquivos, key=os.path.getmtime) if arquivos else None
```

`main()` usa o argumento quando fornecido, confirma se ele existe, interpreta o retorno de `testar_arquivo` e encerra com `sys.exit(0 if resultado["ok"] else 1)`. Já o guarda `if __name__ == "__main__":` evita chamar `main()` na importação.

## Estratégia de uso

```powershell
python dados/testar_dados.py dados/dados_aceleracao_giro-experimento.csv
if ($LASTEXITCODE -eq 0) {
    python grafico/plotar_csv.py dados/dados_aceleracao_giro-experimento.csv
}
```

Passe o caminho explicitamente quando a rastreabilidade for importante. Escolher “o mais recente” é conveniente para testes rápidos, mas pode selecionar uma coleta errada quando há experimentos concorrentes.

1. Preserve o CSV original produzido por [[gravador]].
2. Valide o arquivo com este script.
3. Se retornar falha, use o relatório para investigar firmware, serial ou configuração de escala.
4. Se retornar sucesso, use [[plotar_csv]] para interpretar tendências, picos e ruído.

## Insights para outros projetos

- **CSV é uma interface:** validar nomes, ordem e quantidade de campos cedo reduz ambiguidades entre aquisição e análise.
- **Contadores e relógios se completam:** contador expõe lacunas; timestamp expõe cadência. Nenhum substitui o outro.
- **Códigos de processo são uma API simples:** `0`/`1` permitem encaixar validação em automações sem interpretar texto do terminal.
- **Faixas físicas precisam de fonte única de verdade:** firmware e análise devem compartilhar ou sincronizar as escalas do sensor.
- **Validação antecede visualização:** um gráfico convincente não prova que a sequência está completa nem que os valores são finitos.

## Resumo mental

Trate `testar_dados.py` como a inspeção de recebimento de um experimento: ele confirma que o arquivo segue o contrato, que a sequência não mostra lacunas detectáveis, que tempos e números são usáveis e que as medições cabem na escala esperada. Depois da aprovação, [[plotar_csv]] ajuda a compreender a forma do sinal; em caso de falha, o relatório indica a camada a investigar.
#PROJETO_SENSOR_VIBRAÇÃO
