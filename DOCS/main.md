# `realtime/main.py`

**Responsabilidade:** ponto de entrada da interface principal.

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

`main.py` não lê serial e não calcula estatísticas. Ele cria a aplicação Qt e entrega o restante do trabalho para `realtime.janela.Janela`.

## Execução recomendada

```powershell
python -m realtime.main
```

O formato com `-m` garante que os imports `realtime.*` e `sensor.*` sejam resolvidos a partir da raiz do projeto.

## O que acontece ao fechar

`Janela.closeEvent()` para os timers e chama `manager.parar()`. O manager encerra o coletor, descarrega o CSV e fecha o gravador antes do processo Qt terminar.

## Relação com outros arquivos

- [[janela]] — interface criada por este arquivo.
- [[manager]] — encerra as threads quando a janela fecha.
- [[ARQUITETURA]] — visão do fluxo completo.
