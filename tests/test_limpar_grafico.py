import sys
import types
import unittest


def instalar_stubs_graficos():
    serial = types.ModuleType("serial")
    serial.Serial = type("Serial", (), {})
    sys.modules.setdefault("serial", serial)

    pyqtgraph = types.ModuleType("pyqtgraph")
    pyqtgraph.setConfigOptions = lambda **_: None
    sys.modules.setdefault("pyqtgraph", pyqtgraph)

    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.QTimer = type("QTimer", (), {})
    qtcore.Qt = type("Qt", (), {})

    qtwidgets = types.ModuleType("PyQt6.QtWidgets")
    for nome in (
        "QCheckBox",
        "QGridLayout",
        "QGroupBox",
        "QHBoxLayout",
        "QLabel",
        "QMainWindow",
        "QPushButton",
        "QVBoxLayout",
        "QWidget",
    ):
        setattr(qtwidgets, nome, type(nome, (), {}))

    pyqt6 = types.ModuleType("PyQt6")
    sys.modules.setdefault("PyQt6", pyqt6)
    sys.modules.setdefault("PyQt6.QtCore", qtcore)
    sys.modules.setdefault("PyQt6.QtWidgets", qtwidgets)


instalar_stubs_graficos()

from realtime.janela import Janela


class CurvaDeTeste:
    def __init__(self):
        self.foi_limpa = False

    def clear(self):
        self.foi_limpa = True


class BufferDeTeste:
    def __init__(self):
        self.foi_limpo = False

    def limpar(self):
        self.foi_limpo = True


class ManagerDeTeste:
    def __init__(self):
        self.buffer = BufferDeTeste()


class LimparGraficoTests(unittest.TestCase):
    def test_limpar_grafico_esvazia_buffer_e_limpa_todas_as_curvas(self):
        janela = Janela.__new__(Janela)
        janela.manager = ManagerDeTeste()
        curvas = [CurvaDeTeste() for _ in range(6)]
        (
            janela.curva_ax,
            janela.curva_ay,
            janela.curva_az,
            janela.curva_gx,
            janela.curva_gy,
            janela.curva_gz,
        ) = curvas

        janela.limpar_grafico()

        self.assertTrue(janela.manager.buffer.foi_limpo)
        self.assertTrue(all(curva.foi_limpa for curva in curvas))


if __name__ == "__main__":
    unittest.main()
