# Fornece a fila limitada que desacopla aquisição e persistência.
from queue import Queue
# Cria a thread dedicada ao loop serial.
from threading import Thread

# Implementa o produtor de linhas de nove valores e seu buffer para a interface.
from sensor.coletor import Coletor
# Implementa o consumidor assíncrono das linhas que serão persistidas.
from sensor.gravador_worker import GravadorWorker


class SensorManager:

    def __init__(self):
        # Cria o coletor reutilizado pelas sessões controladas por esta instância.
        self.coletor = Coletor()

        # Referencia a thread do coletor enquanto há uma sessão em execução.
        self.thread = None
        # Referencia a fila temporária que liga coletor e gravador na sessão.
        self.fila_gravacao = None
        # Referencia a thread responsável pelo CSV enquanto a sessão está ativa.
        self.gravador_thread = None

    def iniciar(self):
        # Evita iniciar uma segunda sessão enquanto a thread atual ainda está viva.
        if self.thread is not None and self.thread.is_alive():
            return

        # A fila absorve picos temporarios de escrita sem parar a thread serial.
        self.fila_gravacao = Queue(maxsize=50_000)
        # Entrega a fila recém-criada ao produtor antes de iniciar qualquer thread.
        self.coletor.configurar_fila_gravacao(self.fila_gravacao)

        # Cria o consumidor do CSV antes do produtor para haver destino para a primeira amostra.
        self.gravador_thread = GravadorWorker(self.fila_gravacao)
        # Inicia o bloqueio em Queue.get() do gravador.
        self.gravador_thread.start()

        # Cria a thread daemon que executa a aquisição serial sem bloquear o chamador.
        self.thread = Thread(target=self.coletor.executar, name="coletor-serial", daemon=True)

        # Inicia o produtor depois de a fila e o consumidor estarem prontos.
        self.thread.start()

    def parar(self):
        # Sem thread, nao houve sessao ativa a encerrar.
        if self.thread is None:
            return False

        # Solicita a parada cooperativa do loop de aquisição.
        self.coletor.parar()

        # Aguarda o produtor terminar para que nenhuma nova linha seja enfileirada depois da sentinela.
        if self.thread is not None:
            self.thread.join()

        # O sentinela faz o gravador descarregar o ultimo lote e fechar o arquivo.
        if self.fila_gravacao is not None:
            self.fila_gravacao.put(None)

        if self.gravador_thread is not None:
            # Aguarda o consumo da sentinela, o flush e o fechamento do arquivo.
            self.gravador_thread.join()

        # Remove as referências da sessão encerrada, permitindo iniciar uma nova sessão.
        self.thread = None
        self.gravador_thread = None
        self.fila_gravacao = None

        return True

    @property
    def buffer(self):
        # Expõe à interface o buffer circular mantido pelo coletor, sem cópia intermediária.
        return self.coletor.buffer


# Instância global usada como singleton prático pelos módulos de interface e teste.
manager = SensorManager()
