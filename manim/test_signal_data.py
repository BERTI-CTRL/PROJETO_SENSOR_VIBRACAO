"""Testes dos dados científicos; não requer renderização nem hardware."""

import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from signal_data import illustrative_response, load_signal


class SignalDataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "ensaio.csv"

    def write_rows(self, rows):
        with self.path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["tempo_arduino_us", "tempo_relogio_pc", "contador",
                             "ax", "ay", "az", "gx", "gy", "gz"])
            for number, (timestamp, value) in enumerate(rows):
                writer.writerow([timestamp, number * 0.1, number, 1, -2, value, 0, 0, 0])

    def test_crop_uses_arduino_time_and_preserves_raw_g(self):
        # Catches use of PC time, conversion to SI, baseline removal or resampling.
        self.write_rows([(10_000_000, 99), (10_100_000, 3),
                         (10_300_000, -4), (10_500_000, 8)])
        result = load_signal(self.path, start=0.1, duration=0.2)
        np.testing.assert_allclose(result.t, [0, 0.2])
        np.testing.assert_array_equal(result.values, [3, -4])
        self.assertAlmostEqual(result.start_seconds, 0.1)
        self.assertAlmostEqual(result.rms, np.sqrt(12.5))
        self.assertAlmostEqual(result.mean, -0.5)
        self.assertAlmostEqual(result.std, 3.5)
        self.assertEqual(result.sample_count, 2)
        self.assertEqual(result.axis, "az")
        self.assertEqual(result.source, self.path)
        self.assertFalse(result.synthetic)

    def test_axis_selection_and_actual_first_sample_time(self):
        self.write_rows([(1_000_000, 3), (1_120_000, 4), (1_250_000, 5)])
        result = load_signal(self.path, axis="ay", start=0.1, duration=0.2)
        np.testing.assert_array_equal(result.values, [-2, -2])
        np.testing.assert_allclose(result.t, [0, 0.13])
        self.assertAlmostEqual(result.start_seconds, 0.12)

    def test_explicit_missing_path_never_becomes_synthetic(self):
        with self.assertRaises(FileNotFoundError):
            load_signal(self.path)

    def test_default_missing_source_is_explicitly_synthetic_and_deterministic(self):
        with patch("signal_data.DEFAULT_CSV", self.path):
            first = load_signal(start=8, duration=2)
            second = load_signal(start=8, duration=2)
        self.assertTrue(first.synthetic)
        self.assertIsNone(first.source)
        self.assertIn("sint", first.source_label.lower())
        self.assertGreater(first.sample_count, 100)
        self.assertAlmostEqual(first.t[0], 0)
        self.assertAlmostEqual(first.t[-1], 2)
        np.testing.assert_array_equal(first.values, second.values)

    def test_invalid_default_file_is_not_silently_replaced(self):
        self.write_rows([(0, 1), (0, 2)])
        with patch("signal_data.DEFAULT_CSV", self.path):
            with self.assertRaises(ValueError):
                load_signal(start=0, duration=1)

    def test_rejects_bad_axis_and_crop_arguments(self):
        for kwargs in ({"axis": "gx"}, {"start": -1}, {"duration": 0},
                       {"duration": float("nan")}, {"start": float("inf")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                load_signal(self.path, **kwargs)

    def test_rejects_nonfinite_nonmonotonic_and_too_short_data(self):
        examples = [[], [(0, 1)], [(0, 1), (0, 2)], [(2, 1), (1, 2)],
                    [(0, 1), (1, float("nan"))], [(0, 1), (float("inf"), 2)]]
        for rows in examples:
            self.write_rows(rows)
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                load_signal(self.path, start=0, duration=1)

    def test_rejects_a_crop_without_two_samples(self):
        self.write_rows([(0, 1), (1_000_000, 2), (2_000_000, 3)])
        with self.assertRaises(ValueError):
            load_signal(self.path, start=1, duration=0.1)

    def test_rejects_missing_required_columns(self):
        self.path.write_text("time,az\n0,1\n1,2\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_signal(self.path, start=0, duration=1)

    def test_real_default_capture_keeps_every_sample_in_the_crop(self):
        result = load_signal()
        self.assertFalse(result.synthetic)
        self.assertGreater(result.sample_count, 2100)
        self.assertLess(result.sample_count, 2300)
        self.assertEqual(float(result.values.max()), 0.57)
        self.assertEqual(float(result.values.min()), -0.48)
        self.assertTrue(np.all(np.diff(result.t) > 0))


class IllustrativeResponseTests(unittest.TestCase):
    def test_response_derivatives_and_free_motion_satisfy_newton_equation(self):
        # Finite differences independently detect sign and scale errors in v/a.
        t = np.linspace(0.01, 3, 800)
        step = 1e-5
        params = dict(mass=2, damping=1.2, stiffness=18, amplitude=0.03)
        x, velocity, acceleration = illustrative_response(t, **params)
        x_before, v_before, _ = illustrative_response(t - step, **params)
        x_after, v_after, _ = illustrative_response(t + step, **params)
        np.testing.assert_allclose((x_after - x_before) / (2 * step), velocity,
                                   rtol=1e-6, atol=1e-9)
        np.testing.assert_allclose((v_after - v_before) / (2 * step), acceleration,
                                   rtol=1e-6, atol=1e-9)
        np.testing.assert_allclose(2 * acceleration + 1.2 * velocity + 18 * x,
                                   0, atol=1e-14)

    def test_initial_conditions_are_explicit_and_in_si(self):
        x, velocity, acceleration = illustrative_response(np.array([0.0]))
        self.assertAlmostEqual(x[0], 0.018)
        self.assertAlmostEqual(velocity[0], -0.0063)
        self.assertAlmostEqual(acceleration[0], -0.28359)

    def test_rejects_nonphysical_or_unsupported_model_parameters(self):
        for kwargs in ({"mass": 0}, {"stiffness": 0}, {"damping": -1},
                       {"damping": 8}, {"damping": 9},
                       {"amplitude": float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                illustrative_response(np.array([0, 1]), **kwargs)


if __name__ == "__main__":
    unittest.main()
