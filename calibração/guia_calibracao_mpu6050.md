# Guia de calibração e uso do MPU6050 em medições de vibração

Este guia explica como usar uma referência de vibração conhecida para caracterizar o MPU6050 deste projeto e, depois, usar as leituras corrigidas em uma máquina real.

> Escopo: este documento descreve o procedimento. Por enquanto, ele não altera o firmware nem o código Python.

## 1. Ideia central

O caminho de uma medição calibrada é:

~~~
referência conhecida
        ↓ compara
MPU6050 do projeto ──► calcula erro ──► cria calibração
                                                ↓
                               novas medições ──► valores corrigidos
~~~

O firmware atual já converte valores brutos do sensor para g e °/s. Isso é uma conversão de unidade usando a sensibilidade nominal do componente. Não é uma calibração completa.

Calibrar significa comparar o valor medido com um valor verdadeiro conhecido e estimar como corrigir a diferença. Esse processo é necessário porque cada módulo pode apresentar pequeno deslocamento de zero, erro de ganho, ruído, desalinhamento entre eixos e mudança de comportamento com temperatura.

O MPU6050 permite faixas de ±2, ±4, ±8 e ±16 g no acelerômetro, e ±250, ±500, ±1000 e ±2000 °/s no giroscópio. O firmware atual usa ±16 g e ±2000 °/s. A especificação também informa tolerâncias iniciais de offset e sensibilidade. [MPU-6000/MPU-6050 Product Specification — TDK InvenSense](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet.pdf)

## 2. Que erros precisam ser investigados

| Tipo de erro | Exemplo | Efeito prático | Como investigar |
|---|---|---|---|
| Offset | parado, gx = -3 °/s | parece haver giro inexistente | medir em repouso e subtrair a média |
| Ganho | referência 1 g, sensor 0,96 g | amplitude fica errada | comparar valores conhecidos |
| Desalinhamento | excitação em X aparece em Y | eixo físico não coincide com o eixo medido | alinhar montagem ou usar matriz 3×3 |
| Sensibilidade cruzada | vibrar X altera Y/Z | um eixo vaza para outro | testar cada eixo separadamente |
| Ruído | sinal varia parado | falsos eventos em vibração pequena | calcular desvio/RMS em repouso |
| Temperatura | offset muda após aquecer | calibração fria deixa de valer | ensaiar em mais de uma temperatura |
| Saturação | curva corta no máximo | o pico real é perdido | escolher fundo de escala adequado |
| Erro de tempo | frequência medida diverge | FFT e fase ficam incorretas | validar taxa de amostragem |

Cada teste existe por um motivo. Um teste parado mede offset e ruído, mas não prova que a amplitude está correta. Uma senoide conhecida mede ganho e frequência, mas não substitui a calibração estática de todos os eixos.

## 3. Modelo matemático mínimo

Comece pelo modelo simples, com offset e ganho por eixo:

~~~
valor_corrigido = ganho × (valor_medido - offset)
~~~

Exemplos:

~~~
ax_corrigido = ganho_ax × (ax_medido - offset_ax)
gz_corrigido = ganho_gz × (gz_medido - offset_gz)
~~~

Esse modelo corrige os dois erros mais frequentes: valor diferente de zero em repouso e amplitude proporcionalmente incorreta.

Em uma etapa mais avançada, pode-se usar:

~~~
vetor_corrigido = M × (vetor_medido - b)
~~~

b contém os offsets de X, Y e Z. M é uma matriz 3×3 que representa ganhos, desalinhamentos e sensibilidade cruzada. Para este projeto, comece com offset e ganho por eixo; uma matriz só é justificada se os testes demonstrarem que ela é necessária.

## 4. Preparação do ensaio

### 4.1 Definir o objetivo

Antes de testar, responda:

1. Qual equipamento será observado?
2. Qual é a menor vibração que precisa ser detectada?
3. Qual é a maior frequência relevante?
4. Qual é a maior aceleração ou velocidade angular esperada?
5. O sensor ficará fixo ou sua orientação mudará?

**Por que:** não existe configuração ideal para todos os casos. Uma faixa grande evita saturação, mas reduz a resolução para sinais pequenos. Uma taxa de amostragem pequena pode impedir a observação da frequência de interesse.

### 4.2 Fixar e orientar o sensor

Prenda o módulo rigidamente ao corpo de teste. Marque os eixos do MPU6050 e registre sua correspondência com os eixos físicos da máquina.

~~~
Máquina: longitudinal / transversal / vertical
              │              │              │
Sensor:       X              Y              Z
~~~

**Por que:** fita flexível, parafuso frouxo, cabo puxando a placa ou base instável podem criar vibrações da montagem, e não da máquina. Sem a orientação documentada, um valor em ax não possui significado físico claro.

### 4.3 Registrar condições

Para cada ensaio, registre:

- data, duração e identificação do teste;
- identificação do módulo;
- versão do firmware e do código Python;
- fundo de escala e taxa de amostragem observada;
- ponto de fixação e orientação;
- temperatura aproximada;
- tipo de referência;
- frequência, amplitude e unidade da referência.

**Por que:** um CSV sem contexto não permite descobrir se uma mudança posterior veio do sensor, da montagem, da máquina ou do software.

## 5. Calibração estática do giroscópio

O giroscópio ideal deveria apresentar 0 °/s quando está imóvel. Na prática, há um pequeno offset.

### Procedimento

1. Fixe o sensor em uma superfície estável.
2. Não toque no conjunto durante a captura.
3. Aguarde alguns minutos se a aplicação for sensível a temperatura.
4. Grave entre 20 e 60 segundos.
5. Calcule a média de gx, gy e gz.

Exemplo:

~~~
gx médio = -3,50 °/s
gy médio =  0,22 °/s
gz médio = -0,41 °/s
~~~

A correção correspondente é:

~~~
gx_corrigido = gx_medido - (-3,50)
gy_corrigido = gy_medido - ( 0,22)
gz_corrigido = gz_medido - (-0,41)
~~~

### Por que usar média

Uma leitura única contém ruído. A média de muitas amostras reduz a influência do ruído e aproxima o resultado do comportamento de repouso daquele módulo.

Calcule também desvio padrão e RMS em repouso.

**Por que:** essas métricas representam o piso de ruído. Um algoritmo de detecção de giro ou vibração deve usar limites acima desse piso para evitar falsos alarmes.

### Limite da correção

O offset pode mudar com a temperatura. Um valor medido com o sensor frio pode não valer depois de vários minutos perto de um motor. Para maior precisão, repita o ensaio em diferentes temperaturas e crie uma correção dependente da temperatura.

## 6. Calibração estática do acelerômetro: teste das seis faces

A gravidade é uma referência conhecida. Quando o sensor está parado, o vetor aceleração tem magnitude próxima de 1 g.

| Posição do módulo | Referência esperada |
|---|---|
| X apontando para cima | ax = +1 g |
| X apontando para baixo | ax = -1 g |
| Y apontando para cima | ay = +1 g |
| Y apontando para baixo | ay = -1 g |
| Z apontando para cima | az = +1 g |
| Z apontando para baixo | az = -1 g |

Em cada posição, aguarde o sinal estabilizar e calcule a média do eixo relevante.

Para um eixo, chame de m_mais a média na posição +1 g e m_menos a média na posição -1 g:

~~~
offset = (m_mais + m_menos) / 2
ganho  = 2 / (m_mais - m_menos)

a_corrigida = ganho × (a_medida - offset)
~~~

Exemplo: se o eixo X medir +0,97 g e -1,03 g:

~~~
offset = (0,97 + -1,03) / 2 = -0,03 g
ganho  = 2 / (0,97 - -1,03) = 1,00
ax_corrigido = ax_medido + 0,03
~~~

### Por que usar seis faces

Uma única posição não separa corretamente offset e ganho. As posições opostas fornecem dois pontos conhecidos por eixo, +1 g e -1 g, permitindo calcular os dois parâmetros.

### Cuidados

- Não mova o sensor durante a captura.
- Os outros dois eixos devem ficar próximos de 0 g.
- Valores grandes em eixos não alinhados com a gravidade podem indicar desalinhamento, montagem imperfeita ou ruído.

## 7. Calibração dinâmica com vibração conhecida

Depois da calibração estática, use a bancada de vibração para conferir amplitude e frequência ao longo da faixa de interesse.

### 7.1 Montagem recomendada

~~~
Mesa vibratória / excitador
        │
        ├── sensor de referência calibrado
        └── MPU6050 do projeto
~~~

Os dois sensores devem ficar no mesmo corpo rígido, próximos, alinhados ao eixo de excitação e fixados de forma semelhante.

**Por que:** pontos diferentes de uma estrutura podem vibrar de formas diferentes. Nesse caso, a diferença entre sensores pode ser mecânica e não um erro de medição.

### 7.2 Referência de vibração

A referência pode ser:

- acelerômetro calibrado;
- mesa vibratória com aceleração controlada;
- sistema que informe deslocamento e frequência de uma senoide.

Se o sistema fornecer deslocamento de pico x_pico e frequência f:

~~~
a_pico = (2πf)² × x_pico
a_rms = a_pico / √2
~~~

**Por que distinguir pico, pico a pico e RMS:** são formas diferentes de expressar a amplitude. Comparar 1 g RMS de uma referência com 1 g de pico do sensor cria um erro aparente mesmo se os dois estiverem corretos.

### 7.3 Plano inicial de ensaios

| Ensaio | Frequência | Amplitude | Objetivo |
|---|---:|---:|---|
| repouso | 0 Hz | sem excitação | offset e ruído |
| 1 | 5 Hz | baixa | resposta em baixa frequência |
| 2 | 10 Hz | baixa | validar ganho inicial |
| 3 | 20 Hz | média | resposta no centro da banda |
| 4 | 40 Hz | média | verificar resposta em frequência |
| 5 | maior frequência útil | segura | verificar limite operacional |

Repita cada condição ao menos três vezes.

**Por que repetir:** um único ensaio pode conter ruído, fixação imperfeita ou erro operacional. Repetições permitem avaliar a repetibilidade.

### 7.4 O que comparar

| Medida | Pergunta respondida |
|---|---|
| média | há offset durante o ensaio? |
| RMS | a intensidade coincide com a referência? |
| pico | há saturação ou subestimação de impacto? |
| frequência dominante | o sinal aparece na frequência imposta? |
| fase, se houver sincronismo | existe atraso importante? |
| eixos não excitados | há acoplamento mecânico ou sensibilidade cruzada? |

O script grafico/plotar_csv.py ajuda a fazer inspeção visual. Para medir frequência e fase quantitativamente, o próximo passo é incluir FFT e comparação automática com a referência.

## 8. Vibração linear não calibra o giroscópio

Uma mesa que sobe, desce ou se move lateralmente produz aceleração linear. Ela é adequada para caracterizar o acelerômetro, mas não fornece necessariamente uma velocidade angular conhecida.

O giroscópio mede rotação. Para calibrá-lo dinamicamente, use uma referência de rotação:

- mesa giratória;
- rate table;
- eixo ou motor com velocidade angular conhecida;
- mecanismo que faça rotações controladas em cada eixo.

Um plano simples é medir 0, +90, -90, +180 e -180 °/s em cada eixo.

**Por que usar os dois sentidos:** valores positivos e negativos ajudam a separar offset de erro de ganho, da mesma forma que as faces opostas do acelerômetro.

## 9. Taxa de amostragem e aliasing

O projeto recebe aproximadamente 200 Hz, mas a taxa real deve ser conferida pelos valores de Hz da janela e pelos tempos do Arduino.

Pelo critério de Nyquist, uma taxa fs só representa frequências menores que fs / 2. Com fs próximo de 200 Hz, o limite teórico está perto de 100 Hz.

Na prática, use margem:

~~~
fs ≥ 5 a 10 × maior frequência de interesse
~~~

Exemplo: para analisar até 30 Hz, busque pelo menos 150 a 300 Hz estáveis.

**Por que:** frequências acima da capacidade de amostragem podem aparecer no CSV como frequências falsas mais baixas. Esse efeito, chamado aliasing, pode levar a um diagnóstico errado.

Também monitore saltos no contador do Arduino. Diminuir o intervalo de redesenho da janela não aumenta a taxa física do sensor; apenas aumenta a frequência de atualização visual.

## 10. Calibrar não é validar

- **Calibrar:** usar dados conhecidos para calcular coeficientes.
- **Validar:** usar novos ensaios para verificar se os coeficientes funcionam.

Procedimento:

1. Reserve parte dos ensaios para validação.
2. Calcule offsets e ganhos com os dados de calibração.
3. Aplique a correção nos dados reservados.
4. Compare medida corrigida e referência.
5. Registre os erros.

Métricas úteis:

~~~
erro absoluto = |medida_corrigida - referência|
erro relativo = erro absoluto / |referência|
RMSE = raiz da média dos erros ao quadrado
~~~

**Por que validar em dados novos:** um ajuste pode parecer excelente apenas para os dados usados no cálculo. Um ensaio independente mostra se a correção realmente funciona em outras condições.

Defina um critério de aceitação adequado à aplicação, por exemplo: erro RMS de amplitude menor que 5% entre 5 e 40 Hz no eixo vertical.

## 11. Como levar a calibração para este projeto

O ponto adequado para aplicar a correção é depois da leitura serial e antes do buffer, da janela e do CSV:

~~~
Arduino
   ↓
serial_reader.py: lê e converte a linha
   ↓
coletor.py: aplica calibração  ← local recomendado
   ↓
BufferSensores → Janela → CSV → Plotly
~~~

**Por que nesse ponto:** todos os consumidores recebem a mesma medida corrigida. Corrigir apenas na janela deixaria o CSV sem correção; corrigir apenas no Plotly faria a análise posterior divergir da visualização em tempo real.

### Preservar valores brutos

Em uma evolução do projeto, mantenha dados brutos e corrigidos:

~~~
ax_bruto, ay_bruto, az_bruto, gx_bruto, gy_bruto, gz_bruto
ax_corrigido, ay_corrigido, az_corrigido, gx_corrigido, gy_corrigido, gz_corrigido
versao_da_calibracao
~~~

**Por que:** se um coeficiente for aperfeiçoado, os CSVs antigos poderão ser reprocessados. Sem os dados brutos, não há como auditar a origem de um resultado.

### Guardar coeficientes fora do código

Armazene a calibração em um arquivo, por exemplo:

~~~
calibracao_mpu6050_modulo_01.json
~~~

Esse arquivo deve conter identificação do módulo, data, responsável, offsets, ganhos, fundo de escala, faixa validada, temperatura, versão do procedimento e erros de validação.

**Por que:** coeficientes pertencem ao módulo e ao ensaio, não ao código universal. Separá-los permite trocar sensor ou repetir a calibração sem modificar a aplicação.

## 12. Uso em um sistema real

Depois da calibração, a questão passa a ser: o comportamento da máquina mudou?

### 12.1 Criar uma linha de base

1. Fixe o sensor no ponto definitivo.
2. Registre várias sessões com a máquina em condição normal.
3. Calcule RMS, pico, desvio padrão e frequência dominante.
4. Registre como essas métricas mudam com carga, rotação e temperatura.

**Por que:** o mesmo valor de vibração pode ser normal em uma máquina e anormal em outra. A linha de base permite comparar o equipamento com ele próprio.

### 12.2 Métricas úteis

| Métrica | Uso prático |
|---|---|
| RMS | intensidade global da vibração |
| pico | impacto ou evento máximo |
| pico a pico | variação total |
| desvio padrão | instabilidade/dispersão |
| frequência dominante | repetição ligada à rotação ou mecanismo |
| energia por faixa | intensidade em banda específica |
| giro médio | rotação sustentada |
| integral do giro | ângulo no curto prazo, com cautela contra drift |

Fluxo típico:

~~~
coletar janela
   ↓
aplicar calibração e remover baseline quando apropriado
   ↓
calcular RMS, pico e FFT
   ↓
comparar com linha de base normal
   ↓
registrar tendência ou gerar alerta
~~~

### Gravidade e aceleração linear

O acelerômetro mede gravidade e aceleração linear. Se o sensor tiver orientação fixa, um baseline médio pode destacar a vibração. Se a orientação mudar, é necessário estimar a orientação antes de separar gravidade e vibração.

**Por que:** inclinar o sensor pode mudar um eixo em aproximadamente 1 g mesmo sem vibração. Interpretar essa mudança como defeito mecânico gera falso alarme.

## 13. Problemas frequentes

| Problema | Consequência | Prevenção |
|---|---|---|
| sensor solto | mede a montagem, não a máquina | fixação rígida e repetível |
| escala alterada no .ino sem mudar divisor | unidade incorreta | atualizar configuração e conversão juntas |
| comparar pico com RMS | erro artificial de amplitude | registrar tipo de amplitude |
| usar mesa linear para validar giro | não há referência angular | usar mesa giratória ou rate table |
| usar apenas uma frequência | não mede resposta em frequência | ensaiar vários pontos |
| salvar somente dado corrigido | impede revisão futura | guardar bruto, corrigido e versão |
| ignorar temperatura | offset muda em uso | ensaiar faixa térmica relevante |
| taxa insuficiente | aliasing e frequências falsas | validar fs antes de analisar |
| não registrar orientação | eixos perdem significado | documentar montagem |

## 14. Checklist

### Antes

- [ ] Sensor fixado, eixos identificados e orientação anotada.
- [ ] Fundo de escala, porta e baud rate conferidos.
- [ ] Referência conhecida identificada.
- [ ] Frequência, amplitude, unidade e duração definidas.

### Durante

- [ ] MPU6050 e referência estão no mesmo corpo rígido.
- [ ] Não existem mensagens de depuração na serial.
- [ ] Hz observado atende a frequência de interesse.
- [ ] O contador não apresenta saltos.
- [ ] Cada condição foi repetida ao menos três vezes.

### Depois

- [ ] Aquisição foi encerrada normalmente para finalizar o CSV.
- [ ] Dados de calibração e validação foram separados.
- [ ] Offsets, ganhos e erros foram registrados.
- [ ] A versão da calibração foi armazenada.

## 15. Roteiro recomendado para este projeto

1. Confirmar taxa de coleta estável e ausência de saltos no contador.
2. Medir 30 segundos em repouso para offset e ruído do giroscópio.
3. Fazer o teste das seis faces para offset e ganho do acelerômetro.
4. Ensaiar o acelerômetro em referência vibratória com várias frequências.
5. Ensaiar o giroscópio em referência de rotação, se ele for relevante.
6. Calcular coeficientes e guardá-los com metadados.
7. Validar em ensaios não usados no ajuste.
8. Só depois integrar a correção em sensor/coletor.py.
9. Criar baseline do equipamento real e acompanhar tendências.

Esse processo evita pular diretamente para um alarme sem saber se o sensor está medindo corretamente. Primeiro mede-se o erro, depois corrige-se, valida-se e só então usa-se o dado para interpretar a máquina.

## Referências

- [MPU-6000/MPU-6050 Product Specification — TDK InvenSense](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet.pdf)
- [Firmware atual do projeto](../arduino/mpu-6050/mpu-6050.ino)
- [Coletor, local recomendado para correção futura](../sensor/coletor.py)
- [Plotador de CSV para inspeção visual](../grafico/plotar_csv.py)
