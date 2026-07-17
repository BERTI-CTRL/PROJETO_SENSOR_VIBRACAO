from threading import Thread

from sensor.coletor import Coletor


class SensorManager:

    def __init__(self):

        self.coletor = Coletor()

        self.thread = None

    def iniciar(self):
        if self.thread is not None and self.thread.is_alive():
            return
        
        self.thread = Thread(target= self.coletor.executar,daemon=True)
        
        self.thread.start()

    def parar(self):
        self.coletor.parar()

        if self.thread is not None:
            self.thread.join()
        
        self.thread = None

    @property
    def buffer(self):
        
        return self.coletor.buffer  #


manager = SensorManager()