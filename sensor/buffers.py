#buffers.py -> Só guarda dados.
from collections import deque
from itertools import islice
from threading import Lock


class BufferSensores:
    """Histórico circular compartilhado entre aquisição e interface."""

    def __init__(self, tamanho=10000):
        self.tamanho_maximo = tamanho
        # Um lock protege a atualização conjunta dos nove sinais.
        # Ele nunca é mantido durante leitura serial, gravação CSV ou desenho.
        self._lock = Lock()

        self.tempo_arduino_us = deque(maxlen=tamanho)
        self.timestamp = deque(maxlen=tamanho)
        self.contador = deque(maxlen=tamanho)
        
        self.ax = deque(maxlen=tamanho)
        self.ay = deque(maxlen=tamanho)
        self.az = deque(maxlen=tamanho)

        self.gx = deque(maxlen=tamanho)
        self.gy = deque(maxlen=tamanho)
        self.gz = deque(maxlen=tamanho)
    
    def adicionar(self, tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz):
        with self._lock:
            self.tempo_arduino_us.append(tempo_arduino_us)
            self.timestamp.append(timestamp)
            self.contador.append(contador)

            self.ax.append(ax)
            self.ay.append(ay)
            self.az.append(az)

            self.gx.append(gx)
            self.gy.append(gy)
            self.gz.append(gz)

        # Mantido como log de depuração, mas fora do lock para nunca atrasar a UI.
        if contador % 1000 == 0:
            print(f"[Buffer] {contador}")

    def vazio(self):
        """
        Invariante da classe:

        Todos os deques possuem exatamente o mesmo número de amostras.

        Dessa forma, basta verificar o tamanho de qualquer um deles
        para saber se existem dados armazenados.

        tip Em vez de acessar diretamente os atributos internos de uma classe (len(buffer.ax)), prefira perguntar à própria classe sobre seu estado (buffer.vazio()). 
        Isso reduz o acoplamento e permite alterar a implementação interna sem afetar o restante do sistema.
        """
        with self._lock:
            return len(self.ax) == 0

    def tamanho_atual(self):
        """Retorna a quantidade de amostras no histórico."""
        with self._lock:
            return len(self.contador)

    def snapshot(self, quantidade=None):
        """Copia um recorte consistente de todos os sinais.

        A interface deve usar este método em vez de copiar cada deque separadamente.
        Assim, todos os eixos retornados pertencem exatamente às mesmas amostras.
        """
        with self._lock:
            total = len(self.contador)
            if quantidade is None:
                inicio = 0
            else:
                inicio = max(0, total - quantidade)

            fim = total
            return {
                "tempo_arduino_us": list(islice(self.tempo_arduino_us, inicio, fim)),
                "timestamp": list(islice(self.timestamp, inicio, fim)),
                "contador": list(islice(self.contador, inicio, fim)),
                "ax": list(islice(self.ax, inicio, fim)),
                "ay": list(islice(self.ay, inicio, fim)),
                "az": list(islice(self.az, inicio, fim)),
                "gx": list(islice(self.gx, inicio, fim)),
                "gy": list(islice(self.gy, inicio, fim)),
                "gz": list(islice(self.gz, inicio, fim)),
            }

    def limpar(self):
        """Remove o histórico visual sem interromper a aquisição."""
        with self._lock:
            self.tempo_arduino_us.clear()
            self.timestamp.clear()
            self.contador.clear()
            self.ax.clear()
            self.ay.clear()
            self.az.clear()
            self.gx.clear()
            self.gy.clear()
            self.gz.clear()
