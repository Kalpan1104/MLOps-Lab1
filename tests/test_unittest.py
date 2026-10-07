"""unittest suite for src/ride_metrics.py — runs with `python -m unittest`, no extra installs."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.generate_data import generate, write_csv  # noqa: E402
from src import ride_metrics as rm  # noqa: E402


class TestDurationAndValidation(unittest.TestCase):
    def setUp(self):
        self.ride = {
            "ride_id": "R1", "start_time": "2025-06-01 08:00:00",
            "end_time": "2025-06-01 08:20:00", "start_station": "Tech Campus",
            "end_station": "Harbor Point", "rider_type": "casual", "bike_type": "electric",
        }

    def test_duration(self):
        self.assertEqual(rm.duration_minutes(self.ride["start_time"], self.ride["end_time"]), 20)

    def test_valid_ride(self):
        self.assertTrue(rm.is_valid_ride(self.ride))

    def test_invalid_variants(self):
        cases = {
            "end_station": "",
            "rider_type": "unknown",
            "end_time": "2025-06-01 07:59:00",
            "start_time": "garbage",
        }
        for field, bad in cases.items():
            with self.subTest(field=field):
                ride = dict(self.ride, **{field: bad})
                self.assertFalse(rm.is_valid_ride(ride))


class TestGeoAndSpeed(unittest.TestCase):
    def test_zero_distance(self):
        self.assertEqual(rm.haversine_km(42.0, -71.0, 42.0, -71.0), 0)

    def test_distance_is_symmetric(self):
        a = rm.haversine_km(42.355, -71.050, 42.340, -71.089)
        b = rm.haversine_km(42.340, -71.089, 42.355, -71.050)
        self.assertAlmostEqual(a, b, places=9)

    def test_speed(self):
        self.assertAlmostEqual(rm.average_speed_kmh(6, 20), 18.0)

    def test_speed_zero_minutes_raises(self):
        with self.assertRaises(ValueError):
            rm.average_speed_kmh(1, 0)


class TestFares(unittest.TestCase):
    def test_casual_classic(self):
        self.assertEqual(rm.estimate_fare(20, "casual", "classic"), 4.00)

    def test_member_free_window_boundary(self):
        self.assertEqual(rm.estimate_fare(45, "member", "classic"), 0.0)

    def test_member_overage(self):
        self.assertEqual(rm.estimate_fare(55, "member", "classic"), 0.75)  # 10 * 0.15 * 0.5

    def test_unknown_bike_raises(self):
        with self.assertRaises(ValueError):
            rm.estimate_fare(10, "member", "unicycle")


class TestPipelineOnFakeData(unittest.TestCase):
    """End-to-end: generate -> write CSV -> load -> clean -> summarize."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.csv_path = write_csv(generate(rows=300, seed=3), Path(cls.tmpdir.name) / "rides.csv")
        cls.rides = rm.load_rides(cls.csv_path)
        cls.valid, cls.rejected = rm.clean_rides(cls.rides)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_row_count(self):
        self.assertEqual(len(self.rides), 300)

    def test_coordinates_are_floats(self):
        self.assertIsInstance(self.rides[0]["start_lat"], float)

    def test_dirty_rows_caught(self):
        self.assertGreater(len(self.rejected), 0)
        self.assertEqual(len(self.valid) + len(self.rejected), 300)

    def test_peak_hour_in_range(self):
        self.assertIn(rm.peak_hour(self.valid), range(24))

    def test_summary_counts_match(self):
        summary = rm.station_summary(self.valid)
        self.assertEqual(sum(s["rides"] for s in summary.values()), len(self.valid))
        for stats in summary.values():
            self.assertGreater(stats["avg_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
