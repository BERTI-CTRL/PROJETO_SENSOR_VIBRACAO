import time

from sensor.manager import manager

print("Iniciando aquisição...")
manager.iniciar()

try:
    while True:
        if not manager.buffer.vazio():
            contador = manager.buffer.contador[-1]
            print(
                f"Contador: {contador:.0f} | "
                f"Amostras: {len(manager.buffer.contador)}"
            )

        time.sleep(1)

except KeyboardInterrupt:
    print("\nEncerrando...")

finally:
    manager.parar()
    print("Fim do teste.")