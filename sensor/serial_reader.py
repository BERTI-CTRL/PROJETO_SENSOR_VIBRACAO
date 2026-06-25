#serial_reader.py ->conversar com o Arduino
import serial
import time

import random

def ler_dados(porta, baudrate=115200, timeout=1):

    with serial.Serial(porta, baudrate, timeout=timeout) as arduino:
    

        time.sleep(2)
        arduino.reset_input_buffer() # reduzir o lixo

        while True:
            timestamp = time.perf_counter()
            dados_linha = arduino.readline().decode(
                'utf-8',
                errors='ignore'
            ).strip()

            #print(repr(dados_linha))

            try:
                timestamp,contador,ax,ay,az,gx,gy,gz = map(float,dados_linha.split(","))
                yield (
                timestamp,
                contador,
                ax,
                ay,
                az,
                gx,
                gy,
                gz
            )

            except ValueError:
                continue



def ler_dados_fake():

    contador = 0

    while True:

        contador += 1

        ax = random.uniform(-2, 2)
        ay = random.uniform(-2, 2)
        az = random.uniform(-2, 2)

        gx = random.uniform(-250, 250)
        gy = random.uniform(-250, 250)
        gz = random.uniform(-250, 250)

        yield contador, ax, ay, az, gx, gy, gz

        time.sleep(0.01)  # simula ~100 Hz


from collections import deque
if __name__ == "__main__":

    n = 0
    t0 = time.perf_counter()
    t_anterior = time.perf_counter()


    
    hzs = deque(maxlen=100)
    for contador,ax,ay,az,gx,gy,gz in ler_dados(porta="COM5",baudrate=115200):

        #print(f"Aceleração em x:{ax} | Aceleração em y:{ay} | Aceleração em z:{az}")
        #
        #print(f"Giro em x: {gx} | Giro em y: {gy} | Giro em z: {gz}")
        #time.sleep(3)


        #media acumulada
        n += 1

        if n % 100 == 0:

            dt = time.perf_counter() - t0

            hz = n / dt

            print(f"\rTaxa de recebimento: {hz:.2f} Hz\n",end="")


        #Media instantânea
        agora = time.perf_counter()

        dt = agora - t_anterior
        t_anterior = agora

        hz_inst = 1 / dt if dt > 0 else 0

        hzs.append(hz_inst)

        print(f"\rHz instantâneo: {hz_inst:6.2f}", end="")

        if contador == 1000:
            print(hzs)#media de 250 hzs
            break

    #fake
    '''for contador, ax, ay, az, gx, gy, gz in ler_dados_fake():
        print(ax, ay, az)'''