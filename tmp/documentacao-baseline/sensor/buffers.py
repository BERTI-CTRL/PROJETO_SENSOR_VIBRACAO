# buffers.py - Buffer circular otimizado com NumPy (compatível com código existente)
from threading import Lock
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
        self.tamanho_maximo = tamanho
        self._lock = Lock()
        # Array 2D: (tamanho_maximo, 9 colunas)
        self._dados = np.zeros((tamanho, 9), dtype=np.float64)
        self._index = 0      # Próxima posição a escrever
        self._count = 0      # Total de amostras escritas (cresce até tamanho_maximo)

    def adicionar(self, tempo_arduino_us, timestamp, contador, ax, ay, az, gx, gy, gz):
        with self._lock:
            self._dados[self._index] = [
                tempo_arduino_us, timestamp, contador,
                ax, ay, az, gx, gy, gz
            ]
            self._index = (self._index + 1) % self.tamanho_maximo
            if self._count < self.tamanho_maximo:
                self._count += 1

    def vazio(self):
        with self._lock:
            return self._count == 0

    def tamanho_atual(self):
        with self._lock:
            return self._count

    def snapshot(self, quantidade=None):
        """Retorna janela das amostras MAIS RECENTES em ordem cronológica (antigo → novo)."""
        with self._lock:
            if quantidade is None:
                quantidade = self._count
            quantidade = min(quantidade, self._count)
            if quantidade == 0:
                return {coluna: self._dados[0:0, i].copy() for i, coluna in enumerate(self.COLUNAS)}
            
            if self._count < self.tamanho_maximo:
                # Buffer não cheio: dados contíguos em 0 até _count-1
                inicio = self._count - quantidade
                return {
                    coluna: self._dados[inicio:self._count, i].copy()
                    for i, coluna in enumerate(self.COLUNAS)
                }
            else:
                # Buffer cheio: copia somente a janela pedida, sem montar
                # as 10.000 amostras inteiras a cada atualização da UI.
                inicio = (self._index - quantidade) % self.tamanho_maximo
                fim = inicio + quantidade

                if fim <= self.tamanho_maximo:
                    dados_cronologicos = self._dados[inicio:fim, :]
                else:
                    dados_cronologicos = np.concatenate([
                        self._dados[inicio:, :],
                        self._dados[:fim - self.tamanho_maximo, :]
                    ])

                return {
                    coluna: dados_cronologicos[:, i].copy()
                    for i, coluna in enumerate(self.COLUNAS)
                }

    def limpar(self):
        with self._lock:
            self._index = 0
            self._count = 0

    # =========================================================================
    # MÉTODO AUXILIAR: Retorna slice correto considerando wrap-around
    # =========================================================================
    
    def _get_coluna_slice(self, coluna_idx):
        """Retorna view da coluna com TODAS as amostras em ordem cronológica (mais antigo → mais novo).
        
        Lida corretamente com wrap-around: quando buffer está cheio (_count == tamanho_maximo),
        os dados cronológicos estão em _index até fim, depois 0 até _index-1.
        """
        with self._lock:
            if self._count == 0:
                return self._dados[0:0, coluna_idx]  # array vazio
            
            if self._count < self.tamanho_maximo:
                # Buffer ainda não encheu: dados estão em 0 até _count-1 (contíguo, ordem cronológica)
                return self._dados[:self._count, coluna_idx]
            else:
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
        return self._get_coluna_slice(0)
    
    @property
    def timestamp(self):
        return self._get_coluna_slice(1)
    
    @property
    def contador(self):
        return self._get_coluna_slice(2)
    
    @property
    def ax(self):
        return self._get_coluna_slice(3)
    
    @property
    def ay(self):
        return self._get_coluna_slice(4)
    
    @property
    def az(self):
        return self._get_coluna_slice(5)
    
    @property
    def gx(self):
        return self._get_coluna_slice(6)
    
    @property
    def gy(self):
        return self._get_coluna_slice(7)
    
    @property
    def gz(self):
        return self._get_coluna_slice(8)
