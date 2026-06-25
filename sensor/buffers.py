#buffers.py -> Só guarda dados.
from collections import deque


class BufferSensores:
    def __init__(self,tamanho =10000):

        self.timestamp = deque(maxlen=tamanho)
        self.contador = deque(maxlen=tamanho)
        
        self.ax = deque(maxlen=tamanho)
        self.ay = deque(maxlen=tamanho)
        self.az = deque(maxlen=tamanho)
    
    def adicionar(self,timestamp,contador,ax,ay,az,gx,gy,gz):
        self.timestamp.append(timestamp)
        self.contador.append(contador)

        self.ax.append(ax)
        self.ay.append(ay)
        self.az.append(az)

        self.gx.append(gx)
        self.gy.append(gy)
        self.gz.append(gz)