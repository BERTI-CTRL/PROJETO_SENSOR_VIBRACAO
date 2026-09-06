import unittest

from game.main import add_new_calibration_sample, combine_direction, should_start_keyboard_mode
from game.sensor_input import SensorSample


class MainLoopTests(unittest.TestCase):
    def test_keyboard_and_sensor_direction_are_clamped(self) -> None:
        self.assertEqual(combine_direction(sensor_direction=0.8, keyboard_direction=1), 1.0)
        self.assertEqual(combine_direction(sensor_direction=-0.8, keyboard_direction=-1), -1.0)
        self.assertEqual(combine_direction(sensor_direction=0.4, keyboard_direction=0), 0.4)

    def test_calibration_collects_each_sensor_sample_only_once(self) -> None:
        samples: list[float] = []
        first = SensorSample(counter=10, ax=1.0, ay=0.12, az=0.0)
        second = SensorSample(counter=11, ax=1.0, ay=0.14, az=0.0)

        counter = add_new_calibration_sample(samples, None, first)
        counter = add_new_calibration_sample(samples, counter, first)
        counter = add_new_calibration_sample(samples, counter, second)

        self.assertEqual(counter, 11)
        self.assertEqual(samples, [0.12, 0.14])

    def test_calibration_accepts_a_new_counter_after_sensor_reset(self) -> None:
        samples: list[float] = []
        reset_sample = SensorSample(counter=1, ax=1.0, ay=0.08, az=0.0)

        counter = add_new_calibration_sample(samples, 100, reset_sample)

        self.assertEqual(counter, 1)
        self.assertEqual(samples, [0.08])

    def test_missing_recent_sample_uses_keyboard_calibration_mode(self) -> None:
        self.assertTrue(should_start_keyboard_mode(None))
        self.assertFalse(should_start_keyboard_mode(SensorSample(1, 1.0, 0.0, 0.0)))
