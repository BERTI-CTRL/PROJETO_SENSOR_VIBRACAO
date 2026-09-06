# `sensor/buffers.py`

`BufferSensores` é a janela circular em memória que recebe cada amostra do [[coletor]]. Ele serve a [[janela]] e [[statistics]] sem substituir o histórico integral de gravação do [[esquema-csv]].

## Estrutura e exclusão mútua

O construtor usa capacidade padrão de 10.000 e cria `_dados = np.zeros((tamanho, 9), dtype=np.float64)`. As colunas são, nesta ordem:

| Índice | Coluna |
|---:|---|
| 0 | `tempo_arduino_us` |
| 1 | `timestamp` |
| 2 | `contador` |
| 3–5 | `ax`, `ay`, `az` |
| 6–8 | `gx`, `gy`, `gz` |

`_lock` protege escrita, contagens, snapshots, limpeza e leituras pelas propriedades. `_index` é a próxima posição física de escrita; `_count` é o número de amostras válidas, crescendo até a capacidade.

## Escrita e snapshots

`adicionar(...)` grava os nove valores em `_index`, avança com módulo da capacidade e só aumenta `_count` até o limite. Assim, após encher, a nova amostra substitui a mais antiga.

`snapshot(quantidade)` limita a solicitação a `_count` e devolve um dicionário com as nove chaves. Cada array é uma **cópia**, portanto a UI não observa mutações durante o desenho. Se o buffer ainda não encheu, a faixa é contígua. Se está cheio, há dois ramos:

1. quando o fim pedido não ultrapassa a capacidade, uma única fatia já contém a janela cronológica;
2. quando atravessa o final físico, `np.concatenate` une a faixa final e a inicial.

Nos dois casos a ordem é do mais antigo para o mais novo. `limpar()` apenas reinicia `_index` e `_count`; o array alocado é reutilizado.

## Propriedades de compatibilidade

`tempo_arduino_us`, `timestamp`, `contador`, `ax`, `ay`, `az`, `gx`, `gy` e `gz` chamam `_get_coluna_slice`. Ele entrega a coluna inteira em ordem cronológica: vazia se não há dados, fatia direta antes de encher e concatenação de `_index:` com `:_index` após o wrap-around. Essas propriedades preservam os acessos diretos já usados pela interface.

O comportamento após a capacidade é especialmente importante para [[correcao-buffer-congelando-wrap-around]]: ordem física e ordem cronológica deixam de coincidir quando `_index` volta a zero.

## Limite de memória versus CSV

O buffer existe para leitura rápida e limitada da UI: no máximo 10.000 amostras na configuração padrão e, em geral, uma janela ainda menor solicitada por [[janela]]. Já a fila do [[coletor]] encaminha cada amostra aceita ao gravador, cujo CSV é o histórico persistente da sessão. Uma amostra descartada por fila cheia não chega ao CSV, mas já pode estar no buffer; essa distinção é detalhada em [[tempo-frequencia-e-perdas]].
