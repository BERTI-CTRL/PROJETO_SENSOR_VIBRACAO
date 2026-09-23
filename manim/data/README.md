# Origem dos dados da animação

O vídeo utiliza o CSV real existente em
`../../dados/dados_aceleracao_giro-2026-09-21_15-13-31.csv`.
Não é necessário duplicar a captura nesta pasta.

O recorte padrão usa `ay`, em **g**, entre **0 e 15 segundos** após a primeira
amostra da sessão. O eixo temporal é calculado de `tempo_arduino_us`, em
microssegundos. No gráfico, o tempo zero corresponde ao primeiro ponto do
recorte; `SignalData.start_seconds` conserva sua posição dentro da captura.
Todos os pontos selecionados permanecem nos dados: não há filtro,
reamostragem, normalização nem remoção do nível médio. As estatísticas RMS,
média e desvio padrão descrevem a aceleração bruta em g.

A captura completa contém **3.276 amostras** e dura aproximadamente **15,30 s**.
O recorte padrão de 15 s contém **3.213 amostras**. A aceleração `ay` nesse
recorte tem média de −0,162 g, desvio padrão de 0,843 g e RMS de 0,859 g.
Esses valores descrevem o sinal bruto, sem remoção de gravidade, offset ou ruído.

É possível escolher outro arquivo pelo argumento `csv_path` de `load_signal`,
além de `axis`, `start` e `duration`. Um caminho informado que não exista gera
erro. Somente quando o CSV **padrão** estiver ausente será usada uma sequência
determinística marcada **DADOS SINTÉTICOS**, com `synthetic=True` e `source=None`.
CSV inválido jamais é substituído silenciosamente por dados de demonstração.

# Modelo conceitual do pórtico e comparação

A cena do pórtico mostra a equação simbólica usada como referência pela equipe:

```text
M v''(t) + ε v'(t) + K v(t) = P(t)
```

Na animação, `v(t)` é o deslocamento generalizado do pórtico. A notação e os
parâmetros são conceituais; não foram identificados a partir do CSV. A curva
experimental mostrada usa o eixo `ay` da captura indicada acima.

## Resposta ilustrativa usada nas cenas seguintes

`../signal_data.py` implementa apenas para a animação uma resposta de vibração
livre subamortecida inspirada no modelo documentado em
`../../DOCS/arquitetura/teoria_vibração.md`:

```text
m x'' + c x' + k x = 0
x(t) = A exp(-alpha t) cos(wd t)
alpha = c/(2m)
wd = sqrt(k/m - alpha²)
```

Os valores padrão são **ilustrativos**: m = 1 kg, c = 0,7 N·s/m,
k = 16 N/m e A = 0,018 m. As condições iniciais correspondentes são
x(0) = A e v(0) = -alpha A. A função `illustrative_response` retorna
deslocamento em m, velocidade em m/s e aceleração em m/s².
Para colocar a aceleração teórica no mesmo eixo em g que a medição,
utiliza-se `acceleration / 9.80665`.

Não há identificação de m, c ou k a partir destes dados, nem calibração
aplicada, separação da gravidade ou método experimental documentado que
valide o modelo nesta captura. A estrutura desenhada é uma representação
didática. A sobreposição de curvas mostra **como uma comparação poderia ser
feita**, sem afirmar concordância, erro percentual ou validação do modelo.
Os painéis da comparação usam escalas verticais independentes para mostrar as
formas dos sinais sem insinuar que suas amplitudes sejam comparáveis. O rótulo
“Comparação conceitual • escalas verticais independentes • sem ajuste
experimental” acompanha essa etapa do vídeo.
