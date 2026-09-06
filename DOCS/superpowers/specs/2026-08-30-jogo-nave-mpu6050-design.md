# Jogo de nave controlado pelo MPU6050 — desenho

## Objetivo

Criar um jogo independente em `game/` no qual o jogador controla uma nave espacial desviando de meteoros ao inclinar o conjunto com MPU6050. O jogo precisa continuar utilizável pelo teclado quando não houver sensor, sem alterar o coletor, o firmware Arduino ou a interface de análise existentes.

## Experiência do jogador

Ao iniciar, o jogo abre numa tela curta de preparação. O jogador posiciona o conjunto na posição de repouso e pressiona `C`; durante cerca de 1,5 s, o programa reúne amostras e calcula a posição neutra. A tela informa se a conexão serial está ativa. Depois da calibração, a nave se move horizontalmente ao inclinar o sensor, enquanto meteoros caem e a pontuação cresce com o tempo e com os desvios bem-sucedidos.

O conjunto fotografado e os CSVs disponíveis indicam repouso com `ax` próximo de `+1 g` e `ay` próximo de `0 g`. Por isso, o controle padrão será `ay - ay_neutro`. A tecla `I` inverte o sentido imediatamente se a montagem física resultar em esquerda/direita invertidas. Uma zona morta e uma suavização curta evitam que ruído parado mova a nave.

As setas esquerda/direita serão uma alternativa deliberada para demonstrar o jogo sem hardware e para permitir uso quando a porta serial estiver indisponível.

## Arquitetura

```text
MPU6050 / Arduino --CSV serial--> SensorReader (thread)
                                         |
                                  última amostra válida
                                         |
Pygame (60 FPS) --> TiltController --> posição da nave --> colisões / placar / renderização
```

`SensorReader` é responsável apenas por abrir a serial, descartar linhas inválidas e publicar a amostra válida mais recente de forma segura entre threads. Ele entende o protocolo atual de oito campos: `contador,tempo_arduino_us,ax,ay,az,gx,gy,gz`.

`TiltController` contém a calibração, zona morta, inversão e filtro de movimento. Ele não depende de Pygame nem da serial, permitindo testes unitários diretos. O loop Pygame desenha a tela, processa eventos, consulta o controlador e atualiza jogo e interface.

## Componentes e arquivos

- `game/main.py`: ponto de entrada, loop Pygame, telas de preparação/jogo/fim, desenho e comandos.
- `game/sensor_input.py`: leitura serial assíncrona, validação CSV e exposição do estado da conexão.
- `game/controller.py`: calibração e conversão de aceleração em velocidade horizontal.
- `game/entities.py`: nave, meteoro, colisão e atualização de entidades.
- `game/config.py`: tamanho da janela, porta, baud rate e parâmetros de jogo/controle.
- `game/README.md`: instalação, execução, configuração da porta e controles.
- `game/tests/`: testes das regras puras de controle e colisão.

O visual será criado com formas e efeitos do Pygame: fundo estrelado, nave geométrica com propulsão, meteoros coloridos, partículas e HUD. Assim não há arquivos de imagem externos ou licença de arte a administrar.

## Falhas e comportamento seguro

Se a serial não abrir — porta errada, monitor serial ocupando a porta, Arduino ainda inicializando ou sensor desconectado — o jogo não termina. O HUD mostra o motivo e ativa o teclado. Linhas de inicialização ou depuração que não tenham os oito campos numéricos são ignoradas. Se os dados deixarem de chegar, a entrada do sensor deixa de mover a nave até que haja uma amostra atual.

O leitor serial roda separado do loop de 60 FPS e guarda somente a última amostra; portanto, renderização e obstáculos não acumulam atrasos na aquisição. O jogo não grava CSV e não compete com o pipeline de coleta existente: para jogar, o usuário fecha qualquer aplicação que já esteja usando a mesma porta.

## Verificação

Os testes automatizados cobrirão:

- parse e rejeição de linhas seriais;
- cálculo de neutro, zona morta, suavização e inversão;
- limitação da nave nas bordas;
- colisões retângulo-círculo entre nave e meteoro.

A verificação manual confirmará que o jogo abre sem sensor, aceita setas, mostra erro de porta sem travar, calibra com dados simulados e responde ao MPU6050 conectado na montagem atual.
