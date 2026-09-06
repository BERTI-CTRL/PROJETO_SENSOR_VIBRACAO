# Apesar do nome genérico herdado, este módulo é o gravador de CSV da aquisição.

# Fornece o escritor que serializa as linhas no formato CSV.
import csv
# Representa o caminho de saída de modo independente da plataforma.
from pathlib import Path
# Cria o sufixo temporal que diferencia os arquivos de cada sessão.
from datetime import datetime


class GravadorCSV:

    def __init__(
        self,
        # Parâmetro histórico: hoje não escolhe o destino, que é montado abaixo.
        arquivo="dados/dados_aceleracao_giro.csv",
        # Define quantas linhas ficam em memória antes de uma escrita em lote.
        tamanho_buffer=10000
    ):
        # Acumula linhas para reduzir a quantidade de operações de disco.
        self.buffer = []
        # Conserva o limite escolhido para a decisão de escrita em lote.
        self.tamanho_buffer = tamanho_buffer
        # Gera uma identificação temporal legível para a sessão atual.
        data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Monta o destino efetivo; o parâmetro arquivo acima permanece ignorado nesta versão.
        self.arquivo = Path(f'dados/dados_aceleracao_giro-{data_hora}.csv')

        # Descobre se este destino já existe para não repetir o cabeçalho em append.
        arquivo_existe = self.arquivo.exists()

        # Abre em append, preservando conteúdo existente e configurando CSV adequado ao Windows.
        self.f = open(
            self.arquivo,
            mode="a",
            newline="",
            encoding="utf-8"
        )

        # Cria o escritor que receberá o cabeçalho e os lotes de amostras.
        self.writer = csv.writer(self.f)

        # Um arquivo novo recebe a ordem estável das nove colunas persistidas.
        if not arquivo_existe:
            # Escreve o cabeçalho uma única vez para tornar cada coluna identificável.
            self.writer.writerow([
                "tempo_arduino_us",
                "tempo_relogio_pc",
                "contador",
                "ax",
                "ay",
                "az",
                "gx",
                "gy",
                "gz"
            ])

    def salvar(self, linha):
        # Retém a linha até formar um lote de escrita.
        self.buffer.append(linha)

        # Descarrega o lote assim que ele alcança a capacidade configurada.
        if len(self.buffer) >= self.tamanho_buffer:
            # Persiste todas as linhas pendentes em uma única operação CSV.
            self.writer.writerows(self.buffer)

            # Libera as referências do lote já persistido para reutilizar a lista.
            self.buffer.clear()

    def fechar(self):
        # Garante que o lote incompleto também seja persistido no encerramento normal.
        if self.buffer:
            # Escreve as últimas linhas que não atingiram tamanho_buffer.
            self.writer.writerows(self.buffer)

            # Esvazia o buffer após a persistência final.
            self.buffer.clear()

        # Fecha o descritor do arquivo depois do flush final do buffer da aplicação.
        self.f.close()
