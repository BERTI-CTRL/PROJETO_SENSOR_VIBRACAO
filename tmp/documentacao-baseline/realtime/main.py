import sys

from PyQt6.QtWidgets import QApplication

from realtime.janela import Janela


def main():

    app = QApplication(sys.argv)

    janela = Janela()
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()