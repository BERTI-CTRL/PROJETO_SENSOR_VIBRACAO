import unittest

from game.main import combine_direction


class MainLoopTests(unittest.TestCase):
    def test_keyboard_and_sensor_direction_are_clamped(self) -> None:
        self.assertEqual(combine_direction(sensor_direction=0.8, keyboard_direction=1), 1.0)
        self.assertEqual(combine_direction(sensor_direction=-0.8, keyboard_direction=-1), -1.0)
        self.assertEqual(combine_direction(sensor_direction=0.4, keyboard_direction=0), 0.4)
