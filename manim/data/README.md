# Origem dos dados da animação

O vídeo utiliza o CSV real existente em
`../../dados/dados_aceleracao_giro-2026-09-07_16-57-08.csv`.
Não é necessário duplicar a captura nesta pasta.

O recorte padrão usa `az`, em **g**, entre **8 e 18 segundos** após a primeira
amostra da sessão. O eixo temporal é calculado de `tempo_arduino_us`, em
microssegundos. No gráfico, o tempo zero corresponde ao primeiro ponto do
recorte; `SignalData.start_seconds` conserva sua posição dentro da captura.
Todos os pontos selecionados permanecem nos dados: não há filtro,
reamostragem, normalização nem remoção do nível médio. As estatísticas RMS,
média e desvio padrão descrevem a aceleração bruta em g.

A captura completa contém **7.883 amostras**, dura aproximadamente **35,924 s**
e apresenta taxa média efetiva de **219,408 amostras/s**. A validação com
`dados/testar_dados.py` não encontrou saltos de contador, valores não finitos,
regressões do tempo do PC nem valores fora das faixas configuradas.
Essa validação atesta integridade estrutural, não comprova a hipótese mecânica.

É possível escolher outro arquivo pelo argumento `csv_path` de `load_signal`,
além de `axis`, `start` e `duration`. Um caminho informado que não exista gera
erro. Somente quando o CSV **padrão** estiver ausente será usada uma sequência
determinística marcada **DADOS SINTÉTICOS**, com `synthetic=True` e `source=None`.
CSV inválido jamais é substituído silenciosamente por dados de demonstração.

# Modelo ilustrativo e comparação

`../signal_data.py` implementa apenas para a animação a hipótese de vibração
livre subamortecida documentada em
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
O rótulo “Comparação conceitual • parâmetros ilustrativos • sem ajuste
experimental” deve acompanhar essa etapa do vídeo.
