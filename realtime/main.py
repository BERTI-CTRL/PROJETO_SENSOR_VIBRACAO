# ``sys.argv`` repassa ao Qt as opcoes recebidas pela linha de comando e
# ``sys.exit`` devolve ao processo o codigo produzido pelo event loop.
import sys

# QApplication representa a unica aplicacao Qt deste processo.
from PyQt6.QtWidgets import QApplication

# [[janela]] concentra a composicao da UI e os controles da aquisicao.
from realtime.janela import Janela


def main():

    # Deve existir exatamente uma QApplication; ela precisa ser criada antes
    # de qualquer widget e recebe os argumentos originais do processo.
    app = QApplication(sys.argv)

    # Constroi a janela principal e a torna visivel; a aquisicao ainda depende
    # do botao Iniciar, conectado dentro de Janela.
    janela = Janela()
    janela.show()

    # Entra no loop de eventos bloqueante do Qt e propaga seu codigo de saida.
    sys.exit(app.exec())


# A guarda evita abrir a GUI apenas por importar este modulo.
if __name__ == "__main__":
    main()
