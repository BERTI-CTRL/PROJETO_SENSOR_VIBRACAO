# Agenda a observação periódica do estado do buffer durante o teste interativo.
import time

# Importa o singleton que inicia e encerra o mesmo pipeline usado pela aplicação.
from sensor.manager import manager

# Este efeito ocorre ao importar/executar o módulo: inicia imediatamente a aquisição.
print("Iniciando aquisição...")
# Constrói fila e threads do pipeline antes de começar a exibir o estado.
manager.iniciar()

try:
    while True:
        # Só tenta acessar o último contador quando o buffer já recebeu ao menos uma amostra.
        if not manager.buffer.vazio():
            # Lê o contador mais recente do buffer circular para indicar progresso da aquisição.
            contador = manager.buffer.contador[-1]
            # Mostra contador e número de amostras preservadas uma vez por ciclo.
            print(
                f"Contador: {contador:.0f} | "
                f"Amostras: {len(manager.buffer.contador)}"
            )

        # Limita a atualização visual do terminal a aproximadamente uma vez por segundo.
        time.sleep(1)

except KeyboardInterrupt:
    # Converte Ctrl+C em caminho normal de encerramento do teste.
    print("\nEncerrando...")

finally:
    # Sempre encerra a sessão para enviar a sentinela e fechar o CSV, inclusive após Ctrl+C.
    manager.parar()
    # Confirma no terminal que o caminho de encerramento foi concluído.
    print("Fim do teste.")
