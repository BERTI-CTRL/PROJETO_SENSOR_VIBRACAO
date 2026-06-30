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

        self.t0 = 0 
        self.t_anterior = 0

        self.historico_hzs_inst = deque(maxlen=100) # fila usada para calcular o valor hz instantaneo suavizado - > GUARDA OS ÚLTIMOS 100 HZ 
    
    def executar(self):

        self.rodando = True

        self.numero_amostras = 0

        self.hz_medio = 0
        self.hz_inst = 0
        self.hz_inst_suavizado = 0


        self.t0 = time.perf_counter()
        self.t_anterior = self.t0

        self.historico_hzs_inst.clear()

        print("Coletor iniciado")



        
        try:

                for timestamp,contador, ax, ay, az, gx, gy, gz in ler_dados(
                    porta=self.porta,
                   baudrate=self.baudrate
                ):
                    self.numero_amostras += 1

                    #####################################
                    # Estatísticas da aquisição
                    #####################################
                    agora = time.perf_counter()
                    dt = agora - self.t0


                    #####################################
                    #Hertz médio
                    #####################################
                    

                    if dt>0:

                        self.hz_medio = self.numero_amostras/dt



                    ###################################
                    #Hz inst
                    ###################################
                    dt_inst = agora = self.t_anterior
                    self.t_anterior = agora



                    #####################################
                    #Hertz instantâneo Suavizado -> menos suscetível a grandes variações. Isso é importante pois a taxa de hz sofre microvariações em decorrência dos tipos dedados envolvidos
                    #e à própria variação da precisão computacional. A taxa inst é calculada para fins didáticos e será atualizada poucas vezes por segundo, já que a Hz altos se torna impossível de ler
                    #####################################

                    dt_inst = agora - self.t_anterior

                    self.t_anterior = agora

                    if dt_inst>0:

                        self.hz_inst  = 1/dt_inst #hz inst real
                        

                        self.deque_hzs_inst_suavizado.append(self.hz_inst)
                        self.hz_inst_suavizado = sum(self.historico_hzs_inst) / len(self.historico_hzs_inst)


                    ####################################
                    #Hz instantâneo
                    ####################################
                    #agora = time.perf_counter()
                    #dt_inst = agora - self.t_anterior

                    '''self.t_anterior = agora

                    if dt_inst>0:

                        hz = 1/dt_inst'''

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