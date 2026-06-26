#coletor.py ->Só processa uma amostra.
from buffers import BufferSensores


from serial_reader import ler_dados
from gravador import GravadorCSV


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
        
    
    def executar(self):
        self.rodando = True
        try:

                for timestamp,contador, ax, ay, az, gx, gy, gz in ler_dados(
                    porta=self.porta,
                    baudrate=self.baudrate
                ):
                    if not self.rodando:#Pra controle
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