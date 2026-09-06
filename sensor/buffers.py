# Importa o mutex que protege dados compartilhados entre aquisição e interface.
from threading import Lock
# Importa o array numérico contíguo e as operações de concatenação.
import numpy as np


class BufferSensores:
    """Buffer circular thread-safe usando um único array 2D do NumPy.
    
    Otimizado para alta performance em aquisição de dados do MPU6050.
    - Usa um único array 2D para armazenar todos os dados
    - Operações de snapshot são extremamente rápidas (cópia de arrays NumPy)
    - Thread-safe com Lock para sincronizar acesso
    - Mantém 100% compatibilidade com código existente (atributos ax, ay, az, etc.)
    """
    
    # Nomes das colunas
    COLUNAS = [
        "tempo_arduino_us", "timestamp", "contador",
        "ax", "ay", "az", "gx", "gy", "gz"
    ]

    def __init__(self, tamanho=10000):
        # Guarda o limite de amostras que a janela em memória pode reter.
        self.tamanho_maximo = tamanho
        # Cria a exclusão mútua para todas as leituras e escritas no estado circular.
        self._lock = Lock()
        # Array 2D: (tamanho_maximo, 9 colunas)
        # Reserva nove colunas float64 para manter todas as amostras em um único bloco NumPy.
        self._dados = np.zeros((tamanho, 9), dtype=np.float64)
        # Aponta para a posição física que receberá a próxima amostra.
        self._index = 0      # Próxima posição a escrever
        # Registra quantas posições já contêm dados válidos, até o máximo configurado.
        self._count = 0      # Total de amostras escritas (cresce até tamanho_maximo)

    def adicionar(self, tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz):
        # Impede que um snapshot veja uma linha parcialmente atualizada.
        with self._lock:
            # Escreve os nove valores da nova amostra na posição circular atual.
            self._dados[self._index] = [
                tempo_arduino_us, timestamp, contador,
                ax, ay, az, gx, gy, gz
            ]
            # Avança para a próxima posição e retorna a zero ao atingir a capacidade.
            self._index = (self._index + 1) % self.tamanho_maximo
            # Aumenta a quantidade válida apenas até o buffer ficar cheio.
            if self._count < self.tamanho_maximo:
                self._count += 1

    def vazio(self):
        # Protege a leitura do contador contra escrita concorrente.
        with self._lock:
            # Informa se nenhuma posição contém amostra válida.
            return self._count == 0

    def tamanho_atual(self):
        # Protege a leitura da quantidade atual contra escrita concorrente.
        with self._lock:
            # Entrega a quantidade de amostras válidas atualmente retidas.
            return self._count

    def snapshot(self, quantidade=None):
        """Retorna janela das amostras MAIS RECENTES em ordem cronológica (antigo → novo)."""
        # Mantém toda a decisão de janela e cópia sob o mesmo lock da aquisição.
        with self._lock:
            # Usa todas as amostras disponíveis quando o chamador não limita a janela.
            if quantidade is None:
                quantidade = self._count
            # Limita a solicitação à quantidade realmente armazenada.
            quantidade = min(quantidade, self._count)
            # Retorna arrays vazios independentes para manter o contrato de todas as nove chaves.
            if quantidade == 0:
                return {coluna: self._dados[0:0, i].copy() for i, coluna in enumerate(self.COLUNAS)}
            
            # Usa a região contínua quando o buffer ainda não sobrescreveu a primeira posição.
            if self._count < self.tamanho_maximo:
                # Buffer não cheio: dados contíguos em 0 até _count-1
                # Localiza o primeiro índice da janela mais recente solicitada.
                inicio = self._count - quantidade
                # Copia cada coluna para que a UI não compartilhe memória mutável com o buffer.
                return {
                    coluna: self._dados[inicio:self._count, i].copy()
                    for i, coluna in enumerate(self.COLUNAS)
                }
            else:
                # Buffer cheio: copia somente a janela pedida, sem montar
                # as 10.000 amostras inteiras a cada atualização da UI.
                # Calcula o início físico da janela cronológica mais recente desejada.
                inicio = (self._index - quantidade) % self.tamanho_maximo
                # Calcula o fim exclusivo dessa janela na numeração física estendida.
                fim = inicio + quantidade

                # Usa uma única fatia quando a janela não atravessa o final do array físico.
                if fim <= self.tamanho_maximo:
                    dados_cronologicos = self._dados[inicio:fim, :]
                else:
                    # Concatena os dois trechos quando a janela cruza o ponto de wrap-around.
                    dados_cronologicos = np.concatenate([
                        self._dados[inicio:, :],
                        self._dados[:fim - self.tamanho_maximo, :]
                    ])

                # Entrega cópias por coluna para preservar a ordem cronológica e isolar o consumidor.
                return {
                    coluna: dados_cronologicos[:, i].copy()
                    for i, coluna in enumerate(self.COLUNAS)
                }

    def limpar(self):
        # Protege o reset da posição e do contador contra aquisição concorrente.
        with self._lock:
            # Faz a próxima escrita voltar à primeira posição física.
            self._index = 0
            # Marca todas as posições como logicamente vazias sem zerar o array alocado.
            self._count = 0

    # =========================================================================
    # MÉTODO AUXILIAR: Retorna slice correto considerando wrap-around
    # =========================================================================
    
    def _get_coluna_slice(self, coluna_idx):
        """Retorna view da coluna com TODAS as amostras em ordem cronológica (mais antigo → mais novo).
        
        Lida corretamente com wrap-around: quando buffer está cheio (_count == tamanho_maximo),
        os dados cronológicos estão em _index até fim, depois 0 até _index-1.
        """
        # Protege o cálculo da ordem e as fatias contra alteração durante a leitura.
        with self._lock:
            # Retorna a fatia vazia da coluna solicitada quando não há histórico.
            if self._count == 0:
                return self._dados[0:0, coluna_idx]  # array vazio
            
            # Retorna uma view contínua enquanto o buffer não alcançou a capacidade.
            if self._count < self.tamanho_maximo:
                # Buffer ainda não encheu: dados estão em 0 até _count-1 (contíguo, ordem cronológica)
                return self._dados[:self._count, coluna_idx]
            else:
                # Une os dois trechos para que a coluna volte em ordem de amostra, não em ordem física.
                # Buffer cheio + wrap-around: ordem cronológica = _index até fim, depois 0 até _index-1
                return np.concatenate([
                    self._dados[self._index:, coluna_idx],
                    self._dados[:self._index, coluna_idx]
                ])

    # =========================================================================
    # PROPRIEDADES PARA COMPATIBILIDADE (janela.py acessa buffer.ax, etc.)
    # =========================================================================
    
    @property
    def tempo_arduino_us(self):
        # Expõe a primeira coluna para compatibilidade com consumidores legados.
        return self._get_coluna_slice(0)
    
    @property
    def timestamp(self):
        # Expõe o timestamp do PC para compatibilidade com consumidores legados.
        return self._get_coluna_slice(1)
    
    @property
    def contador(self):
        # Expõe o contador do firmware para compatibilidade com consumidores legados.
        return self._get_coluna_slice(2)
    
    @property
    def ax(self):
        # Expõe a aceleração X para compatibilidade com consumidores legados.
        return self._get_coluna_slice(3)
    
    @property
    def ay(self):
        # Expõe a aceleração Y para compatibilidade com consumidores legados.
        return self._get_coluna_slice(4)
    
    @property
    def az(self):
        # Expõe a aceleração Z para compatibilidade com consumidores legados.
        return self._get_coluna_slice(5)
    
    @property
    def gx(self):
        # Expõe a velocidade angular X para compatibilidade com consumidores legados.
        return self._get_coluna_slice(6)
    
    @property
    def gy(self):
        # Expõe a velocidade angular Y para compatibilidade com consumidores legados.
        return self._get_coluna_slice(7)
    
    @property
    def gz(self):
        # Expõe a velocidade angular Z para compatibilidade com consumidores legados.
        return self._get_coluna_slice(8)
