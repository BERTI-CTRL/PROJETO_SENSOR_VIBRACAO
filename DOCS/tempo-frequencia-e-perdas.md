# Tempo, frequência e perdas

Esta página descreve as métricas calculadas por [[coletor]] a partir das amostras de [[serial_reader]]. O protocolo e seus campos estão em [[protocolo-serial]].

## Três noções de frequência

| Métrica | Fórmula | Janela |
|---|---|---|
| `hz_medio` | `(n - 1) / ((t_atual - t_inicial) / 1_000_000)` | sessão desde a primeira amostra |
| `hz_inst` | `1 / ((t_atual - t_anterior) / 1_000_000)` | par de amostras consecutivas |
| `hz_inst_suavizado` | média dos últimos até 100 valores de `hz_inst` | janela móvel de no máximo 100 intervalos |

`t_*` é `tempo_arduino_us`, obtido por `micros()` no Arduino. A primeira amostra só inicializa referências; as métricas são atualizadas apenas se o intervalo for positivo.

## Por que não usar o instante do PC

`timestamp`, medido por `time.perf_counter()` no PC, é útil para observar a recepção e é persistido no CSV. Porém seu intervalo inclui escalonamento do sistema operacional, bloqueio da leitura serial, lote de bytes e trabalho do processo Python. O tempo `micros()` é capturado pelo produtor próximo da amostragem e não sofre essas variações de transporte; por isso o coletor o prefere para calcular Hz. Isso não elimina limites do próprio firmware, como resolução e eventual overflow de `micros()`.

## Perdas com semânticas diferentes

| Sinal | Onde ocorre | Como é contado | Consequência |
|---|---|---|---|
| `amostras_perdidas` | antes ou durante a entrega serial | diferença positiva entre contadores consecutivos menos um | a amostra não chegou ao coletor |
| `amostras_nao_enfileiradas` | após a amostra chegar ao coletor | `Queue.put_nowait` lança `Full` | buffer/UI ainda recebem a amostra, mas ela não é encaminhada ao CSV |

`saltos_contador` conta eventos de salto, enquanto `amostras_perdidas` soma o tamanho de todas as lacunas. Por exemplo, 10→13 gera um salto e duas amostras perdidas. Uma fila cheia não altera o contador do Arduino nem aumenta essas duas métricas; é contabilizada separadamente para não esconder um gargalo de persistência.

Para os cuidados de linhas parciais, consulte [[correcao-pulos-amostras-serial]]. Para a retenção limitada em memória após uma amostra válida, consulte [[buffers]].
