import time

from serial_reader import ler_dados
from gravador import GravadorCSV

gravador = GravadorCSV(
    arquivo="dados_vibracao.csv",
    tamanho_buffer=1000
)

try:

    for contador, ax, ay, az, gx, gy, gz in ler_dados(
        porta="COM5",
        baudrate=115200
    ):

        gravador.salvar([
            time.perf_counter(),
            contador,
            ax,
            ay,
            az,
            gx,
            gy,
            gz
        ])

except KeyboardInterrupt:

    gravador.fechar()

    print("Aquisição encerrada.")