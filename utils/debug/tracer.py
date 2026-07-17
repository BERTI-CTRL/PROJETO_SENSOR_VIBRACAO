from time import perf_counter

DEBUG = True


class Tracer:
    def __init__(self):
        self.ultimo = {}

    def marcar(self, etapa, contador):
        if not DEBUG:
            return

        agora = perf_counter()

        if etapa in self.ultimo:
            anterior = self.ultimo[etapa]

            if contador != anterior + 1:
                print(
                    f"[{etapa}] "
                    f"CONTADOR ESPERADO {anterior+1} "
                    f"RECEBIDO {contador}"
                )

        self.ultimo[etapa] = contador

        if contador % 1000 == 0:
            print(f"[{etapa}] contador={contador}")