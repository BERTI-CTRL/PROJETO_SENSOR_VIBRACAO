# `realtime/gráfico.py`

**Responsabilidade:** janela minima de depuracao para verificar rapidamente se
`ax` chega ao Python. Ela nao substitui [[janela]], a interface principal.

## Quando usar

Use apenas para diagnóstico rápido: confirmar que a porta abre e que a aceleração X muda quando o sensor é movimentado. Para coleta normal, use `python -m realtime.main`.

```powershell
python realtime\gráfico.py
```

Este arquivo cria `QApplication`, `Janela` e o event loop diretamente no nivel
do modulo, sem guarda `__main__`. Portanto, deve ser executado como script e
nao importado como biblioteca. Ele chama `manager.iniciar()` automaticamente
e, ao fechar, delega o encerramento a [[manager]].

## Como funciona

```text
manager.buffer.ax
        ↓
últimos 500 valores
        ↓
curva única amarela
```

O timer proprio roda a cada `16 ms` (~60 FPS). A cada tick, ele ignora buffers
com menos de dois pontos, le a propriedade de compatibilidade `buffer.ax`,
converte-a em lista e desenha no maximo as ultimas 500 amostras. Essa
propriedade pode copiar uma janela grande quando [[buffers]] esta cheio. Por
isso o script e util para poucos segundos de depuracao, mas nao e indicado para
teste sustentado de desempenho ou coleta longa.

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

Ele usa o mesmo `sensor.manager.manager` da interface principal. Portanto,
tambem abre a porta serial e gera CSV. Ao fechar, `manager.parar()` segue
[[threads-e-encerramento]]. Nao execute este script junto com `realtime.main`,
pois os dois tentariam abrir a mesma porta.

## Referências

- [[manager]] — objeto que inicia a coleta.
- [[buffers]] — origem da propriedade `ax`.
- [[janela]] — interface principal recomendada.
- [[plotar_csv]] — análise posterior do CSV.
