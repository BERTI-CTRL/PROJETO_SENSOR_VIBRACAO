# Meteor Dash — jogo com MPU6050

Desvie dos meteoros movendo a nave com a inclinação do MPU6050. O jogo também pode ser demonstrado somente com o teclado.

## Instalar e executar

No PowerShell, na raiz do projeto:

```powershell
# Instala a dependência caso o ambiente ainda não tenha Pygame.
.\.venv\Scripts\python.exe -m pip install pygame

# Abre o jogo.
.\.venv\Scripts\python.exe -m game.main
```

Se usar `uv`, `uv sync` também instala a dependência registrada em `pyproject.toml`.

## Controles

| Tecla | Ação |
|---|---|
| `C` | Mede por 1,5 s a posição neutra do sensor e começa a partida. Deixe o conjunto parado. |
| `I` | Inverte esquerda/direita se a nave responder ao contrário da inclinação. |
| `←` / `→` | Controle reserva por teclado; funciona até quando o sensor não está conectado. |
| `R` | Reinicia a partida e retorna à calibração. |
| `Esc` | Fecha o jogo. |

## Conectar o sensor

1. Grave o firmware em `arduino/mpu-6050/mpu-6050.ino` e conecte o Arduino.
2. Feche o Serial Monitor e qualquer outra parte deste projeto que esteja usando a porta.
3. O jogo usa `COM4` a `230400` baud. Caso o Arduino esteja em outra porta, altere `PORTA_SERIAL` em `sensor/config.py`.
4. Abra o jogo, mantenha o sensor na posição em que pretende jogar e pressione `C`.

Na montagem fotografada, os dados parados existentes mostram `ax` próximo de `+1 g` e `ay` próximo de zero. Por isso, o controle usa mudanças em `ay`. Caso a direção fique invertida, a tecla `I` corrige sem alterar nenhum código.

## Diagnóstico rápido

- **"Sem sensor" no rodapé:** confirme porta, cabo, Serial Monitor fechado e o atraso inicial de aproximadamente 10 s do firmware.
- **Nave se mexe parada:** calibre outra vez com `C`; o jogo aplica uma zona morta para filtrar ruído pequeno.
- **Nave vai para o lado errado:** pressione `I`.
- **Quer testar sem hardware:** pressione `C` e use as setas.

O jogo lê a serial em uma thread própria e não grava CSV. Dessa forma, ele não altera o pipeline de coleta e análise do restante do projeto.
#PROJETO_SENSOR_VIBRAÇÃO
