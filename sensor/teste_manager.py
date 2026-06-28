import time

from manager import manager

print("Iniciando aquisição...")

manager.iniciar()

time.sleep(15)

print(f"Amostras no buffer: {len(manager.buffer.ax)}")

manager.parar()

print("Fim do teste.")