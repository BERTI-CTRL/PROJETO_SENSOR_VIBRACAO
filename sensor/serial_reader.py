#serial_reader.py ->conversar com o Arduino

import time
import serial
import random


def ler_dados(porta, baudrate=115200, timeout=1):

    with serial.Serial(porta, baudrate, timeout=timeout) as arduino:
        #print("Abrindo serial...")
    
        time.sleep(2)


        #print("Resetando buffer")
        arduino.reset_input_buffer() # reduzir o lixo


        #print("Entrando no while")
        while True:
            #relogio do pc. É importante ressaltar que usar o tempo de pc para medir Hz - como é o caso- pode gerar erros
            #um dos erros que tive foi taxas de hz intantaneo absurdas,como >1000hz variando muito,haja vista que a leitura em buffers pode fazer o python atropelar dados
            # . O arduino oferece um método interessante
            # e mais confiável para ter um dt confiável e robusto,a saber, micros(). A partir dele, se torna mais confiável calcular o hz,
            #ja que temos o tempo do arduino n do pc,ainda que o do pc ofereça informações relevantes, em questões de recebimento
            timestamp = time.perf_counter()
            dados_linha = arduino.readline().decode(
                'utf-8',
                errors='ignore'
            ).strip()

            print("Recebi bytes:", repr(dados_linha)) #slk que linha maravilhosa

    
            '''   
            try:
                contador,tempo_arduino_us,ax,ay,az,gx,gy,gz = map(float,dados_linha.split(","))

                print(
                    contador,
                    tempo_arduino_us,
                    ax,
                    ay,
                    az,
                    gx,
                    gy,
                    gz
                )

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

            except Exception as e:
                print(e)
            '''


def ler_dados_fake():

    contador = 0

    while True:

        timestamp = time.perf_counter()
        contador += 1

        ax = random.uniform(-2, 2)
        ay = random.uniform(-2, 2)
        az = random.uniform(-2, 2)

        gx = random.uniform(-250, 250)
        gy = random.uniform(-250, 250)
        gz = random.uniform(-250, 250)

        yield timestamp,contador, ax, ay, az, gx, gy, gz

        time.sleep(0.01)  # simula ~100 Hz


if __name__ == "__main__":
    from collections import deque

    n = 0
    t0 = time.perf_counter()
    t_anterior = time.perf_counter()


    
    hzs = deque(maxlen=100)
    for tempo_arduino_us,timestamp,contador,ax,ay,az,gx,gy,gz in ler_dados(porta="COM4",baudrate=115200):

        print(f"Aceleração em x:{ax} | Aceleração em y:{ay} | Aceleração em z:{az}")
        #
        print(f"Giro em x: {gx} | Giro em y: {gy} | Giro em z: {gz}")
        #time.sleep(3)


        #media acumulada
        n += 1

        if n % 100 == 0:

            dt = time.perf_counter() - t0

            hz = n / dt

            #print(f"\rTaxa de recebimento: {hz:.2f} Hz\n",end="")


        #Media instantânea
        agora = time.perf_counter()

        dt = agora - t_anterior
        t_anterior = agora

        hz_inst = 1 / dt if dt > 0 else 0

        hzs.append(hz_inst)

        #print(f"\rHz instantâneo: {hz_inst:6.2f}", end="")

        '''if contador == 1000:
            print(hzs)#media de 250 hzs
            break'''

    #fake
    '''for contador, ax, ay, az, gx, gy, gz in ler_dados_fake():
        print(ax, ay, az)'''