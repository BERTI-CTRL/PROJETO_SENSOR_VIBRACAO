import unittest

from game.sensor_input import SensorReader, SensorSample, parse_sensor_line


class SensorInputTests(unittest.TestCase):
    def test_parser_reads_the_current_arduino_protocol(self) -> None:
        sample = parse_sensor_line("42,123456,1.00,-0.15,0.02,0.0,0.0,0.0")

        self.assertEqual(sample, SensorSample(counter=42, ax=1.0, ay=-0.15, az=0.02))

    def test_parser_discards_boot_messages_and_incomplete_rows(self) -> None:
        self.assertIsNone(parse_sensor_line("Erro MPU"))
        self.assertIsNone(parse_sensor_line("1,2,3"))

    def test_latest_sample_expires_when_serial_stops_sending(self) -> None:
        now = [10.0]
        reader = SensorReader(
            "COM404",
            115200,
            stale_after_s=0.5,
            clock=lambda: now[0],
        )
        with reader._lock:
            reader._latest = SensorSample(counter=1, ax=1.0, ay=0.2, az=0.0)
            reader._latest_at = now[0]

        now[0] = 10.51

        self.assertIsNone(reader.latest_sample())
