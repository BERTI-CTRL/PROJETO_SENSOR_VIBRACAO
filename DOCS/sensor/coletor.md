# coletor.py

## Resumo

`Coletor` é o produtor central da sessão: consome [[serial_reader]], calcula frequência e perdas, atualiza [[buffers]] e tenta enfileirar a mesma amostra para [[gravador_worker]]. Não escreve no disco.

## Dependências, entrada e saída

Importa `BufferSensores`, `deque`, `Full` e `ler_dados`. Recebe porta, baud rate e fila opcional. Sua entrada é a tupla de nove valores do leitor. Suas saídas são o buffer, listas de nove valores na fila, atributos de métricas e logs.

```python
Coletor(porta="COM4", baudrate=230400, fila_gravacao=None)
```

O construtor cria `BufferSensores()`, contadores, três valores Hz, referências de tempo Arduino e `deque(maxlen=100)` para suavização.

## Métodos

### `configurar_fila_gravacao(fila_gravacao)`

Troca a fila de destino. [[manager]] a fornece no início de cada sessão.

### `_registrar_salto(contador)`

Conta somente avanço maior que um:

```python
if self.contador_anterior is not None and contador > self.contador_anterior + 1:
    perdidas = int(contador - self.contador_anterior - 1)
```

Incrementa `saltos_contador` por evento e `amostras_perdidas` pelo número estimado; por fim atualiza a referência.

> [!warning]
> Repetição, retrocesso, reinício e overflow do contador não satisfazem a condição e não são classificados como salto.

### `_enfileirar_gravacao(linha)`

Se não há fila, retorna. Caso exista, usa `put_nowait`; em `Full`, aumenta `amostras_nao_enfileiradas` e registra a primeira perda e cada mil seguintes.

> [!idea]
> Esta degradação é deliberada: preservar serial/UI tem prioridade sobre bloquear a aquisição para esperar o disco.

### `executar()`

Marca `rodando=True`, zera estado de sessão e itera:

```python
for tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz in ler_dados(
    porta=self.porta,
    baudrate=self.baudrate,
    deve_continuar=lambda: self.rodando,
):
```

Cada amostra incrementa `numero_amostras`, mede salto, atualiza Hz, chama `buffer.adicionar(...)` e enfileira a mesma sequência como lista. A primeira amostra só fixa os dois tempos de referência. Depois, se intervalos são positivos:

```python
self.hz_medio = (self.numero_amostras - 1) / dt_total
self.hz_inst = 1 / dt_inst
self.hz_inst_suavizado = sum(self.historico_hzs_inst) / len(self.historico_hzs_inst)
```

`dt_total` e `dt_inst` vêm de microssegundos Arduino convertidos para segundos; o timestamp do PC é armazenado, não usado nessas fórmulas.

> [!warning]
> Tempo Arduino igual, decrescente ou em rollover não recebe correção explícita; a frequência anterior pode continuar exposta até novo delta positivo.

### `parar()`

Somente imprime aviso e muda `rodando=False`. O leitor serial e [[manager]] realizam a interrupção física e joins.

## Fluxo e limitações

`[[serial_reader]] → executar → métricas + [[buffers]] → Queue → [[gravador_worker]] → [[gravador]]`. `amostras_perdidas` é lacuna serial; `amostras_nao_enfileiradas` é perda apenas de persistência, detalhada em [[tempo-frequencia-e-perdas]].

> [!warning]
> Nova sessão reinicia métricas, mas não chama `buffer.limpar()`. Como o coletor é reutilizado por [[manager]], valores anteriores podem seguir visíveis até sobrescritos.

## Código explicado, na ordem do arquivo

### Imports, classe e estado inicial

```python
from sensor.buffers import BufferSensores
from collections import deque
from queue import Full
from sensor.serial_reader import ler_dados
```

Os imports conectam armazenamento, janela de Hz, exceção de saturação e fonte serial. `class Coletor` não herda outra classe. O construtor recebe `porta="COM4"`, `baudrate=230400` e fila opcional, não retorna valor, e cria `self.buffer = BufferSensores()` mais estado de sessão: flag `rodando`, contadores, perdas, Hz, tempos e `deque(maxlen=100)`.

### Configuração de fila e salto de contador

```python
def configurar_fila_gravacao(self, fila_gravacao):
    self.fila_gravacao = fila_gravacao
```

Recebe uma Queue e apenas substitui o destino, permitindo que [[manager]] crie uma fila nova por sessão.

```python
if self.contador_anterior is not None and contador > self.contador_anterior + 1:
    perdidas = int(contador - self.contador_anterior - 1)
    self.saltos_contador += 1
    self.amostras_perdidas += perdidas
...
self.contador_anterior = contador
```

`_registrar_salto()` recebe contador e não retorna valor. O `if` evita calcular na primeira amostra e ignora sequência normal; quando há lacuna, loga diagnóstico. A última atribuição ocorre sempre para preparar a próxima comparação.

### Enfileiramento não bloqueante

```python
if self.fila_gravacao is None:
    return
try:
    self.fila_gravacao.put_nowait(linha)
except Full:
    self.amostras_nao_enfileiradas += 1
```

`_enfileirar_gravacao()` recebe uma lista de nove valores e não retorna valor. O retorno precoce permite usar coletor sem gravador. `put_nowait` não bloqueia a thread serial; o `except Full` preserva aquisição e limita logs com `if ... % 1000 == 1`.

### `executar()`: reinício e loop principal

No início, `executar()` define `rodando=True` e zera todos os contadores, referências e Hz; também chama `self.historico_hzs_inst.clear()`. Então consome o gerador:

```python
for tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz in ler_dados(
    porta=self.porta,
    baudrate=self.baudrate,
    deve_continuar=lambda: self.rodando,
):
    if not self.rodando:
        print("Parando")
        break
```

O `lambda` permite que [[serial_reader]] observe esta mesma flag. O `if` adicional cobre o caso de a parada ocorrer após o leitor já ter produzido uma tupla.

Na primeira amostra, o `if self.numero_amostras == 1` só atribui os tempos inicial/anterior. Nas demais, `dt_total` atualiza `hz_medio` se positivo; `dt_inst` atualiza Hz instantâneo, adiciona ao `deque` e calcula média suavizada se positivo. Ao final de cada iteração:

```python
self.buffer.adicionar(tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz)
self._enfileirar_gravacao([
    tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz,
])
```

Assim as duas saídas recebem exatamente a mesma ordem de dados.

### `parar()` e bloco direto

`parar()` não recebe argumentos e não retorna valor: imprime e muda `self.rodando=False`.

O bloco executável `if __name__ == "__main__":` (linhas 217–242) é alternativa manual a [[manager]]. Ele importa localmente `Queue` e `GravadorWorker`, faz `fila_gravacao = Queue(maxsize=50_000)`, cria `gravador = GravadorWorker(fila_gravacao)` e chama `gravador.start()` **antes** de configurar/iniciar `collector = Coletor(fila_gravacao=fila_gravacao)`. Assim o consumidor já existe quando a primeira linha puder ser produzida. O `try` chama `collector.executar()`; `except KeyboardInterrupt` transforma Ctrl+C em `collector.parar()`; o `finally` faz `fila_gravacao.put(None)` e `gravador.join()`. A sentinela vem depois do produtor e o join espera o flush/fechamento do CSV.

## Insights para outros projetos

- Mantenha produtor de hardware livre de I/O de disco.
- Separe “não chegou pela serial” de “chegou mas não foi salvo”.
- Use o relógio do dispositivo para medir uma taxa do dispositivo.

## Resumo mental

Uma amostra entra da serial, vira telemetria e visualização, e tenta virar CSV sem permitir que o disco lento freie o sensor.
#PROJETO_SENSOR_VIBRAÇÃO
