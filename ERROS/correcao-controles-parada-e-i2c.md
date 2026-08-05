# Correções de controles, parada e leitura I²C

**Data:** 04/08/2026
**Status:** corrigido

## Problemas encontrados

| Problema | Sintoma | Causa | Correção simples aplicada |
|---|---|---|---|
| Botão de parada | O código tratava `botao_parar.clicked` como condição. | `clicked` é o sinal do Qt, não informa se houve clique; como objeto, ele é avaliado como verdadeiro. | O sinal permanece conectado a `parar()`, que chama diretamente `manager.parar()`. |
| Parada sem dados serial | Ao parar durante a abertura da porta ou sem linhas válidas, a janela podia esperar até a próxima leitura. | O leitor usava espera fixa de 2 s e um `while True` sem observar o estado do coletor. | `ler_dados()` recebe `deve_continuar`; a espera inicial é cancelável e o laço encerra depois de, no máximo, um `timeout` serial de 0,1 s. |
| Plotly ao parar | Um clique em **Parar** sem uma coleta válida podia reabrir o CSV antigo. | O programa procurava simplesmente o CSV mais recente. | A janela só abre o Plotly se a sessão efetivamente encerrada recebeu ao menos uma amostra. |
| Auto-scroll | Reposicionar os dois eixos X em todo frame reduzia o tempo disponível para a leitura serial. | Cada `setXRange()` força novo trabalho de visualização, além do redesenho das seis curvas. | O auto-scroll foi removido; o botão voltou a ser **Auto Escala** e o eixo X relativo é reutilizado. |
| Uso de CPU na interface | Mesmo pedindo 150 pontos, o buffer cheio podia copiar 10.000 amostras a cada atualização. | `snapshot()` montava toda a sequência cronológica antes de recortar a janela. | O recorte cronológico é calculado primeiro e só os pontos solicitados são copiados. |
| I²C incompleto | Uma falha parcial poderia resultar no envio de uma nova linha com valores anteriores. | O firmware lia as variáveis sem confirmar os 14 bytes solicitados. | Se `Wire.available() < 14`, o ciclo termina sem incrementar o contador nem enviar a amostra. |

## Como verificar

1. Inicie e pare logo em seguida: a janela deve retornar sem travar e sem abrir um CSV antigo se nenhuma amostra chegou.
2. Inicie uma coleta normal e pare: o CSV da sessão deve ser fechado antes de o Plotly abrir.
3. Clique em **Auto Escala**: os dois gráficos devem ajustar continuamente apenas suas faixas Y às curvas visíveis. O eixo X deve continuar fixo em `0–149`.
4. Deixe o buffer passar de 10.000 amostras: a interface deve continuar desenhando a janela curta mais recente.
5. Durante um teste físico, acompanhe saltos no contador. A verificação I²C evita registrar valores antigos, mas não substitui a inspeção do cabo, alimentação e taxa efetiva.

## Decisão propositalmente não automatizada

O firmware ainda não fixa `SMPLRT_DIV` nem `CONFIG`/DLPF. Isso não foi alterado porque escolher uma taxa ou filtro sem conhecer a maior frequência de vibração de interesse pode atenuar o sinal que se deseja medir. Antes de calibração dinâmica ou análise por FFT, defina esses parâmetros para o experimento e documente a configuração usada.

Ver também: [[arduino_mpu6050]], [[serial_reader]], [[buffers]] e [[janela]].
