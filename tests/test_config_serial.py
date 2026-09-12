import importlib
import inspect
import unittest
from unittest.mock import patch


class ConfiguracaoSerialTests(unittest.TestCase):
    def test_consumidores_usam_configuracao_serial_central(self):
        especificacao = importlib.util.find_spec("sensor.config")
        self.assertIsNotNone(especificacao, "sensor.config deve centralizar porta e baud rate")

        from sensor import config
        import game.config as game_config
        import sensor.coletor as coletor
        import sensor.serial_reader as serial_reader

        try:
            with (
                patch.object(config, "PORTA_SERIAL", "COM99"),
                patch.object(config, "BAUD_RATE", 57600),
            ):
                importlib.reload(serial_reader)
                importlib.reload(coletor)
                importlib.reload(game_config)

                parametros_leitor = inspect.signature(serial_reader.ler_dados).parameters
                self.assertEqual(parametros_leitor["porta"].default, "COM99")
                self.assertEqual(parametros_leitor["baudrate"].default, 57600)

                aquisicao = coletor.Coletor()
                self.assertEqual(aquisicao.porta, "COM99")
                self.assertEqual(aquisicao.baudrate, 57600)

                self.assertEqual(game_config.SERIAL_PORT, "COM99")
                self.assertEqual(game_config.SERIAL_BAUDRATE, 57600)
        finally:
            importlib.reload(serial_reader)
            importlib.reload(coletor)
            importlib.reload(game_config)


if __name__ == "__main__":
    unittest.main()
