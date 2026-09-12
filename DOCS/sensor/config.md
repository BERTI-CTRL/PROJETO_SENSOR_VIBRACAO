# config.py — configuração serial central

O arquivo `sensor/config.py` define os dois valores compartilhados pelos programas Python que se conectam ao MPU6050:

```python
PORTA_SERIAL = "COM4"
BAUD_RATE = 230400
```

Para trocar de `COM4` para outra porta, edite apenas `PORTA_SERIAL`. O `sensor/serial_reader.py`, o `sensor/coletor.py` e o jogo reutilizam esses valores. `BAUD_RATE` deve permanecer igual ao valor de `Serial.begin(...)` do firmware Arduino.
