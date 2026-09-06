import unittest

from game.controller import TiltController


class TiltControllerTests(unittest.TestCase):
    def test_calibration_uses_average_of_collected_samples(self) -> None:
        controller = TiltController(dead_zone_g=0.04, full_tilt_g=0.30, smoothing=1.0)

        self.assertAlmostEqual(controller.calibrate([0.10, 0.12, 0.11]), 0.11)

    def test_dead_zone_prevents_resting_noise_from_moving_ship(self) -> None:
        controller = TiltController(dead_zone_g=0.04, full_tilt_g=0.30, smoothing=1.0)
        controller.calibrate([0.0])

        self.assertEqual(controller.update(0.03), 0.0)

    def test_full_tilt_is_clamped_and_can_be_inverted(self) -> None:
        controller = TiltController(dead_zone_g=0.04, full_tilt_g=0.30, smoothing=1.0)
        controller.calibrate([0.0])

        self.assertEqual(controller.update(1.0), 1.0)
        self.assertTrue(controller.toggle_inversion())
        self.assertEqual(controller.update(1.0), -1.0)
