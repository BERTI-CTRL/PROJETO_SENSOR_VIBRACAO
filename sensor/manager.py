from queue import Queue
from threading import Thread

from sensor.coletor import Coletor
from sensor.gravador_worker import GravadorWorker


class SensorManager:

    def __init__(self):

        self.coletor = Coletor()

        self.thread = None
        self.fila_gravacao = None
        self.gravador_thread = None

    def iniciar(self):
        if self.thread is not None and self.thread.is_alive():
            return
        
        # A fila absorve picos temporarios de escrita sem parar a thread serial.
        self.fila_gravacao = Queue(maxsize=50_000)
        self.coletor.configurar_fila_gravacao(self.fila_gravacao)

        self.gravador_thread = GravadorWorker(self.fila_gravacao)
        self.gravador_thread.start()

        self.thread = Thread(target=self.coletor.executar, name="coletor-serial", daemon=True)
        
        self.thread.start()

    def parar(self):
        self.coletor.parar()

        if self.thread is not None:
            self.thread.join()

        # O sentinela faz o gravador descarregar o ultimo lote e fechar o arquivo.
        if self.fila_gravacao is not None:
            self.fila_gravacao.put(None)

        if self.gravador_thread is not None:
            self.gravador_thread.join()

        self.thread = None
        self.gravador_thread = None
        self.fila_gravacao = None

    @property
    def buffer(self):
        
        return self.coletor.buffer  #


manager = SensorManager()
