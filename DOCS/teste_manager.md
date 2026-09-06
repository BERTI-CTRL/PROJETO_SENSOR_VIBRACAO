# `sensor/teste_manager.py`

Este é um teste interativo de aquisição sem GUI. Ao importar **ou executar** o módulo, ele imprime a mensagem inicial e chama `manager.iniciar()` imediatamente; portanto, `python -m sensor.teste_manager` abre o caminho normal de aquisição por [[manager]] e [[coletor]]. Não o importe de uma biblioteca ou teste automatizado esperando ausência de efeitos colaterais.

Enquanto recebe dados, o laço consulta o [[buffers|buffer circular]] a cada segundo. Quando ele não está vazio, mostra o último `contador` e a quantidade de amostras retidas. A aquisição continua até o usuário pressionar `Ctrl+C`, que gera `KeyboardInterrupt`; o `finally` então chama `manager.parar()` para terminar as threads e fechar o CSV conforme [[threads-e-encerramento]].

Ele é diferente de [[testar_dados]]. `teste_manager.py` exige aquisição/serial e observa o pipeline vivo; `dados/testar_dados.py` abre um CSV já existente para verificar cabeçalho, continuidade, taxa e valores. Para visualizar gráficos durante a aplicação, consulte [[janela]].

```powershell
python -m sensor.teste_manager
```

Use `Ctrl+C` para encerrar normalmente. Não execute este módulo em verificações sem hardware.
