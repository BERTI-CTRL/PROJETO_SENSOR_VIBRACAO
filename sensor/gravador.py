# gravador.py ->Só grava CSV.

import csv
from pathlib import Path

class GravadorCSV:

    def __init__(
        self,
        arquivo="dados/dados_aceleracao_giro.csv",
        tamanho_buffer=10000
    ):

        self.buffer = []
        self.tamanho_buffer = tamanho_buffer

        self.arquivo = Path(arquivo)

        arquivo_existe = self.arquivo.exists()

        self.f = open(
            self.arquivo,
            mode="a",
            newline="",
            encoding="utf-8"
        )

        self.writer = csv.writer(self.f)

        if not arquivo_existe:

            self.writer.writerow([
                "timestamp",
                "contador",
                "ax",
                "ay",
                "az",
                "gx",
                "gy",
                "gz"
            ])

    def salvar(self, linha):

        self.buffer.append(linha)

        if len(self.buffer) >= self.tamanho_buffer:

            self.writer.writerows(self.buffer)

            self.buffer.clear()

    def fechar(self):

        if self.buffer:

            self.writer.writerows(self.buffer)

            self.buffer.clear()

        self.f.close()