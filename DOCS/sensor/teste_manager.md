# teste_manager.py

## Resumo

Este é o teste interativo sem GUI do pipeline real. Inicia o singleton [[manager]], acompanha o buffer no terminal e encerra as threads/CSV com `Ctrl+C`.

## Dependências, entrada e saída

Importa `time` e `manager` de [[manager]]. Não define classe, função ou parâmetros: seu corpo de módulo é executável. A entrada é a serial configurada no coletor; as saídas são mensagens de terminal e o CSV produzido pelo pipeline.

## Fluxo top-down

Ao importar ou executar, inicia imediatamente:

```python
print("Iniciando aquisição...")
manager.iniciar()
```

O `while True` consulta `manager.buffer.vazio()`. Se há amostra, lê `manager.buffer.contador[-1]` e mostra contador recente e `len(manager.buffer.contador)`. `time.sleep(1)` reduz atualização a aproximadamente uma vez por segundo.

`KeyboardInterrupt` imprime encerramento e o `finally` sempre chama:

```python
manager.parar()
print("Fim do teste.")
```

Assim segue o protocolo de [[threads-e-encerramento]]: encerra coleta, envia sentinela e fecha CSV.

> [!warning]
> Importar este arquivo já inicia serial, threads e persistência. Não é módulo passivo para biblioteca ou automação sem hardware.

> [!warning]
> `contador[-1]` só é seguro porque há `vazio()` antes. Para leitura concorrente mais elaborada, [[buffers]].snapshot() oferece cópia isolada.

## Uso

```powershell
python -m sensor.teste_manager
```

Use `Ctrl+C` para encerrar. Diferentemente de [[testar_dados]], que inspeciona um CSV existente, este módulo observa aquisição viva. Para gráficos, use [[janela]].

## Código explicado, na ordem do arquivo

### Imports e efeito de carregamento

```python
import time
from sensor.manager import manager

print("Iniciando aquisição...")
manager.iniciar()
```

`time` fornece a pausa periódica; importar `manager` cria/acessa o singleton. As duas últimas linhas não ficam em função ou `__main__`: executam tanto ao importar quanto ao rodar o módulo. `iniciar()` começa sessão se não houver thread viva.

### Loop de observação

```python
try:
    while True:
        if not manager.buffer.vazio():
            contador = manager.buffer.contador[-1]
            print(...)
        time.sleep(1)
```

O `while True` não possui término interno; depende de interrupção. O `if` evita indexar coluna vazia. `contador[-1]` é a amostra mais recente fornecida pela propriedade; `len(manager.buffer.contador)` é a quantidade atualmente retida. `sleep` impede impressão contínua.

### `KeyboardInterrupt` e `finally`

```python
except KeyboardInterrupt:
    print("\nEncerrando...")
finally:
    manager.parar()
    print("Fim do teste.")
```

O `except` apenas torna Ctrl+C visível; o `finally` roda também após outra saída do `try`. `manager.parar()` retorna booleano, mas o teste não o usa: ele solicita parada e espera a sequência de [[threads-e-encerramento]]. Não há bloco `__main__`; esse efeito de importação é intencionalmente parte do comportamento.

## Insights para outros projetos

- Smoke tests manuais podem reutilizar o pipeline real.
- Coloque encerramento de hardware em `finally`.
- Documente efeitos de importação porque eles impactam testes e ferramentas.

## Resumo mental

É um painel de terminal mínimo: liga a aquisição, mostra um pulso por segundo e desliga ordenadamente com `Ctrl+C`.
#PROJETO_SENSOR_VIBRAÇÃO
