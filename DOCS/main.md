# `realtime/main.py`

`realtime/main.py` e o ponto de entrada da interface principal descrita em
[[janela]]. Ele apenas estabelece o ciclo de vida do Qt; leitura serial,
buffer, estatisticas e gravacao ficam nos componentes especializados.

## O que o arquivo faz

```text
QApplication
    ↓
Janela()
    ↓
janela.show()
    ↓
app.exec()  ← loop de eventos do Qt
```

`QApplication(sys.argv)` e criado uma unica vez e antes de qualquer widget.
Em seguida `Janela()` monta graficos e paineis, `show()` torna a janela visivel
e `app.exec()` assume o loop de eventos bloqueante. `sys.exit(...)` devolve ao
processo o codigo com que o Qt encerrou.

A guarda `if __name__ == "__main__"` impede que a GUI seja aberta apenas por
importar o modulo. `realtime/__init__.py` tambem permanece sem efeitos
colaterais: importar o pacote nao cria aplicacao, timers nem widgets.

## Execução recomendada

```powershell
python -m realtime.main
```

O formato com `-m` garante que os imports `realtime.*` e `sensor.*` sejam resolvidos a partir da raiz do projeto.

## O que acontece ao fechar

`Janela.closeEvent()` para os dois timers e chama `manager.parar()`. O
[[manager]] encerra o [[coletor]], aguarda a persistencia restante e fecha o
gravador antes do processo Qt terminar, conforme [[threads-e-encerramento]].

## Relação com outros arquivos

- [[janela]] — interface criada por este arquivo.
- [[manager]] — coordena a sessao e encerra as threads.
- [[threads-e-encerramento]] — ordem da parada segura.
- [[ARQUITETURA]] — visao do fluxo completo.
