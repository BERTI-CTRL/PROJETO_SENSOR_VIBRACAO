# realtime/main.py

**Responsabilidade:** Entry point da aplicação PyQt6 - inicializa QApplication e exibe a janela principal.  
**Tipo:** Script executável (`python -m realtime.main`)  
**Thread:** Main thread (GUI)

---

## Código Completo

```python
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
```

---

## Fluxo de Execução

```
python -m realtime.main
       │
       ▼
┌─────────────────────┐
│ QApplication(sys.argv)  │  ──▶ Inicializa Qt (event loop, recursos)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Janela()            │  ──▶ Constrói UI completa:
│                     │      - Gráfico (PlotWidget)
│                     │      - Painel sinais (checkboxes)
│                     │      - Painel estatísticas (QLabels)
│                     │      - Botões (Iniciar/Parar/Limpar/Auto)
│                     │      - Timer (200ms + 500ms)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ janela.show()       │  ──▶ Exibe janela, processa eventos de pintura
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ sys.exit(app.exec())│  ──▶ Loop principal Qt (bloqueante)
│                     │      Processa: input, timers, paint, sinais
└─────────────────────┘
```

---

## Pontos-Chave

| Aspecto | Detalhe |
|---------|---------|
| `QApplication(sys.argv)` | Obrigatório **antes** de qualquer widget Qt |
| `Janela()` | Constrói UI inteira no `__init__` (síncrono, rápido) |
| `janela.show()` | Não bloqueia; agenda paint event |
| `app.exec()` | **Bloqueante** - roda até `quit()` ou fechar janela |
| `sys.exit()` | Propaga código de saída do Qt para OS |

---

## Ciclo de Vida da Aplicação

```
Início                              Fim (usuário fecha janela)
─────                               ────────────────────────
1. QApplication()                   1. closeEvent() em Janela
2. Janela()                         2. manager.parar() → para threads
3. janela.show()                    3. app.quit() implícito
4. app.exec()  ──────────────────▶  4. sys.exit(código)
   │                                    │
   │  Loop de eventos Qt                │
   │  ├─ Timers (200ms, 500ms)         │
   │  ├─ Botões (sinais/slots)         │
   │  ├─ Paint events (gráfico)        │
   │  └─ Sinais Qt (resize, etc)       │
   ▼                                    ▼
```

---

## Tratamento de Encerramento (`Janela.closeEvent`)

```python
def closeEvent(self, event):
    self.manager.parar()    # Para aquisição + threads + flush CSV
    event.accept()          # Permite fechamento
```

**Garantias:**
- Aquisição **sempre parada** antes de fechar
- Threads `join()` com timeout → não trava encerramento
- CSV **sempre flushado** e fechado corretamente

---

## Como Executar

```bash
# Opção 1: Módulo (recomendado)
python -m realtime.main

# Opção 2: Script direto
python realtime/main.py

# Opção 3: Via entry point (se configurado em pyproject.toml)
# sensor-vibracao  # hipotético
```

---

## Dependências

- `PyQt6.QtWidgets.QApplication` - Application loop
- `realtime.janela.Janela` - UI principal
- `sys` - Argumentos + exit code

---

## Referências Cruzadas

| Arquivo | Linha | Relação |
|---------|-------|---------|
| `realtime/janela.py:56` | `class Janela(QMainWindow)` | UI implementada aqui |
| `realtime/janela.py:524` | `def closeEvent` | Encerramento limpo |
| `sensor/manager.py` | - | Pipeline backend |
| `pyproject.toml` | - | Dependências PyQt6 |