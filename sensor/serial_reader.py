# Registra imediatamente no console que o módulo de leitura serial foi importado.
print("INICIOU O SERIAL_READER")

# Fornece relógios de alta resolução e pausas canceláveis durante a inicialização.
import time
# Abre a porta e lê os bytes enviados pelo Arduino.
import serial
# Gera valores aleatórios no gerador de teste sem hardware.
import random


def ler_dados(porta, baudrate=230400, timeout=0.1, deve_continuar=None):
    """Lê linhas da serial enquanto a aquisição estiver ativa."""

    # Encapsula a regra de parada, aceitando aquisição contínua quando não há callback.
    def continuar():
        # Consulta o callback apenas quando ele foi informado pelo chamador.
        return deve_continuar is None or deve_continuar()

    # Abre a serial e garante seu fechamento ao sair do gerador, inclusive por erro ou parada.
    with serial.Serial(porta, baudrate, timeout=timeout) as arduino:
        #print("Abrindo serial...")

        # Abertura da serial pode reiniciar o Arduino. Espera sem impedir
        # que o botão Parar encerre a thread durante esse intervalo.
        # Calcula o instante-limite com um relógio que não retrocede se o relógio civil mudar.
        limite_espera = time.monotonic() + 2
        # Aguarda o possível reset do Arduino, mas reavalia a solicitação de parada a cada ciclo.
        while time.monotonic() < limite_espera:
            # Encerra antes de iniciar leituras se a interface solicitou parada durante a espera.
            if not continuar():
                return
            # Limita a frequência de consulta do callback durante os dois segundos de estabilização.
            time.sleep(0.05)

        #print("Resetando buffer")
        # Descarta bytes acumulados durante o reset para iniciar na próxima linha disponível.
        arduino.reset_input_buffer() # reduzir o lixo


        #print("Entrando no while")
        # Conta linhas descartadas para diagnóstico local, sem alterar o fluxo de aquisição.
        linhas_invalidas = 0
        # Processa uma linha por vez enquanto a aquisição estiver autorizada a continuar.
        while continuar():
            # O relógio do PC descreve a recepção; o Coletor usa micros() do Arduino para calcular Hz.
            # Registra o instante de recepção no PC; ele integra a tupla, mas não mede a frequência do sensor.
            timestamp = time.perf_counter()


            #print("Esperando linha...")
            # Aguarda até uma linha ou até o timeout configurado, decodifica bytes tolerando corrupção e remove espaços.
            dados_linha = arduino.readline().decode(
                'utf-8',
                errors='ignore'
            ).strip()


            # Ignora timeout, linha vazia ou apenas terminadores, mantendo o gerador aberto.
            if not dados_linha:
                continue
            #print("Recebi bytes:", repr(dados_linha)) #slk que linha maravilhosa

            
            # Separa a linha CSV produzida pelo firmware nos campos individuais.
            campos = dados_linha.split(",")
            # Aceita somente o protocolo com seus oito campos antes de tentar conversão numérica.
            if len(campos) != 8:
                # Registra a rejeição para inspeção futura sem expor uma amostra incompleta ao coletor.
                linhas_invalidas += 1 
                
                continue
    
            
            # Captura valores não numéricos sem interromper a aquisição serial.
            try:
                # Converte e desempacota contador, micros() e os seis eixos exatamente na ordem do firmware.
                contador,tempo_arduino_us,ax,ay,az,gx,gy,gz = map(float,campos)
                # Emite um marco de progresso a cada mil amostras recebidas.
                if contador % 1000 ==0:
                    print(f"[Serial] : {contador}")
                    
                # Mantém desativado o antigo bloco de diagnóstico detalhado, sem executá-lo.
                """print(
                    contador,
                    tempo_arduino_us,
                    ax,
                    ay,
                    az,
                    gx,
                    gy,
                    gz
                )"""

                # Entrega ao Coletor nove valores: tempo do Arduino, tempo do PC, contador e seis eixos.
                yield (
                tempo_arduino_us,
                timestamp,
                contador,
                ax,
                ay,
                az,
                gx,
                gy,
                gz
            )
            

            # Trata a falha de conversão de qualquer um dos oito campos da linha.
            except ValueError:
                # Conta a linha inválida antes de prosseguir para a próxima leitura.
                linhas_invalidas += 1
                # Expõe o conteúdo rejeitado para diagnóstico sem encerrar o gerador.
                print(f"[Serial] Linha inválida: {repr(dados_linha)}")
                continue
            


def ler_dados_fake():

    # Inicia a sequência sintética no mesmo ponto que o contador do firmware recém-ligado.
    contador = 0

    # Produz continuamente dados de teste até que o consumidor pare de iterar o gerador.
    while True:

        # Mede o instante no PC para acompanhar a forma da saída de teste já existente.
        timestamp = time.perf_counter()
        # Avança o contador sintético uma vez por amostra gerada.
        contador += 1

        # Sorteia aceleração no eixo X dentro da faixa de teste estabelecida.
        ax = random.uniform(-2, 2)
        # Sorteia aceleração no eixo Y dentro da faixa de teste estabelecida.
        ay = random.uniform(-2, 2)
        # Sorteia aceleração no eixo Z dentro da faixa de teste estabelecida.
        az = random.uniform(-2, 2)

        # Sorteia velocidade angular no eixo X dentro da faixa de teste estabelecida.
        gx = random.uniform(-250, 250)
        # Sorteia velocidade angular no eixo Y dentro da faixa de teste estabelecida.
        gy = random.uniform(-250, 250)
        # Sorteia velocidade angular no eixo Z dentro da faixa de teste estabelecida.
        gz = random.uniform(-250, 250)

        # Emite a tupla sintética histórica, cuja forma tem oito valores e não inclui tempo do Arduino.
        yield timestamp,contador, ax, ay, az, gx, gy, gz

        # Espaça as amostras artificiais para aproximar uma taxa de 100 Hz.
        time.sleep(0.01)  # simula ~100 Hz


if __name__ == "__main__":
    # Informa que o módulo foi iniciado diretamente para depuração manual.
    print("Entrou no main")

    


    

    # Lê continuamente a COM4 com 115200 para o modo manual; este valor diverge do padrão da função e é preservado.
    for tempo_arduino_us,timestamp,contador,ax,ay,az,gx,gy,gz in ler_dados(porta="COM4",baudrate=115200):

        # Mostra o contador recebido para acompanhar a continuidade das amostras.
        print("contador:",contador)
        # Mostra os três eixos de aceleração para inspeção visual rápida.
        print(f"Aceleração em x:{ax} | Aceleração em y:{ay} | Aceleração em z:{az}")
        
        #print(f"Giro em x: {gx} | Giro em y: {gy} | Giro em z: {gz}")
        #time.sleep(3)

        
    #fake (debug)
    '''for contador, ax, ay, az, gx, gy, gz in ler_dados_fake():
        print(ax, ay, az)'''
