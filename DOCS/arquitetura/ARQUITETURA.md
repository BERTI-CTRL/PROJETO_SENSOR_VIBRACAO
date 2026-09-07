# Arquitetura do projeto

Este documento explica o caminho real de uma amostra, do MPU6050 até a janela e o gráfico Plotly.

## Visão do fluxo

```text
MPU6050
  ↓ I²C
arduino/mpu-6050/mpu-6050.ino
  ↓ serial: contador, tempo, ax, ay, az, gx, gy, gz
sensor/serial_reader.py
  ↓ tupla Python
sensor/coletor.py  (thread coletor-serial)
  ├─→ sensor/buffers.py → realtime/janela.py
  └─→ Queue → sensor/gravador_worker.py → sensor/gravador.py → dados/*.csv
                                                               ↓
                                                     grafico/plotar_csv.py
```

## 1. Arduino e protocolo serial

O firmware configura o MPU6050 em `±16 g` e `±2000 °/s`, lê os 14 bytes consecutivos do sensor e envia uma linha por amostra:

```text
contador,tempo_arduino_us,ax,ay,az,gx,gy,gz
```

O `contador` permite detectar perdas. `tempo_arduino_us`, vindo de `micros()`, é a referência usada para calcular Hz no Python. Veja [[arduino_mpu6050]] para registradores, escalas e cuidados de I²C.

## 2. Leitor serial

`sensor/serial_reader.py` abre a porta em `115200` baud, aguarda a reinicialização do Arduino e usa `readline()` para obter uma linha completa. Só aceita oito campos numéricos.

O leitor recebe de `coletor.py` uma função `deve_continuar`. Assim, ao parar a coleta, ele encerra mesmo se a serial não estiver recebendo linhas; no pior caso espera o timeout serial de `0,1 s`.

## 3. Coletor: ponto central da aquisição

`sensor/coletor.py` roda em uma thread criada pelo `SensorManager`. Para cada amostra válida, ele:

1. calcula Hz médio, instantâneo e suavizado pelo tempo do Arduino;
2. compara o contador atual com o anterior e conta saltos;
3. envia a amostra ao `BufferSensores`;
4. coloca uma cópia na fila de gravação sem esperar pelo disco.

No futuro, este é o ponto recomendado para aplicar uma calibração validada: depois da leitura serial e antes de buffer, janela e CSV. Hoje o projeto ainda mantém os valores recebidos sem correção adicional.

## 4. Buffer e janela em tempo real

`sensor/buffers.py` mantém até 10.000 amostras em memória, em ordem cronológica e protegido por `Lock`.

`realtime/janela.py` não lê a serial. Ela pede `snapshot(150)` ao buffer e redesenha os dois gráficos aproximadamente a cada `33 ms`:

```text
últimas 150 amostras
        ↓
eixo X relativo de 0 até n - 1
        ↓
curvas de aceleração e giro
```

O eixo X não é deslocado a cada frame. Esse detalhe reduz o custo de renderização e ajuda a preservar a taxa de aquisição. O botão **Auto Escala** pode reajustar somente o eixo Y; ele nunca move X.

As estatísticas são atualizadas separadamente a cada `500 ms`. Elas usam outra cópia das últimas 150 amostras e exibem média, desvio padrão e RMS.

### Janela não é histórico completo

A janela mostra somente cerca de `150 / 210 ≈ 0,7 s` recentes. Um pico que ocorreu antes pode ter desaparecido da janela, mas permanece no CSV e aparecerá no Plotly.

## 5. Gravação assíncrona do CSV

O `Coletor` não escreve em disco diretamente. Ele envia cada linha para uma `Queue(maxsize=50000)` e `GravadorWorker` grava lotes de 1.000 linhas no arquivo CSV.

Essa separação protege a serial contra pequenas pausas de disco. Se a fila encher, o coletor registra `amostras_nao_enfileiradas`: a janela pode continuar mostrando dados, mas o CSV poderá perder algumas linhas.

Ao parar, `SensorManager.parar()` faz três coisas em ordem: para o coletor, espera sua thread terminar, envia o sentinela `None` ao gravador e espera o flush do arquivo. Só então a janela abre o Plotly.

## 6. Plotly: análise posterior

`grafico/plotar_csv.py` lê o CSV completo e cria dois painéis no navegador:

- aceleração: `ax`, `ay`, `az`;
- giroscópio: `gx`, `gy`, `gz`.

Por isso, Plotly pode exibir eventos que não aparecem mais na janela. Ele não recebe dados da interface: ambos usam a mesma sessão apenas porque o CSV foi gravado pelo coletor.

## 7. Calibração por vibração conhecida

`calibração/calibrar_vibracao.py` é executado depois da captura, sobre um CSV. Para um eixo excitado em uma bancada com RMS conhecido, ele calcula:

```text
offset = média do eixo
ganho  = RMS conhecido / RMS medido após remover o offset
valor corrigido = ganho × (valor medido - offset)
```

O resultado é um JSON. O script não modifica o firmware, o coletor, a janela ou o CSV original. Antes de integrar os coeficientes, valide-os em outra captura. Veja [[calibrar_vibracao]].

## Executar cada parte

| Objetivo | Comando | O que acontece |
|---|---|---|
| Monitorar normalmente | `python -m realtime.main` | Abre a janela; clique em Iniciar. |
| Testar serial sem GUI | `python -m sensor.teste_manager` | Imprime contador e tamanho do buffer. |
| Debug visual mínimo | `python realtime\gráfico.py` | Inicia coleta e mostra apenas `ax`; use por pouco tempo. |
| Analisar CSV | `python grafico\plotar_csv.py` | Abre o CSV mais recente no navegador. |
| Calibrar uma vibração | `python calibração\calibrar_vibracao.py 0.50` | Compara o último CSV com referência de `0,50 g RMS` em `az`. |

## Limites importantes

- Não há correção de calibração aplicada automaticamente ainda.
- O firmware não verifica continuamente se o MPU6050 preservou as escalas configuradas. Se, após movimento, um eixo parado passa de aproximadamente `1 g` para `8 g`, investigue possível reset do MPU, alimentação e I²C.
- Taxa e filtro DLPF não são configurados explicitamente no firmware; não use o sistema para uma análise de frequência crítica sem primeiro definir e validar esses parâmetros.

## Referências

- [[arduino_mpu6050]] — firmware, registradores e escalas.
- [[serial_reader]], [[coletor]], [[buffers]], [[gravador]] e [[manager]] — pipeline Python.
- [[janela]] e [[grafico]] — interfaces de tempo real.
- [[plotar_csv]] — análise do CSV completo.
- [[calibrar_vibracao]] — calibração simples por referência RMS.
#PROJETO_SENSOR_VIBRAÇÃO
