# `realtime/janela.py`

**Responsabilidade:** mostrar os seis sinais em tempo real e controlar o ciclo de aquisição iniciado por `sensor.manager`.

## O que a janela faz — e o que ela não faz

A janela não abre a porta serial e não grava arquivos. Ela pede amostras ao buffer, desenha as curvas e apresenta estatísticas. O `manager` cria as threads de coleta e gravação.

```text
manager.buffer.snapshot(150)
        ↓
Janela: dois gráficos + estatísticas
```

## Gráficos

| Gráfico | Curvas | Faixa inicial atual | Motivo |
|---|---|---:|---|
| Aceleração | `ax`, `ay`, `az` | -40 a 40 g | comporta ensaios fortes sem cortar logo no início |
| Giroscópio | `gx`, `gy`, `gz` | -50 a 50 °/s | permite visualizar offsets e giros pequenos |

As faixas são definidas no topo do arquivo por `INTERVALO_EIXO_Y_ACELERAÇÃO` e `INTERVALO_EIXO_Y_GIROSCÓPIO`. Elas são apenas limites visuais; não mudam a escala física configurada no Arduino.

O mouse segue a constante `MOUSE_ATIVADO`. No estado atual ela é `False`, portanto zoom e pan manuais ficam desativados. Para experimentar navegação manual, altere somente essa constante para `True`.

## Atualização e desempenho

```python
INTERVALO_GRAFICO_MS = 33       # aproximadamente 30 FPS
INTERVALO_ESTATISTICAS_MS = 500 # 2 FPS
PONTOS_GRAFICO = 150
```

Em cada atualização gráfica, a janela lê as últimas 150 amostras, reutiliza um eixo X relativo (`0` até `n - 1`) e chama `setData()` apenas nas curvas marcadas. Ela não movimenta a faixa X a cada frame; isso foi removido porque o auto-scroll horizontal prejudicava a aquisição.

O botão **Auto Escala** ativa o auto-range contínuo apenas do eixo Y. Depois do clique, picos novos podem aumentar a faixa Y enquanto X continua fixo. Se a interface ficar pesada em um computador específico, teste sem clicar nesse botão.

## Controles

| Controle | Efeito |
|---|---|
| Iniciar | Pede ao `manager` para criar o coletor e o gravador. |
| Parar | Fecha a sessão, aguarda o flush do CSV e abre o arquivo mais recente no Plotly se houve amostras. |
| Limpar | Limpa as curvas desenhadas, mas não limpa buffer nem interrompe a coleta. No próximo tick, dados do buffer voltam a aparecer. |
| Checkboxes | Mostram/ocultam uma curva; a coleta daquele eixo continua. |
| Auto Escala | Reajusta Y conforme os dados subsequentes; X permanece fixo. |

## Estatísticas mostradas

O timer de 500 ms chama `utils.statistics.calcular_estatisticas()` para cada eixo usando outra janela de 150 amostras. A interface mostra:

- status da aquisição;
- Hz médio, instantâneo e suavizado;
- total de amostras e ocupação do buffer;
- média, desvio padrão e RMS de cada eixo.

Esses números descrevem apenas o trecho recente, não todo o CSV.

## Relação com o Plotly

Ao parar, a janela chama `grafico.plotar_csv.plotar_csv()`. O Plotly abre o **CSV completo**, por isso pode mostrar picos que já saíram das últimas 150 amostras da interface.

## Execução

```powershell
python -m realtime.main
```

## Referências

- [[main]] — cria a aplicação Qt e a `Janela`.
- [[manager]] — inicia e para as threads.
- [[buffers]] — fornece `snapshot(150)` thread-safe.
- [[statistics]] — cálculos exibidos.
- [[plotar_csv]] — gráfico completo aberto depois da parada.
