# Teoria de vibração: da física ao dado

> [!abstract] Propósito desta leitura
>
> Esta nota constrói a ponte entre um objeto que vibra, o sinal que o MPU6050 mede e os números que chegam à interface. Ela vem antes da programação: primeiro entendemos **o que o sistema tenta representar**, depois fica muito mais fácil compreender por que existem [[serial_reader]], [[coletor]], [[buffers]], [[statistics]] e [[plotar_csv]].

## Como usar esta nota

Não é preciso dominar cálculo para começar. Leia as ideias em ordem, usando as equações como mapas: elas resumem relações que serão explicadas em palavras. Quando algum termo parecer técnico, continue; a intuição costuma vir antes do formalismo.

O projeto atual é um sistema de **medição e observação de vibração**. Ele ainda não identifica automaticamente o tipo de máquina, nem resolve uma EDO a partir do CSV. Mesmo assim, a teoria abaixo explica o significado dos dados e indica o que seria necessário para evoluir de “ver sinais” para “modelar um sistema físico”.

## 1. O que é vibração?

Vibração é movimento que se repete em torno de uma posição de equilíbrio. Pense em uma régua presa à mesa: ao puxá-la e soltar, ela alterna para cima e para baixo até parar. A posição de repouso é o equilíbrio; os desvios em torno dela formam a vibração.

Podemos descrever o mesmo movimento de três maneiras:

- **deslocamento**: onde o corpo está em relação ao equilíbrio;
- **velocidade**: quão rápido a posição muda;
- **aceleração**: quão rapidamente a velocidade muda.

Elas são ligadas por derivadas no tempo:

$$
v(t) = \frac{dx(t)}{dt}
$$

$$
a(t) = \frac{d^2x(t)}{dt^2}
$$

Aqui, posição, velocidade e aceleração são funções do tempo. O projeto mede diretamente a última delas em três direções: `ax`, `ay` e `az`. Isso é importante: o gráfico de aceleração não é, por si só, o gráfico de deslocamento.

> [!tip] Intuição rápida
>
> Em uma montanha-russa, você pode estar muito alto e parado por um instante: grande deslocamento, velocidade quase nula e aceleração que depende da curva e das forças. Cada grandeza responde a uma pergunta diferente sobre o movimento.

## 2. Da força ao movimento: a ideia de modelo

A física clássica começa com uma pergunta simples: quais forças atuam no corpo? A segunda lei de Newton relaciona força resultante e aceleração:

$$
\sum F(t) = m a(t)
$$

`m` é a massa. A igualdade não diz que toda vibração é igual; ela oferece uma linguagem para descrever como um sistema responde a forças.

Para transformar uma situação real em modelo, escolhemos o que importa e deixamos o restante como aproximação. Uma máquina real possui várias peças, folgas, ruído, atrito e estruturas flexíveis. Um primeiro modelo pode representá-la por uma única massa, uma mola e um amortecedor. Essa simplificação não é uma mentira: é uma hipótese que deve ser útil, explícita e confrontada com dados.

Esta é a dimensão filosófica central do projeto: uma medida não é a coisa medida, e um modelo não é a realidade. O sinal registrado em [[esquema-csv]] é evidência sobre um fenômeno; sua interpretação depende de escala, montagem, frequência, ruído e perguntas que queremos responder.

## 3. O modelo massa–mola–amortecedor

O modelo mais didático para vibração é um bloco de massa `m` conectado a uma mola de rigidez `k` e a um amortecedor viscoso `c`.

```text
parede fixa ── mola k ──┬── massa m
                        └── amortecedor c
                              │
                         deslocamento x(t)
```

- A **massa** resiste a mudar seu estado de movimento: quanto maior, mais difícil acelerá-la.
- A **mola** puxa o corpo de volta ao equilíbrio: quanto mais rígida, maior a força restauradora para o mesmo deslocamento.
- O **amortecedor** dissipa energia: ele representa atrito, perdas internas do material ou fluido viscoso.

As duas forças internas mais comuns são:

$$
F_{mola}(t) = -k x(t)
$$

$$
F_{amortecedor}(t) = -c v(t)
$$

O sinal negativo significa “contra o desvio ou contra o movimento”. Ao combinar essas forças com a segunda lei de Newton, obtemos a EDO clássica de segunda ordem:

$$
m\frac{d^2x(t)}{dt^2} + c\frac{dx(t)}{dt} + kx(t) = F_{ext}(t)
$$

Uma **equação diferencial ordinária**, ou EDO, relaciona uma grandeza desconhecida e suas derivadas em relação a uma única variável independente — aqui, o tempo. Resolver a EDO significa encontrar uma função `x(t)` compatível com massa, amortecimento, rigidez, força externa e condições iniciais.

> [!note] O que a EDO oferece
>
> A EDO é um gerador de hipóteses. Ela permite prever a resposta de um sistema idealizado. Os dados do sensor permitem perguntar se a previsão parece compatível com a experiência, onde ela falha e quais efeitos reais talvez estejam faltando no modelo.

## 4. Vibração livre: o que acontece depois de soltar?

Quando não há força externa contínua, usamos:

$$
F_{ext}(t) = 0
$$

Se também ignorarmos amortecimento, surge o oscilador harmônico simples:

$$
m\frac{d^2x(t)}{dt^2} + kx(t) = 0
$$

Sua resposta é periódica, com frequência natural angular:

$$
\omega_n = \sqrt{\frac{k}{m}}
$$

E a frequência em hertz é:

$$
f_n = \frac{\omega_n}{2\pi}
$$

Isso traz uma ideia poderosa: mesmo sem uma “batida” externa repetida, um sistema elástico tende a oscilar em frequências próprias. Uma régua curta e rígida vibra mais rápido do que uma longa e flexível porque sua relação efetiva entre rigidez e massa é diferente.

Na prática, quase todo sistema perde energia. Para organizar a intensidade dessas perdas, usamos a razão de amortecimento:

$$
\zeta = \frac{c}{2\sqrt{km}}
$$

- Se o amortecimento for pequeno, o corpo oscila muitas vezes e a amplitude diminui aos poucos.
- Se for crítico, ele retorna ao equilíbrio rapidamente sem oscilar.
- Se for muito alto, retorna sem oscilar, mas de forma mais lenta.

O projeto pode registrar um ensaio de “puxar e soltar” no CSV por [[gravador]]. A curva de aceleração resultante permite observar a diminuição da amplitude. Estimar rigorosamente `m`, `c` e `k`, porém, exige experimento controlado, dados adequados e um método de identificação — não apenas olhar o gráfico.

## 5. Excitação forçada e ressonância

Muitas vibrações reais não são livres: motor desbalanceado, piso, engrenagem ou vibração de base aplicam força continuamente. Um caso didático é uma força senoidal:

$$
F_{ext}(t) = F_0\sin(\omega t)
$$

O sistema então responde com uma combinação de frequência natural, amortecimento e frequência da excitação. Quando a excitação fica perto da frequência natural, a amplitude pode crescer bastante. Esse fenômeno é a **ressonância**.

Ressonância não significa automaticamente quebra ou perigo. Ela significa que o sistema está muito eficiente em receber energia naquela faixa. O risco depende da amplitude, do material, do tempo de exposição e dos limites de projeto.

> [!warning] Um pico não prova ressonância sozinho
>
> Um pico no gráfico de [[plotar_csv]] pode resultar de impacto, saturação, ruído, mudança de montagem ou uma excitação transitória. Para chamar algo de ressonância, compare frequências, repita o ensaio e verifique se o comportamento é consistente com uma hipótese física.

## 6. Vibração da base: onde o sensor está preso importa

Há diferença entre aplicar força diretamente à massa e mover o ponto onde ela está apoiada. Se a base se move com deslocamento `y(t)`, o interesse pode ser o deslocamento relativo:

$$
z(t) = x(t) - y(t)
$$

Uma forma de escrever a EDO para excitação de base é:

$$
m\frac{d^2z(t)}{dt^2} + c\frac{dz(t)}{dt} + kz(t) = -m\frac{d^2y(t)}{dt^2}
$$

Isso ajuda a perceber por que dois sensores em pontos diferentes da mesma estrutura podem registrar sinais distintos. A posição, o aperto, a orientação e a rigidez da fixação fazem parte do experimento. Antes de comparar testes, registre onde e como o MPU6050 foi montado; uma mudança de montagem pode ser maior que a diferença entre duas condições da máquina.

## 7. O que o MPU6050 mede de fato

O acelerômetro do MPU6050 não entrega deslocamento e nem “vibração pura”. Ele mede **aceleração específica**, isto é, a resposta inercial percebida pelo sensor, incluindo o efeito da gravidade quando o módulo está parado em relação à Terra.

Por isso, um sensor imóvel sobre uma mesa normalmente apresenta aproximadamente uma unidade de gravidade em um dos eixos, dependendo de sua orientação. Não significa que a mesa esteja acelerando para cima; significa que o acelerômetro percebe a força de sustentação que impede a queda livre.

O projeto transmite `ax`, `ay` e `az` em unidade `g`, e `gx`, `gy` e `gz` em graus por segundo. [[arduino_mpu6050]] explica as escalas configuradas no firmware: atualmente, o acelerômetro usa ±16 g e o giroscópio ±2000 °/s. Essas escolhas equilibram margem contra saturação e resolução.

Uma aproximação prática para converter a unidade `g` em unidade SI é:

$$
1\,g \approx 9{,}80665\,\mathrm{m/s^2}
$$

> [!warning] Gravidade, inclinação e vibração se misturam
>
> Se o sensor inclina lentamente, a projeção da gravidade muda entre `ax`, `ay` e `az`, mesmo sem vibração estrutural. Separar gravidade de aceleração dinâmica exige orientação, filtragem ou um experimento em que a orientação se mantenha estável. O projeto atual registra os seis eixos, mas não executa fusão sensorial.

## 8. O giroscópio complementa, mas não substitui, o acelerômetro

O giroscópio mede velocidade angular. Ele é útil para detectar rotações, torções e mudanças rápidas de orientação. Integrar velocidade angular pode estimar ângulo:

$$
\theta(t) = \theta(t_0) + \int_{t_0}^{t}\omega(\tau)\,d\tau
$$

Mas integrar também acumula erro: um pequeno *offset* constante vira erro angular crescente. Isso é chamado de deriva. O acelerômetro pode ajudar a corrigir orientação de longo prazo, mas é perturbado por acelerações lineares; a combinação exige filtro complementar ou outro método de fusão sensorial.

No estado atual, os eixos de giro são observáveis em [[janela]] e persistidos em [[esquema-csv]], mas não são integrados em ângulos. Essa decisão é saudável para uma primeira etapa: registrar a medida bruta convertida antes de adicionar hipóteses de filtragem e orientação.

## 9. Senoides, período e frequência

Uma vibração simples pode ser aproximada por:

$$
x(t) = A\sin(2\pi ft + \phi)
$$

`A` é amplitude, `f` é frequência em hertz e `φ` descreve a fase inicial. O período é o tempo de um ciclo completo:

$$
T = \frac{1}{f}
$$

Sistemas reais raramente são uma senoide perfeita. Uma medição pode reunir frequência fundamental, harmônicos, ruído, impactos e mudanças lentas. Ainda assim, a senoide é uma boa peça de construção mental: sinais mais complexos podem ser investigados como combinações de componentes de frequência.

## 10. Do sinal contínuo às amostras do CSV

O movimento físico varia continuamente. O computador, porém, recebe uma sequência de amostras em instantes separados. Se o intervalo de amostragem for aproximadamente constante, a taxa é:

$$
f_s = \frac{1}{\Delta t}
$$

O firmware inclui `tempo_arduino_us`, e [[coletor]] usa esse campo para calcular frequência média, instantânea e suavizada. [[tempo-frequencia-e-perdas]] explica por que esse relógio é preferido ao relógio do PC: ele está mais próximo do momento de aquisição, enquanto a recepção serial inclui atrasos de transporte e agendamento do sistema operacional.

O teorema de Nyquist diz que, para representar uma componente de frequência `f_max` sem ambiguidade ideal, a taxa precisa ser maior que duas vezes essa frequência:

$$
f_s > 2f_{max}
$$

Na engenharia real, “maior que duas vezes” é um limite mínimo teórico, não uma meta confortável. Filtros, ruído, variação de amostragem e interesse em forma de onda recomendam margem. Além disso, o sensor e o firmware precisam ter filtro passa-baixa e taxa configurados de modo coerente; [[arduino_mpu6050]] registra que o DLPF e o divisor de amostragem ainda não são fixados explicitamente no firmware atual.

### Aliasing: quando uma frequência parece outra

Se um sinal rápido é amostrado devagar, seus pontos podem imitar um sinal lento diferente. Essa confusão é chamada de *aliasing*. Depois que a amostra foi registrada, em geral não há como recuperar com certeza a frequência original. A proteção deve ocorrer antes: filtro anti-alias e taxa de amostragem suficiente.

> [!example] Intuição visual
>
> A roda de uma filmagem pode parecer girar devagar ou ao contrário quando a câmera registra poucos quadros. A roda não mudou de comportamento; a taxa de observação tornou a interpretação ambígua.

## 11. Tempo, perdas e qualidade do dado

Uma análise só é tão boa quanto sua cadeia de medição. Cada linha válida da serial possui contador, tempo do Arduino, tempo do PC e seis eixos. [[serial_reader]] converte a linha, [[coletor]] detecta lacunas e [[gravador]] envia o resultado ao CSV sem bloquear a aquisição.

O contador oferece uma verificação independente do tempo. Se ele pula de 10 para 13, duas amostras esperadas não chegaram:

$$
n_{perdidas} = 13 - 10 - 1 = 2
$$

Há também duas perdas conceitualmente diferentes: a amostra pode não chegar pela serial, ou pode chegar ao coletor e não entrar na fila de gravação. [[tempo-frequencia-e-perdas]] diferencia essas situações; tratá-las como uma única métrica esconderia a camada onde o gargalo aconteceu.

Antes de interpretar uma sessão, rode [[testar_dados]]. Ele verifica o contrato do CSV, contagem de campos, saltos detectáveis, valores não finitos e limites das escalas configuradas. Essa validação não prova que o experimento respondeu à pergunta física, mas impede conclusões apoiadas em um arquivo estruturalmente ruim.

## 12. Estatísticas: resumir sem apagar o contexto

Uma janela de amostras contém muitos números. [[statistics]] calcula médias, mediana, mínimo, máximo, pico a pico, desvio padrão, RMS, assimetria e curtose. Cada medida resume uma faceta diferente do sinal.

A média de valores é:

$$
\bar{x} = \frac{1}{N}\sum_{i=1}^{N}x_i
$$

O RMS é:

$$
x_{RMS} = \sqrt{\frac{1}{N}\sum_{i=1}^{N}x_i^2}
$$

Para uma senoide ideal centrada em zero, RMS e amplitude de pico se relacionam por:

$$
x_{RMS} = \frac{A}{\sqrt{2}}
$$

A média ajuda a revelar *offset* e influência da gravidade; RMS resume intensidade sem cancelar metades positivas e negativas. Desvio padrão descreve dispersão em torno da média. Nenhuma dessas métricas revela sozinha a frequência dominante, a forma transitória nem a causa mecânica.

> [!tip] Estatística é resumo, não substituto do sinal
>
> Dois sinais podem ter o mesmo RMS e comportamentos físicos muito distintos. Use as estatísticas da [[janela]] para monitoramento rápido e [[plotar_csv]] para verificar forma, tendências e anomalias antes de concluir algo.

## 13. Erros, ruído, calibração e incerteza

Toda medição é uma mistura de fenômeno e limitações do instrumento. Alguns termos úteis:

- **offset**: valor constante adicionado ao sinal, como um eixo que não fica em zero quando deveria;
- **erro de ganho**: escala multiplicativa incorreta, que aumenta ou reduz todas as leituras;
- **ruído**: flutuações não desejadas;
- **saturação**: o valor real excede a faixa do sensor e o pico é cortado;
- **quantização**: limites de resolução do conversor digital;
- **deriva**: mudança lenta de uma leitura, muitas vezes com temperatura ou tempo.

Uma forma linear simples de correção é:

$$
x_{corrigido} = g\left(x_{medido} - b\right)
$$

`b` representa offset e `g` representa ganho. [[calibrar_vibracao]] usa uma referência RMS conhecida para estimar uma correção de um eixo, sob condições específicas. Calibrar não é “deixar o dado perfeito”: é reduzir um tipo definido de erro em um contexto conhecido. Mudar escala, taxa, filtro, montagem ou faixa de operação pode exigir nova validação.

Também é importante não confundir **precisão** e **exatidão**. Uma série pode repetir valores próximos entre si e ainda estar deslocada do valor verdadeiro. Outra pode ter média correta em muitas repetições, mas oscilar bastante. Bons experimentos relatam como o sensor foi montado, qual foi a escala, qual taxa efetiva foi medida e como os dados foram validados.

## 14. O que os gráficos mostram — e o que não mostram

[[plotar_csv]] desenha os seis eixos ao longo do contador. Ele é excelente para encontrar picos, trechos ausentes, mudança de regime e diferença entre eixos. Contudo, o eixo horizontal é o contador, não o tempo físico. Para estimar frequência com rigor, use `tempo_arduino_us`, a taxa efetiva e métodos apropriados de análise temporal ou espectral.

Um gráfico também não substitui conhecimento do experimento. Um pico pode ser um impacto real, mas pode ser cabo tocando a bancada, sensor frouxo, mudança de orientação ou escala errada após reset. A leitura científica é iterativa:

1. declarar uma hipótese física;
2. montar e medir de forma controlada;
3. validar a integridade do arquivo com [[testar_dados]];
4. observar sinais e estatísticas;
5. comparar com a hipótese e repetir quando necessário.

## 15. Limites atuais e próximos passos honestos

O pipeline atual faz bem o que se propõe: coleta, conserva uma janela em memória, grava, valida e exibe aceleração e giro. Ele não configura explicitamente todos os parâmetros dinâmicos do sensor, não separa gravidade de movimento linear, não calcula FFT e não identifica parâmetros da EDO.

Esses limites não diminuem o projeto; eles definem sua fronteira atual. Evoluções naturais, sempre validadas uma de cada vez, seriam:

- configurar taxa e filtro do MPU6050 no firmware, conforme [[arduino_mpu6050]];
- registrar metadados do ensaio: posição, orientação, fixação, escala e condição operacional;
- usar tempo do Arduino como eixo temporal para análise de frequência;
- aplicar filtros com hipótese e frequência de corte explicitadas;
- estimar espectro, picos e harmônicos depois de confirmar a taxa de amostragem;
- ajustar um modelo massa–mola–amortecedor aos dados somente quando a montagem justificar esse modelo.

## Resumo mental

Vibração é movimento variável no tempo. A EDO massa–mola–amortecedor é uma lente para relacionar força, inércia, elasticidade e perdas; ela não é uma descrição automática de qualquer estrutura. O MPU6050 observa aceleração específica e velocidade angular, que chegam ao computador como amostras com limitações de taxa, filtro e ruído. O software organiza, registra e resume essas observações; a interpretação responsável depende de validação, contexto experimental e comparação entre modelo e realidade.

Ao seguir para a implementação, comece pela [[ARQUITETURA]] para ver como essa cadeia física vira componentes de software e abra [[canvases/fluxo-aquisicao|Fluxo de aquisição]] para acompanhar uma amostra do sensor até o CSV.
#PROJETO_SENSOR_VIBRAÇÃO
