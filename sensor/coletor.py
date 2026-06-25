#coletor.py ->Só processa uma amostra.
from buffers import BufferSensores
import time

from serial_reader import ler_dados
from gravador import GravadorCSV


class Coletor():
    def __init__(self,porta="COM5",baudrate = 115200):
        

        self.porta = porta 
        self.baudrate = baudrate
        self.buffer = BufferSensores()

        self.gravador = GravadorCSV(
            arquivo="dados_vibracao.csv",
            tamanho_buffer=1000
        )
        
    
    def executar(self):
        try:

            for timestamp,contador, ax, ay, az, gx, gy, gz in ler_dados(
                porta=self.porta,
                baudrate=self.baudrate
            ):
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

        except KeyboardInterrupt:

            self.gravador.fechar()

            print("Aquisição encerrada.")


if __name__ == "__main__":

    collector = Collector()

    collector.executar()