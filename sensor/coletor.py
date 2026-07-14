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
        self.numero_amostras = 0

        self.hz_medio = 0 #  valor do hz medio
        self.hz_inst = 0 # valor do hz instantaneo
        self.hz_inst_suavizado = 0 # valor do hz instantaneo suavizado

        self.tempo_arduino_inicial_us = 0
        self.tempo_arduino_anterior_us = 0

        self.historico_hzs_inst = deque(maxlen=100) # fila usada para calcular o valor hz instantaneo suavizado - > GUARDA OS ÚLTIMOS 100 HZ 
    
    def executar(self):

        self.rodando = True

        self.numero_amostras = 0
        self.tempo_arduino_incial_us = 0
        self.tempo_arduino_anterior_us = 0

        self.hz_medio = 0
        self.hz_inst = 0
        self.hz_inst_suavizado = 0



        self.historico_hzs_inst.clear()

        print("Coletor iniciado")



        
        try:

                for tempo_arduino_us,timestamp,contador, ax, ay, az, gx, gy, gz in ler_dados(
                    porta=self.porta,
                   baudrate=self.baudrate
                ):
                    self.numero_amostras += 1
                    
                    if self.numero_amostras == 1:
                        self.tempo_arduino_inicial_us = tempo_arduino_us
                        self.tempo_arduino_anterior_us = tempo_arduino_us

                        continue # esse continue ignora a primeira amostra,já que não há instante anterior

                    

                    #####################################
                    # Estatísticas da aquisição
                    #####################################

                    dt_total = (tempo_arduino_us - self.tempo_arduino_inicial_us )/1_000_000 


                    #####################################
                    #Hertz médio
                    #####################################
                    

                    if dt_total>0:

                        self.hz_medio = self.numero_amostras/dt_total



                    ###################################
                    #Hz inst
                    ###################################
                    dt_inst = (tempo_arduino_us - self.tempo_arduino_anterior_us)/1_000_000
                    

                    #####################################
                    #Hertz instantâneo Suavizado -> menos suscetível a grandes variações. Isso é importante pois a taxa de hz sofre microvariações em decorrência dos tipos dedados envolvidos
                    #e à própria variação da precisão computacional. A taxa inst é calculada para fins didáticos e será atualizada poucas vezes por segundo, já que a Hz altos se torna impossível de ler
                    #####################################


                    if dt_inst>0:

                        self.hz_inst  = 1/dt_inst #hz inst real

                        
                    
                        self.historico_hzs_inst.append(self.hz_inst)
                        self.hz_inst_suavizado = sum(self.historico_hzs_inst) / len(self.historico_hzs_inst)
                    
                    self.tempo_arduino_anterior_us = tempo_arduino_us




                    #print("Recebi uma amostra")

                    if not self.rodando:#Pra controle
                        print("Parando")
                        break




                    self.buffer.adicionar(tempo_arduino_us,timestamp,contador, ax, ay, az, gx, gy, gz)

                    

                    # a ordem deve ser a mesma do gravador
                    
                    '''self.gravador.salvar([
                        tempo_arduino_us,
                        timestamp,
                        contador,
                        ax,
                        ay,
                        az,
                        gx,
                        gy,
                        gz
                    ])'''

        finally:

            self.gravador.fechar()

        
    def parar(self):
        print("Aquisição encerrada.")
        self.rodando=False

    


if __name__ == "__main__":

    collector = Coletor()

    collector.executar()