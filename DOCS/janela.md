# `realtime/janela.py`

**Responsabilidade:** interface PyQt6 para acompanhar os sinais do MPU6050 em tempo real.

## Visão geral

A classe `Janela` herda de `QMainWindow`. A aquisição serial não acontece na interface: ela é controlada por `sensor.manager`. A interface apenas lê uma cópia curta e segura do buffer para desenhar os dados.

```text
Janela
├── Gráfico de aceleração: Ax, Ay, Az (g)
├── Gráfico de giroscópio: Gx, Gy, Gz (°/s)
├── Painel de sinais: checkboxes para ocultar ou mostrar cada curva
├── Painel de estatísticas: Hz, amostras, média, desvio e RMS
└── Botões: iniciar, parar, limpar e autoescala
```

Os sinais foram separados em dois gráficos porque possuem unidades e escalas distintas. Desenhá-los no mesmo eixo Y faria um dos grupos parecer quase plano ou ficaria cortado.

## Gráficos

| Gráfico | Curvas | Unidade | Escala inicial |
|---|---|---|---|
| Aceleração | `ax`, `ay`, `az` | `g` | -2 a 2 |
| Giroscópio | `gx`, `gy`, `gz` | `°/s` | -20 a 20 |

Cada gráfico é um `pyqtgraph.PlotWidget`, com fundo preto, grade e controles de mouse desativados. O auto-range começa desativado para evitar custo extra de cálculo e redesenho a cada atualização.

O método `autoescala()` ativa o auto-range somente no eixo Y dos dois gráficos, cada um usando somente as suas próprias curvas. O eixo X permanece fixo em `0–149`; por isso o gráfico acompanha picos de sinal sem reposicionar a visualização horizontal.

## Atualização em tempo real

```python
INTERVALO_GRAFICO_MS = 33       # aproximadamente 30 atualizações visuais por segundo
INTERVALO_ESTATISTICAS_MS = 500 # 2 atualizações por segundo
PONTOS_GRAFICO = 150            # últimas 150 amostras
```

Em cada tick gráfico, `atualizar_grafico()` executa este fluxo:

```text
buffer.snapshot(150)
        ↓
reutiliza eixo X relativo: 0 até n - 1
        ↓
atualiza as curvas marcadas nos checkboxes
        ↓
```

O eixo X é relativo às últimas amostras e é reutilizado entre atualizações. Assim, a interface não precisa reposicionar a faixa X em todo frame, reduzindo a carga de renderização.

## Estatísticas

`atualizar_estatisticas()` usa outro `QTimer`, a cada 500 ms. Ela exibe:

- estado da aquisição;
- Hz médio, instantâneo e suavizado;
- total de amostras e ocupação do buffer;
- média, desvio padrão e RMS de `ax`, `ay`, `az`, `gx`, `gy` e `gz`.

As estatísticas também usam o snapshot das últimas 150 amostras e são calculadas por `utils.statistics.calcular_estatisticas`.

## Métodos principais

| Método | Função |
|---|---|
| `criar_grafico()` | Cria e configura os dois gráficos e suas seis curvas. |
| `atualizar_grafico()` | Lê o buffer e redesenha apenas as curvas visíveis. |
| `atualizar_estatisticas()` | Atualiza os rótulos de aquisição e a tabela de métricas. |
| `limpar_grafico()` | Limpa as seis curvas, sem parar a aquisição. |
| `iniciar()` / `parar()` | Delegam o controle ao `manager`; ao parar uma sessão com dados, abrem o CSV resultante no Plotly. |
| `closeEvent()` | Para os timers e encerra a aquisição antes de fechar. |

## Execução

```powershell
python -m realtime.main
```

## Referências

- [[main]] — ponto de entrada da interface.
- [[statistics]] — cálculos exibidos no painel.
- [[buffers]] — snapshot thread-safe do buffer circular.
- [[ARQUITETURA]] — fluxo completo entre Arduino, coleta, CSV e interface.
