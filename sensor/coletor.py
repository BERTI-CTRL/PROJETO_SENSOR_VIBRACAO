#coletor.py ->Só processa uma amostra.
from sensor.buffers import BufferSensores
import time
from collections import deque

from sensor.serial_reader import ler_dados
from sensor.gravador import GravadorCSV


class Coletor():
    def __init__(self,porta="COM4",baudrate = 115200):
        self.rodando = False

        self.porta = porta 
        self.baudrate = baudrate
        self.buffer = BufferSensores()

        self.gravador = GravadorCSV(
            arquivo="dados_vibracao.csv",
            tamanho_buffer=1000
        )
        self.hz_medio = 0
        self.hz_inst = 0
        self.hz_amostras = 0
        self.t0 = 0
        self.t_anterior = 0
        
        self.hzs = deque(maxlen=100)
        
    
    def executar(self):
        self.rodando = True
        self.hz = 0
        self.amostras = 0
        self.hz_medio = 0
        self.hz_inst = 0
        self.t0 = time.perf_counter()
        self.t_anterior = self.t0
        self.hzs.clear()




        print("Coletor iniciado")
        
        try:

                for timestamp,contador, ax, ay, az, gx, gy, gz in ler_dados(
                    porta=self.porta,
                   baudrate=self.baudrate
                ):
                    self.amostras += 1

                    #####################################
                    # Estatísticas da aquisição
                    #####################################


                    #####################################
                    #Hertz médio
                    #####################################
                    dt = time.perf_counter() - self.t0
                    self.hz_medio = self.amostras/dt

                    #####################################
                    #Hertz instantâneo
                    #####################################
                    agora = time.perf_counter()
                    dt_inst = agora - self.t_anterior

                    self.t_anterior = agora

                    if dt_inst>0:

                        hz = 1/dt_inst

                        self.hzs.append(hz)
                        self.hz_inst = sum(self.hzs) / len(self.hzs)




                    #print("Recebi uma amostra")

                    if not self.rodando:#Pra controle
                        print("Parando")
                        break




                    self.buffer.adicionar(timestamp,contador, ax, ay, az, gx, gy, gz)

                    


                    self.gravador.salvar([
                        timestamp,
                        contador,
                        ax,
                        ay,
                        az,
                        gx,
                        gy,
                        gz
                    ])

        finally:

            self.gravador.fechar()

        
    def parar(self):
        print("Aquisição encerrada.")
        self.rodando=False

    


if __name__ == "__main__":

    collector = Coletor()

    collector.executar()