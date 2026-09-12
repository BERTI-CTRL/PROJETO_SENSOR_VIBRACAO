# Importa o histórico circular compartilhado com a interface.
from sensor.buffers import BufferSensores
# Importa a deque limitada usada para suavizar a frequência instantânea.
from collections import deque
# Importa a exceção que sinaliza uma fila de gravação cheia.
from queue import Full

# Importa o gerador que transforma linhas seriais em amostras numéricas.
from sensor.serial_reader import ler_dados
from sensor.config import BAUD_RATE, PORTA_SERIAL
 

class Coletor:
    def __init__(self, porta=PORTA_SERIAL, baudrate=BAUD_RATE, fila_gravacao=None):
        # Começa parado; executar() ativa este sinal antes de consumir a serial.
        self.rodando = False

        # Guarda a porta configurada para passá-la ao leitor serial.
        self.porta = porta 
        # Guarda o baud rate configurado sem alterá-lo durante a sessão.
        self.baudrate = baudrate
        # Cria a janela circular em memória que alimenta a interface.
        self.buffer = BufferSensores()

        # A fila e consumida por GravadorWorker. O Coletor nunca escreve no disco.
        # Mantém a fila opcional usada pelo trabalhador de gravação assíncrona.
        self.fila_gravacao = fila_gravacao
        # Conta amostras aceitas na sessão atual.
        self.numero_amostras = 0
        # Armazena o último contador recebido para identificar lacunas.
        self.contador_anterior = None
        # Conta quantos eventos de salto foram detectados.
        self.saltos_contador = 0
        # Acumula o número de amostras ausentes estimadas pelos saltos.
        self.amostras_perdidas = 0
        # Conta amostras que chegaram, mas não puderam seguir para o CSV por fila cheia.
        self.amostras_nao_enfileiradas = 0

        # Inicializa a estimativa acumulada de frequência da sessão.
        self.hz_medio = 0 #  valor do hz medio
        # Inicializa a frequência entre as duas últimas amostras válidas.
        self.hz_inst = 0 # valor do hz instantaneo
        # Inicializa a média móvel da frequência instantânea.
        self.hz_inst_suavizado = 0 # valor do hz instantaneo suavizado

        # Reserva o primeiro micros() recebido para calcular a frequência média.
        self.tempo_arduino_inicial_us = 0
        # Reserva o micros() anterior para calcular a frequência instantânea.
        self.tempo_arduino_anterior_us = 0  

        # Mantém no máximo as 100 últimas frequências instantâneas para a média móvel.
        self.historico_hzs_inst = deque(maxlen=100) # fila usa da para calcular o valor hz instantaneo suavizado - > GUARDA OS ÚLTIMOS 100 HZ 

    def configurar_fila_gravacao(self, fila_gravacao):
        """Define a fila usada para entregar dados ao gravador assíncrono."""
        # Substitui a fila de destino, permitindo ao manager configurar o gravador.
        self.fila_gravacao = fila_gravacao



    def _registrar_salto(self, contador):
        # Reconhece uma lacuna somente se o contador avançou mais de uma unidade.
        if self.contador_anterior is not None and contador > self.contador_anterior + 1:


            # Calcula quantas amostras deveriam existir entre os dois contadores.
            perdidas = int(contador - self.contador_anterior - 1)
            
            # Registra um evento de salto, independentemente de seu tamanho.
            self.saltos_contador += 1
            # Acumula a quantidade estimada de amostras não recebidas pela serial.
            self.amostras_perdidas += perdidas
            # Informa no console o intervalo e a estimativa de perda detectados.
            print(
                f"[Coletor] Salto no contador: "
                f"{self.contador_anterior:.0f} -> {contador:.0f} "
                f"({perdidas} amostras perdidas)"
            )

        # Atualiza a referência para comparar a próxima amostra recebida.
        self.contador_anterior = contador

    def _enfileirar_gravacao(self, linha):
        # Não tenta gravar quando nenhum consumidor CSV foi configurado.
        if self.fila_gravacao is None:
            return

        # Tenta entregar a amostra sem bloquear a thread de aquisição.
        try:
            # A thread serial nao pode esperar pelo disco. Se a fila lotar,
            # registramos explicitamente a perda em vez de bloquear a serial. Como sempre, a perfomance manda na aquisição
            # Insere imediatamente a linha ou lança Full se o gravador não acompanha a produção.
            self.fila_gravacao.put_nowait(linha)
        # Trata somente a saturação esperada da fila de gravação.
        except Full:
            # Conta a perda de persistência, distinta da perda observada no contador serial.
            self.amostras_nao_enfileiradas += 1
            # Reduz o volume de logs, mantendo uma mensagem para a primeira e cada mil perdas.
            if self.amostras_nao_enfileiradas % 1000 == 1:
                print(
                    "[Coletor] Fila de gravacao cheia; "
                    "amostras deixaram de ser enviadas ao CSV."
                )

    def executar(self):

        # Sinaliza ao leitor serial que esta sessão está ativa.
        self.rodando = True

        # Reinicia a contagem de amostras para uma nova sessão.
        self.numero_amostras = 0
        # Reinicia a referência de início usada no cálculo de frequência média.
        self.tempo_arduino_inicial_us = 0
        # Reinicia a referência anterior usada no cálculo instantâneo.
        self.tempo_arduino_anterior_us = 0
        # Remove a referência de contador da sessão anterior.
        self.contador_anterior = None
        # Zera a quantidade de lacunas detectadas nesta sessão.
        self.saltos_contador = 0
        # Zera a estimativa de amostras ausentes nesta sessão.
        self.amostras_perdidas = 0
        # Zera a quantidade de linhas não encaminhadas ao CSV nesta sessão.
        self.amostras_nao_enfileiradas = 0

        # Zera a frequência média até haver pelo menos duas amostras.
        self.hz_medio = 0
        # Zera a frequência instantânea até haver um intervalo válido.
        self.hz_inst = 0
        # Zera a média móvel até o histórico receber valores.
        self.hz_inst_suavizado = 0



        # Remove frequências da sessão anterior antes de calcular a nova média móvel.
        self.historico_hzs_inst.clear()

        # Registra que o loop de aquisição foi iniciado.
        print("Coletor iniciado")



        
        # Consome continuamente as tuplas de nove valores produzidas pela camada serial.
        for tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz in ler_dados(
            porta=self.porta,
            baudrate=self.baudrate,
            deve_continuar=lambda: self.rodando,
        ):
            # Interrompe se parar() foi chamado após o leitor ter produzido esta amostra.
            if not self.rodando:
                print("Parando")
                break

            # Registra a amostra válida antes dos cálculos de frequência.
            self.numero_amostras += 1
            # Atualiza as métricas de lacunas com o contador fornecido pelo firmware.
            self._registrar_salto(contador)

            # Mostra um marco de progresso para cada mil amostras do firmware.
            if contador % 1000 == 0:
                print(f"[Coletor] : {contador}")

            # Na primeira amostra, cria as duas referências de tempo sem calcular frequência.
            if self.numero_amostras == 1:
                # Define o início da sessão no relógio micros() do Arduino.
                self.tempo_arduino_inicial_us = tempo_arduino_us
                # Define também a referência anterior para o próximo intervalo instantâneo.
                self.tempo_arduino_anterior_us = tempo_arduino_us
            else:
                # Converte o tempo decorrido desde a primeira amostra de micros para segundos.
                dt_total = (tempo_arduino_us - self.tempo_arduino_inicial_us) / 1_000_000 #segundos ne

                # Evita divisão por zero ou por intervalo de tempo não crescente,quebraria o prog.
                if dt_total > 0:
                    # Calcula a taxa média pelos intervalos entre as amostras da sessão.
                    self.hz_medio = (self.numero_amostras - 1) / dt_total

                # Converte o intervalo entre duas amostras consecutivas de micros para segundos.
                dt_inst = (tempo_arduino_us - self.tempo_arduino_anterior_us) / 1_000_000

                # Atualiza frequência instantânea somente para intervalo positivo.
                if dt_inst > 0:
                    # Inverte o intervalo de amostragem para obter hertz instantâneo.
                    self.hz_inst = 1 / dt_inst
                    # Inclui a frequência no histórico limitado a cem valores.
                    self.historico_hzs_inst.append(self.hz_inst)
                    # Calcula a média móvel dos valores atualmente preservados no histórico.
                    self.hz_inst_suavizado = (
                        sum(self.historico_hzs_inst) / len(self.historico_hzs_inst)
                    )

                # Move a referência temporal para a amostra que acaba de ser processada. olhe linha 178'
                self.tempo_arduino_anterior_us = tempo_arduino_us

            # Copia a amostra completa para o buffer circular consumido pela interface.
            self.buffer.adicionar(
                tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz
            )

            # Entrega a mesma sequência de nove valores à fila do CSV, sem bloquear a serial.
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
        # Informa o encerramento solicitado no console.
        print("Aquisição encerrada.")
        # Faz o callback do leitor e o loop de execução terminarem na próxima oportunidade.
        self.rodando=False

    


if __name__ == "__main__":
    # Importa a fila concreta somente para o modo de execução manual.
    from queue import Queue

    # Importa o consumidor assíncrono somente para o modo de execução manual.
    from sensor.gravador_worker import GravadorWorker

    # Cria uma fila limitada para desacoplar a aquisição da escrita em disco.
    fila_gravacao = Queue(maxsize=50_000)
    # Cria o trabalhador que consome e grava as linhas da fila.
    gravador = GravadorWorker(fila_gravacao)
    # Inicia o trabalhador antes de iniciar a produção de amostras.
    gravador.start()

    # Configura o coletor manual com a fila que alimenta o trabalhador.
    collector = Coletor(fila_gravacao=fila_gravacao)
    # Mantém a aquisição em execução até interrupção do teclado.
    try:
        collector.executar()
    # Converte Ctrl+C em solicitação normal de parada do coletor.
    except KeyboardInterrupt:
        collector.parar()
    # Encerra o gravador com sentinela e aguarda o término antes de sair.
    finally:
        fila_gravacao.put(None)
        gravador.join()
