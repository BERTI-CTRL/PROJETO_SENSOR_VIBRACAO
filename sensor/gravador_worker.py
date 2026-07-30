"""Thread dedicada para persistir as amostras no CSV.

Esta thread nunca acessa a porta serial. Assim, uma escrita lenta no disco
nao interrompe a leitura feita pelo Coletor.
"""

from threading import Thread

from sensor.gravador import GravadorCSV


class GravadorWorker(Thread):
    """Consome linhas da fila e as grava em lotes no CSV."""

    def __init__(self, fila, tamanho_buffer=1000):
        super().__init__(name="gravador-csv", daemon=True)
        self.fila = fila
        self.tamanho_buffer = tamanho_buffer
        self.erro = None

    def run(self):
        gravador = None

        try:
            gravador = GravadorCSV(tamanho_buffer=self.tamanho_buffer)

            while True:
                linha = self.fila.get()
                try:
                    # None e o sentinela enviado pelo SensorManager ao parar.
                    if linha is None:
                        break

                    gravador.salvar(linha)
                finally:
                    self.fila.task_done()

        except Exception as erro:
            # A interface/manager pode consultar este atributo e informar a falha.
            self.erro = erro
            print(f"[Gravador] Erro: {erro}")
        finally:
            if gravador is not None:
                try:
                    gravador.fechar()
                except Exception as erro:
                    self.erro = self.erro or erro
                    print(f"[Gravador] Erro ao fechar CSV: {erro}")
