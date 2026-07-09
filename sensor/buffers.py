#buffers.py -> Só guarda dados.
from collections import deque


class BufferSensores:
    def __init__(self,tamanho =10000):

        self.timestamp = deque(maxlen=tamanho)
        self.contador = deque(maxlen=tamanho)
        
        self.ax = deque(maxlen=tamanho)
        self.ay = deque(maxlen=tamanho)
        self.az = deque(maxlen=tamanho)

        self.gx = deque(maxlen=tamanho)
        self.gy = deque(maxlen=tamanho)
        self.gz = deque(maxlen=tamanho)
    
    def adicionar(self,timestamp,contador,ax,ay,az,gx,gy,gz):
        self.timestamp.append(timestamp)
        self.contador.append(contador)

        self.ax.append(ax)
        self.ay.append(ay)
        self.az.append(az)

        self.gx.append(gx)
        self.gy.append(gy)
        self.gz.append(gz)

    def vazio(self):
        """
        Invariante da classe:

        Todos os deques possuem exatamente o mesmo número de amostras.

        Dessa forma, basta verificar o tamanho de qualquer um deles
        para saber se existem dados armazenados.

        tip Em vez de acessar diretamente os atributos internos de uma classe (len(buffer.ax)), prefira perguntar à própria classe sobre seu estado (buffer.vazio()). 
        Isso reduz o acoplamento e permite alterar a implementação interna sem afetar o restante do sistema.
        """
        return len(self.ax)==0