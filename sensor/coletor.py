#coletor.py ->Só processa uma amostra.
from sensor.buffers import BufferSensores
from collections import deque
from queue import Full

from sensor.serial_reader import ler_dados


class Coletor:
    def __init__(self, porta="COM4", baudrate=115200, fila_gravacao=None):
        self.rodando = False

        self.porta = porta 
        self.baudrate = baudrate
        self.buffer = BufferSensores()

        # A fila e consumida por GravadorWorker. O Coletor nunca escreve no disco.
        self.fila_gravacao = fila_gravacao
        self.numero_amostras = 0
        self.contador_anterior = None
        self.saltos_contador = 0
        self.amostras_perdidas = 0
        self.amostras_nao_enfileiradas = 0

        self.hz_medio = 0 #  valor do hz medio
        self.hz_inst = 0 # valor do hz instantaneo
        self.hz_inst_suavizado = 0 # valor do hz instantaneo suavizado

        self.tempo_arduino_inicial_us = 0
        self.tempo_arduino_anterior_us = 0

        self.historico_hzs_inst = deque(maxlen=100) # fila usada para calcular o valor hz instantaneo suavizado - > GUARDA OS ÚLTIMOS 100 HZ 

    def configurar_fila_gravacao(self, fila_gravacao):
        """Define a fila usada para entregar dados ao gravador assíncrono."""
        self.fila_gravacao = fila_gravacao

    def _registrar_salto(self, contador):
        if self.contador_anterior is not None and contador > self.contador_anterior + 1:
            perdidas = int(contador - self.contador_anterior - 1)
            self.saltos_contador += 1
            self.amostras_perdidas += perdidas
            print(
                f"[Coletor] Salto no contador: "
                f"{self.contador_anterior:.0f} -> {contador:.0f} "
                f"({perdidas} amostras perdidas)"
            )

        self.contador_anterior = contador

    def _enfileirar_gravacao(self, linha):
        if self.fila_gravacao is None:
            return

        try:
            # A thread serial nao pode esperar pelo disco. Se a fila lotar,
            # registramos explicitamente a perda em vez de bloquear a serial.
            self.fila_gravacao.put_nowait(linha)
        except Full:
            self.amostras_nao_enfileiradas += 1
            if self.amostras_nao_enfileiradas % 1000 == 1:
                print(
                    "[Coletor] Fila de gravacao cheia; "
                    "amostras deixaram de ser enviadas ao CSV."
                )

    def executar(self):

        self.rodando = True

        self.numero_amostras = 0
        self.tempo_arduino_inicial_us = 0
        self.tempo_arduino_anterior_us = 0
        self.contador_anterior = None
        self.saltos_contador = 0
        self.amostras_perdidas = 0
        self.amostras_nao_enfileiradas = 0

        self.hz_medio = 0
        self.hz_inst = 0
        self.hz_inst_suavizado = 0



        self.historico_hzs_inst.clear()

        print("Coletor iniciado")



        
        for tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz in ler_dados(
            porta=self.porta,
            baudrate=self.baudrate,
            deve_continuar=lambda: self.rodando,
        ):
            if not self.rodando:
                print("Parando")
                break

            self.numero_amostras += 1
            self._registrar_salto(contador)

            if contador % 1000 == 0:
                print(f"[Coletor] : {contador}")

            if self.numero_amostras == 1:
                self.tempo_arduino_inicial_us = tempo_arduino_us
                self.tempo_arduino_anterior_us = tempo_arduino_us
            else:
                dt_total = (tempo_arduino_us - self.tempo_arduino_inicial_us) / 1_000_000

                if dt_total > 0:
                    self.hz_medio = (self.numero_amostras - 1) / dt_total

                dt_inst = (tempo_arduino_us - self.tempo_arduino_anterior_us) / 1_000_000

                if dt_inst > 0:
                    self.hz_inst = 1 / dt_inst
                    self.historico_hzs_inst.append(self.hz_inst)
                    self.hz_inst_suavizado = (
                        sum(self.historico_hzs_inst) / len(self.historico_hzs_inst)
                    )

                self.tempo_arduino_anterior_us = tempo_arduino_us

            self.buffer.adicionar(
                tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz
            )

            self._enfileirar_gravacao([
                tempo_arduino_us,
                timestamp,
                contador,
                ax,
                ay,
                az,
                gx,
                gy,
                gz,
            ])

        
    def parar(self):
        print("Aquisição encerrada.")
        self.rodando=False

    


if __name__ == "__main__":
    from queue import Queue

    from sensor.gravador_worker import GravadorWorker

    fila_gravacao = Queue(maxsize=50_000)
    gravador = GravadorWorker(fila_gravacao)
    gravador.start()

    collector = Coletor(fila_gravacao=fila_gravacao)
    try:
        collector.executar()
    except KeyboardInterrupt:
        collector.parar()
    finally:
        fila_gravacao.put(None)
        gravador.join()
