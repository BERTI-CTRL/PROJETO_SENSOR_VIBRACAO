# `dados/testar_dados.py`

**Responsabilidade:** validar uma captura CSV já finalizada e produzir, no terminal, um relatório de continuidade, taxa, faixas físicas e valores inválidos. Este programa não abre a porta serial, não inicia threads e não modifica o CSV.

> Não confunda este arquivo com [[teste_manager]]. `sensor/teste_manager.py` observa uma aquisição viva; `dados/testar_dados.py` analisa uma captura existente depois que ela foi gravada.

## Uso

```powershell
# Escolhe automaticamente o CSV mais recente cujo nome segue o padrão do gravador.
python dados\testar_dados.py

# Valida uma captura específica.
python dados\testar_dados.py dados\dados_aceleracao_giro-2026-08-28_15-29-44.csv
```

O processo termina com código `0` somente se todos os testes passarem. Código `1` significa arquivo ausente, estrutura inválida ou uma inconsistência detectada; isso permite usá-lo em uma verificação automática simples.

## Contrato de entrada

O programa lê o arquivo manualmente, ignora linhas em branco e exige exatamente o cabeçalho e a ordem definidos em [[esquema-csv]]:

```text
tempo_arduino_us,tempo_relogio_pc,contador,ax,ay,az,gx,gy,gz
```

Cada linha de dados precisa ter nove campos conversíveis para `float`. Cabeçalho reordenado, campo faltante, coluna extra ou valor não numérico interrompem a análise antes dos cálculos. O uso de `float` não muda o arquivo: ele apenas forma uma matriz NumPy em memória.

## O que é verificado

| Verificação | Fonte e regra | Interpretação |
|---|---|---|
| Continuidade | `np.diff(contador) > 1` | Cada diferença maior que um é um salto; a perda estimada é a soma de `diferença - 1`. |
| Taxa | `tempo_arduino_us` em microssegundos | Calcula Hz instantâneo para intervalos positivos e Hz médio para a sessão. Consulte [[tempo-frequencia-e-perdas]]. |
| Faixas | aceleração entre -16 e 16 g; giro entre -2000 e 2000 °/s | São as escalas físicas atualmente configuradas no firmware; um valor fora da faixa reprova o resultado. |
| Tempo do PC | `np.diff(tempo_relogio_pc) < 0` | Não deve haver regressão do relógio monotônico de recepção. Ele não é usado para o cálculo de Hz. |
| Finitude | `np.isfinite` em toda a matriz | `NaN` e infinito reprovam o arquivo. |

`saltos` conta eventos de lacuna, enquanto `perdidas` mede o número de amostras que faltaram dentro dessas lacunas. Por exemplo, 10 → 13 significa um salto e duas perdas. Essa leitura é compatível com a semântica explicada em [[tempo-frequencia-e-perdas]], mas o teste é posterior: ele não sabe em qual estágio a perda ocorreu.

## Relatório e sucesso

O relatório mostra quantidade de amostras, extremos, média, desvio padrão e RMS de cada eixo, além de duração e taxa. Quando há saltos, mostra os primeiros cinco para orientar a inspeção. Ao final, `PASSOU` exige simultaneamente:

- nenhum salto no contador;
- nenhum delta negativo do relógio do PC;
- nenhum `NaN` ou infinito;
- nenhum valor de sensor fora da faixa atual.

Uma captura pode falhar e ainda ser útil para diagnóstico. Antes de descartar dados, confira o cabeçalho em [[esquema-csv]], os detalhes de tempo/perdas em [[tempo-frequencia-e-perdas]] e a configuração que produziu o ensaio.

## Próximas análises

Depois de uma captura consistente, use [[plotar_csv]] para inspeção visual de todo o histórico. Se a vibração de referência for conhecida em g RMS e um eixo for excitado, [[calibrar_vibracao]] pode gerar um JSON de offset e ganho. A validação do CSV não aplica calibração nem prova que a amplitude está correta.
