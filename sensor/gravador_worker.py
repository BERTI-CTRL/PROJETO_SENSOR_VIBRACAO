"""Thread dedicada para persistir as amostras no CSV.

Esta thread nunca acessa a porta serial. Assim, uma escrita lenta no disco
nao interrompe a leitura feita pelo Coletor.
"""

# Fornece a classe base para executar a persistência fora da thread de aquisição.
from threading import Thread

# Cria e fecha o arquivo CSV usado exclusivamente por este trabalhador.
from sensor.gravador import GravadorCSV


class GravadorWorker(Thread):
    """Consome linhas da fila e as grava em lotes no CSV."""

    def __init__(self, fila, tamanho_buffer=1000):
        # Registra uma thread daemon nomeada para diagnóstico; o manager ainda faz join explícito.
        super().__init__(name="gravador-csv", daemon=True)
        # Recebe a Queue compartilhada, cuja sincronização é provida pela própria Queue.
        self.fila = fila
        # Guarda o tamanho dos lotes que será passado ao GravadorCSV.
        self.tamanho_buffer = tamanho_buffer
        # Expõe uma eventual falha ao código que controla a sessão.
        self.erro = None

    def run(self):
        # Permite que o finally saiba se a criação do gravador chegou a ocorrer.
        gravador = None

        try:
            # Abre o CSV dentro da thread para concentrar nela todo o acesso ao arquivo.
            gravador = GravadorCSV(tamanho_buffer=self.tamanho_buffer)

            while True:
                # Aguarda sem polling a próxima linha ou a sentinela de encerramento.()
                linha = self.fila.get()
                try:
                    # None e o sentinela enviado pelo SensorManager ao parar.
                    if linha is None:
                        break

                    # Entrega a amostra de nove valores ao buffer de escrita em lote.
                    gravador.salvar(linha)
                finally:
                    # Confirma a conclusão inclusive para sentinela ou falha durante salvar().
                    self.fila.task_done()

        except Exception as erro:
            # Conserva a exceção para diagnóstico externo em vez de deixá-la silenciosa na thread.
            self.erro = erro
            # Mantém a notificação de falha existente no console.
            print(f"[Gravador] Erro: {erro}")
        finally:
            # Só fecha quando a construção do gravador produziu uma instância válida.
            if gravador is not None:
                try:
                    # Descarrega o último lote e fecha o CSV em qualquer caminho de saída.
                    gravador.fechar()
                except Exception as erro:
                    # Preserva o primeiro erro, sem ocultá-lo por uma falha posterior de fechamento.
                    self.erro = self.erro or erro
                    # Mantém visível no console a falha específica do fechamento.
                    print(f"[Gravador] Erro ao fechar CSV: {erro}")
