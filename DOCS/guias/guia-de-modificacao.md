# Guia de modificação segura

Este roteiro identifica acoplamentos do pipeline `MPU6050 → firmware → [[protocolo-serial]] → [[serial_reader]] → [[coletor]] → buffer/fila → janela e [[esquema-csv]] → análise`. Faça uma alteração por vez, registre a configuração do ensaio e valide uma nova captura; não assuma que um coeficiente de calibração continua válido após mudar a medição.

## Porta e baud rate

Altere a porta em `sensor/coletor.py` (`Coletor(porta=...)`) e confira qualquer execução manual em `sensor/serial_reader.py`. Para baud rate, mantenha coerentes `arduino/mpu-6050/mpu-6050.ino` (`Serial.begin(...)`), o padrão de `Coletor`, o padrão de `ler_dados` e o bloco manual de `serial_reader.py`. Hoje há uma divergência documentada entre valores; não a trate como configuração implícita.

Verifique a porta correta no sistema, abra a interface ou [[teste_manager]], confirme que chegam oito campos por linha e capture um CSV. Em seguida rode [[testar_dados]] para observar Hz e saltos. Consulte [[protocolo-serial]] e [[arduino_mpu6050]] antes de alterar a comunicação.

## Protocolo serial

Se adicionar, remover, renomear ou reordenar campos do firmware, atualize juntos `arduino/mpu-6050/mpu-6050.ino`, `sensor/serial_reader.py`, `sensor/coletor.py`, `sensor/gravador.py`, `dados/testar_dados.py`, `grafico/plotar_csv.py` e os consumidores de tuplas/buffer em `realtime/`. Atualize também [[protocolo-serial]] e [[esquema-csv]].

Verifique a quantidade de campos por linha, tipos numéricos, ordem da tupla entregue pelo leitor, cabeçalho gravado e execução de [[testar_dados]] em um CSV novo. Uma alteração parcial pode não gerar erro imediato e, ainda assim, atribuir um eixo à coluna errada.

## Escalas do acelerômetro e giroscópio

Altere em conjunto os registradores e os divisores no firmware `arduino/mpu-6050/mpu-6050.ino`. As faixas de `dados/testar_dados.py` precisam corresponder às novas escalas; revise [[arduino_mpu6050]], [[testar_dados]], [[esquema-csv]] e o guia em `calibração/guia_calibracao_mpu6050.md`.

Com o sensor parado, confirme unidades e gravidade esperada. Depois aplique movimento conhecido sem saturação, rode [[testar_dados]] e repita a validação descrita em [[calibrar_vibracao]] antes de reutilizar ganho ou offset antigos.

## Taxa de amostragem e filtro

A taxa atual resulta do laço do firmware e da comunicação; não há, no código atual, uma taxa de amostragem explicitamente configurada. Alterações de atraso, leituras I2C, serial ou registradores de filtro no `mpu-6050.ino` afetam a resposta. Atualize o firmware, [[arduino_mpu6050]], [[tempo-frequencia-e-perdas]] e a documentação de calibração quando aplicável.

Capture dados longos, compare `hz_medio` e a dispersão de Hz em [[testar_dados]], procure saltos do contador e faça ensaios com frequências conhecidas. Refaça a calibração dinâmica: filtro e taxa podem alterar RMS e resposta em frequência.

## Tamanho de buffer e fila de gravação

O buffer circular é definido em `sensor/buffers.py`; os limites de fila usados pela sessão estão em `sensor/manager.py` e no bloco manual de `sensor/coletor.py`. Os números exibidos em `realtime/janela.py` e a documentação [[buffers]], [[manager]], [[gravador]] e [[janela]] acompanham esses limites.

Verifique retenção correta após encher o buffer, memória suficiente, encerramento com `Ctrl+C` e fechamento do CSV. Para a fila, faça uma captura prolongada e confirme que `amostras_nao_enfileiradas` não cresce; uma fila maior não recupera perdas que ocorreram antes da recepção serial.

## Taxa da interface e estatísticas

Altere `realtime/janela.py` se mudar os intervalos dos timers, `PONTOS_GRAFICO` ou a estratégia de `snapshot()`. Arquivos acoplados: [[janela]], [[grafico]], [[statistics]] e [[buffers]]. O gráfico e as estatísticas têm ritmos e recortes próprios; não conclua que aumentar FPS aumenta a taxa física do sensor.

Verifique responsividade, uso de CPU, ausência de travamento e coerência entre os rótulos e os dados recentes. Faça também uma captura e compare a taxa do coletor com [[testar_dados]], que usa o tempo do Arduino e não a atualização visual.

## CSV e persistência

Para mudar nome, diretório, cabeçalho, delimitador, codificação ou política de gravação, revise `sensor/gravador.py`, `sensor/gravador_worker.py`, `sensor/coletor.py`, `dados/testar_dados.py`, `grafico/plotar_csv.py` e `calibração/calibrar_vibracao.py`. Atualize [[esquema-csv]], [[gravador]], [[testar_dados]], [[plotar_csv]] e [[calibrar_vibracao]].

Faça uma sessão curta, aguarde o encerramento normal e abra o arquivo recém-criado. Confirme cabeçalho e número de colunas, execute [[testar_dados]], gere o gráfico somente de modo manual e confirme que a calibração lê as colunas requeridas. Nunca sobregrave capturas de referência sem cópia.

## Calibração

O cálculo atual está em `calibração/calibrar_vibracao.py` e grava `calibracao_vibracao_<eixo>.json`; o coletor não aplica esse JSON automaticamente. Mudanças no modelo, nome/estrutura do JSON ou ponto de aplicação exigem revisar o script, [[calibrar_vibracao]], `calibração/guia_calibracao_mpu6050.md`, [[coletor]] e todos os consumidores que receberiam valores corrigidos.

Valide argumentos inválidos (referência não positiva, descarte negativo, CSV sem colunas), use uma referência RMS conhecida e separe captura de calibração de captura de validação. Preserve dados brutos e registre escala, filtro, taxa, orientação e temperatura. Consulte também a documentação da InvenSense, caso ela seja adicionada ao vault futuramente.
#PROJETO_SENSOR_VIBRAÇÃO
