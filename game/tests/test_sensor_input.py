import unittest

from game.sensor_input import SensorSample, parse_sensor_line


class SensorInputTests(unittest.TestCase):
    def test_parser_reads_the_current_arduino_protocol(self) -> None:
        sample = parse_sensor_line("42,123456,1.00,-0.15,0.02,0.0,0.0,0.0")

        self.assertEqual(sample, SensorSample(counter=42, ax=1.0, ay=-0.15, az=0.02))

    def test_parser_discards_boot_messages_and_incomplete_rows(self) -> None:
        self.assertIsNone(parse_sensor_line("Erro MPU"))
        self.assertIsNone(parse_sensor_line("1,2,3"))
