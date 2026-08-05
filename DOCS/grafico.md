# `realtime/gráfico.py`

**Responsabilidade:** janela mínima para verificar rapidamente se `ax` chega ao Python.

## Quando usar

Use apenas para diagnóstico rápido: confirmar que a porta abre e que a aceleração X muda quando o sensor é movimentado. Para coleta normal, use `python -m realtime.main`.

```powershell
python realtime\gráfico.py
```

Este arquivo inicia `manager.iniciar()` automaticamente e, ao fechar a janela, chama `manager.parar()`.

## Como funciona

```text
manager.buffer.ax
        ↓
últimos 500 valores
        ↓
curva única amarela
```

O timer roda a cada `16 ms` (~60 FPS). Ele acessa a propriedade `buffer.ax`, que pode copiar uma janela grande quando o buffer está cheio. Por isso é útil para poucos segundos de depuração, mas não é a opção indicada para teste sustentado de desempenho ou coleta longa.

## Diferença para a janela principal

| Aspecto | `gráfico.py` | `janela.py` |
|---|---|---|
| Sinais | apenas `ax` | seis eixos, separados em dois gráficos |
| Atualização | ~60 FPS | ~30 FPS (`33 ms`) |
| Janela de dados | até 500 pontos | últimas 150 amostras via `snapshot()` |
| Controles | nenhum | iniciar, parar, limpar, autoescala e checkboxes |
| Estatísticas | não | Hz, média, desvio e RMS |
| Uso | confirmação rápida | monitoramento normal |

## Relação com o pipeline

Ele usa o mesmo `sensor.manager.manager` da interface principal. Portanto, também abre a porta serial e gera CSV. Não execute este script junto com `realtime.main`, pois os dois tentariam abrir a mesma porta.

## Referências

- [[manager]] — objeto que inicia a coleta.
- [[janela]] — interface principal recomendada.
- [[plotar_csv]] — análise posterior do CSV.
