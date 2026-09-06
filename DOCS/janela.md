# `realtime/janela.py`

**Responsabilidade:** mostrar os seis sinais em tempo real e controlar o ciclo de aquisição iniciado por `sensor.manager`.

## O que a janela faz — e o que ela não faz

A janela nao abre a porta serial e nao grava arquivos diretamente. Ela pede
snapshots a [[buffers]], desenha as curvas e apresenta estatisticas. O
[[manager]] cria as threads de coleta e gravacao descritas em
[[threads-e-encerramento]].

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

Os timers sao independentes. A cada 33 ms, o timer grafico obtem **um unico
snapshot** das ultimas 150 amostras, reutiliza um eixo X relativo (`0` ate
`n - 1`) e chama `setData()` apenas nas curvas marcadas. Usar o mesmo snapshot
mantem os seis eixos alinhados e evita seis leituras concorrentes. A faixa X
nao e movimentada a cada frame.

A cada 500 ms, outro timer obtem seu proprio snapshot unico de 150 amostras e
atualiza status, frequencias, contadores e estatisticas dos seis eixos. Assim,
o custo dos textos a 2 FPS nao reduz a cadencia visual aproximada de 30 FPS.

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

O timer de 500 ms chama [[statistics]] para cada eixo usando a mesma janela
recente daquele tick. A interface mostra:

- status da aquisição;
- Hz médio, instantâneo e suavizado;
- total de amostras e ocupação do buffer;
- média, desvio padrão e RMS de cada eixo.

Esses numeros descrevem apenas o trecho recente. A GUI nao acumula historico
completo: o [[buffers]] e circular e a janela pede somente 150 pontos. O
historico persistente da sessao pertence ao [[esquema-csv]].

## Relação com o Plotly

Ao clicar **Parar**, a janela primeiro verifica se houve amostras, chama
`manager.parar()` e espera o encerramento da sessao. Se uma coleta foi
efetivamente encerrada, localiza o CSV mais recente e chama [[plotar_csv]]. O
Plotly abre o **CSV completo**, por isso pode mostrar picos que ja sairam das
ultimas 150 amostras da interface. Parar sem sessao/dados nao reabre um arquivo
antigo; se nenhum CSV existir, o status informa a ausencia.

O import duplicado de `pyqtgraph as pg` no codigo e redundante, mas foi
preservado deliberadamente nesta rodada documental. A configuracao global
desliga antialias e solicita OpenGL antes de os widgets serem criados.

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
