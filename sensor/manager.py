from threading import Thread

from collector import Collector


class SensorManager:

    def __init__(self):

        self.collector = Collector()

        self.thread = None

        self.rodando = False


manager = SensorManager()