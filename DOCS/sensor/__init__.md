# __init__.py

## Resumo

`sensor/__init__.py` identifica `sensor` como pacote Python e deliberadamente não inicializa nada, não importa submódulos e não reexporta símbolos.

## Papel e código

O arquivo contém somente os comentários:

```python
# O pacote não executa inicialização própria; os módulos são importados explicitamente pelos consumidores.
# A ausência de reexportações preserva os pontos de entrada atuais, como sensor.manager.manager.
```

Não há imports, constantes, classes, funções, entrada, saída ou I/O. Os consumidores escolhem pontos explícitos, como `from sensor.manager import manager` e `from sensor.buffers import BufferSensores`.

## Decisão arquitetural

Manter a raiz passiva permite `import sensor` sem abrir serial, criar thread ou gerar CSV. A ativação fica em módulos concretos como [[manager]] e [[teste_manager]].

> [!idea]
> Em pacotes com hardware, threads ou I/O, um `__init__.py` passivo separa descoberta do pacote de ativação do sistema.

## Relações

É a raiz nominal de [[buffers]], [[serial_reader]], [[coletor]], [[gravador]], [[gravador_worker]] e [[manager]], mas não os carrega automaticamente.

## Código explicado, na ordem do arquivo

O arquivo possui somente os dois comentários abaixo e nenhuma instrução executável:

```python
# O pacote não executa inicialização própria; os módulos são importados explicitamente pelos consumidores.
# A ausência de reexportações preserva os pontos de entrada atuais, como sensor.manager.manager.
```

Assim não há imports, estado de módulo, constantes, classe, construtor, função, condição, loop, `try`/`except` ou bloco `__main__` a detalhar. Ao importar `sensor`, Python carrega este arquivo passivo e não importa automaticamente [[manager]] nem [[serial_reader]]. O resultado é a disponibilidade do namespace de pacote; a ativação depende de importar e chamar o ponto de entrada desejado.

## Insights para outros projetos

- Evite reexportação que crie acoplamento ou efeitos de importação.
- Mantenha o pacote importável sem exigir hardware ou configuração externa.

## Resumo mental

É a placa na porta do pacote: identifica `sensor`, mas não liga nada por conta própria.
#PROJETO_SENSOR_VIBRAÇÃO
