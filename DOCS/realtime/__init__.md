# __init__.py

`realtime/__init__.py` marca `realtime/` como pacote Python da interface e é intencionalmente passivo. O arquivo contém somente comentários: não declara funções, classes, constantes ou objetos públicos.

## Resumo e papel

Ele permite imports como:

```python
from realtime.janela import Janela
```

sem iniciar interface, timer, thread, serial ou gravação. O comentário-fonte estabelece [[main]] como ponto de entrada explícito.

## Entrada, saída e dependências

Não recebe entrada, não gera saída e não importa módulos. Importar `realtime` apenas disponibiliza o pacote ao interpretador:

```text
import realtime
    ↓
nenhum QApplication / widget / timer / thread / serial criado
```

## Decisão arquitetural

Separar descoberta do pacote do ciclo de vida da aplicação deixa cada camada previsível: [[main]] cria `QApplication`, [[janela]] cria widgets/timers e [[manager]] controla aquisição. Isso permite importar componentes sem reservar a porta serial ou abrir uma janela.

> [!note] Contraste com o script de diagnóstico
> [[grafico]] cria aplicação e entra no event loop no nível do módulo. Este `__init__.py` faz o oposto: a ausência de código executável é seu contrato seguro de importação.

## Código explicado, na ordem do arquivo

O arquivo possui exatamente dois comentários consecutivos:

```python
# Marca ``realtime`` como o pacote da interface. A inicializacao permanece
# vazia para que importar o pacote nao crie QApplication, widgets ou timers;
# o ponto de entrada explicito e [[main]].
```

O primeiro comentário explica a função estrutural de `__init__.py`: sinalizar o pacote. O segundo estabelece a decisão de ciclo de vida: não há importação, constante, função, classe, `__main__` ou efeito de nível de módulo. Portanto, não há parâmetros recebidos, retorno, timer, loop ou slot para detalhar. A ausência desse código é precisamente o comportamento utilizado no projeto. O bloco é transcrito sem mudanças porque é comentário-fonte exato.

## Insights para outros projetos

- Use `__init__.py` para estabelecer o limite de pacote, não para iniciar recursos caros ou exclusivos.
- Centralize a entrada da aplicação em um módulo executável protegido por `if __name__ == "__main__"`.
- Imports sem efeitos colaterais tornam testes e reutilização mais previsíveis.

## Resumo mental

`realtime/__init__.py` organiza o pacote. Importar `realtime` não inicia captura; para abrir a interface, use [[main]].
#PROJETO_SENSOR_VIBRAÇÃO
