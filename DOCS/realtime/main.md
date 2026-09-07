# main.py

`realtime/main.py` é o ponto de entrada pequeno da interface principal. Ele cria a única aplicação Qt do processo, constrói [[janela]] e entrega o controle ao loop de eventos. Leitura serial, buffer, estatísticas e CSV pertencem a [[manager]], [[coletor]] e [[gravador_worker]].

## Resumo, entrada e saída

Use a partir da raiz do projeto:

```powershell
python -m realtime.main
```

O arquivo recebe `sys.argv`, repassa esses argumentos para `QApplication` e encerra o processo com o código devolvido por `app.exec()`:

```text
sys.argv → QApplication → Janela() → janela.show() → app.exec() → sys.exit()
```

## Dependências

- `sys`: argumentos do processo e `sys.exit`.
- `PyQt6.QtWidgets.QApplication`: ambiente e event loop Qt.
- [[janela]]: classe da interface criada na linha 20.

## Função `main()`

```python
app = QApplication(sys.argv)
janela = Janela()
janela.show()
sys.exit(app.exec())
```

`QApplication` é criada antes de widgets (linha 16). `Janela()` monta gráficos, painéis e timers, mas a sessão serial continua parada até o clique em **Iniciar**. `show()` exibe a janela, e `app.exec()` bloqueia processando cliques, `QTimer`s e o fechamento.

## Decisões arquiteturais

O arquivo separa o ciclo de vida Qt da composicao da interface. A guarda:

```python
if __name__ == "__main__":
    main()
```

impede que o import abra uma GUI. O arquivo [[realtime/__init__|realtime/__init__.py]] segue o mesmo contrato: importar `realtime` não cria aplicação, widget, timer, thread ou serial.

> [!warning] Uma QApplication por processo
> Este launcher supõe que ainda não exista uma `QApplication`. Em um programa Qt hospedeiro, reutilize a aplicação existente e crie apenas a janela.

## Fechamento e fluxo

Quando a janela fecha, `Janela.closeEvent()` para seus timers e chama `manager.parar()`. O [[manager]] solicita parada ao [[coletor]], aguarda a thread serial, envia a sentinela ao [[gravador_worker]] e aguarda o CSV ser fechado, conforme [[threads-e-encerramento]].

```text
botão Iniciar → manager.iniciar()
serial → coletor → buffers / fila → gravador_worker → CSV
botão Parar ou fechar → manager.parar() → encerramento ordenado
```

## Código explicado, na ordem do arquivo

### Importações (linhas 1–9)

```python
import sys
from PyQt6.QtWidgets import QApplication
from realtime.janela import Janela
```

`sys` fornece tanto `argv` quanto `exit`. `QApplication` é a infraestrutura
obrigatória do Qt antes de qualquer widget. `Janela` vem de [[janela]] e é
importada, em vez de duplicada aqui, para que este arquivo seja somente o
launcher. Nenhuma dessas importações abre a serial diretamente; a importação de
`Janela` apenas disponibiliza a classe e suas dependências.

### Função `main()` (linhas 12–24)

```python
def main():
    app = QApplication(sys.argv)
    janela = Janela()
    janela.show()
    sys.exit(app.exec())
```

`main()` não recebe argumentos Python e não retorna normalmente: a última
instrução levanta o encerramento controlado por `sys.exit` com o inteiro que
`app.exec()` devolve. `sys.argv` mantem as opcoes originais do processo
disponiveis ao Qt. A instancia local `janela` precisa permanecer referenciada
durante o loop; caso contrario, o garbage collector poderia destruir o widget.

`app.exec()` é o único loop explicitamente iniciado neste arquivo. Ele trata
eventos da interface e permite que os `QTimer`s criados por [[janela]] executem
seus slots; o código posterior a essa chamada só ocorre no encerramento.

### Guarda de execução (linhas 27–29)

```python
if __name__ == "__main__":
    main()
```

Quando executado por `python -m realtime.main`, `__name__` vale `"__main__"` e
o launcher é chamado. Quando outro módulo faz `import realtime.main`, a função
fica disponível, mas nenhuma janela é criada. Esse é o contraponto seguro ao
efeito de nível de módulo de [[grafico]].

## Insights para outros projetos

- Mantenha o launcher pequeno e sem regra de negócio.
- Crie a aplicação Qt antes dos widgets e centralize `exec()` em um ponto.
- Use a guarda `__main__` para imports previsiveis.
- Deixe o coordenador de sessão encerrar recursos concorrentes.

## Resumo mental

`main.py` é a porta de entrada Qt: cria uma aplicação, mostra [[janela]] e entra no event loop. A janela controla a coleta; o [[manager]] garante sua parada ordenada.
#PROJETO_SENSOR_VIBRAÇÃO
