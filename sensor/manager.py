from threading import Thread

from coletor import Coletor


class SensorManager:

    def __init__(self):

        self.collector = Collector()

        self.thread = None

        self.rodando = False


manager = SensorManager()