"""pytest suite for src/ride_metrics.py — uses fixtures, parametrize, and tmp_path."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.generate_data import generate, write_csv  # noqa: E402
from src import ride_metrics as rm  # noqa: E402


# ---------- fixtures ----------
@pytest.fixture
def good_ride():
    return {
        "ride_id": "R1", "start_time": "2025-06-01 08:00:00", "end_time": "2025-06-01 08:20:00",
        "start_station": "Old Mill", "end_station": "Market Hall",
        "rider_type": "member", "bike_type": "classic",
    }


@pytest.fixture(scope="module")
def fake_csv(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "rides.csv"
    return write_csv(generate(rows=200, seed=1), path)


# ---------- duration ----------
def test_duration_minutes_from_strings():
    assert rm.duration_minutes("2025-06-01 08:00:00", "2025-06-01 08:45:30") == 45.5


def test_parse_time_rejects_bad_format():
    with pytest.raises(ValueError):
        rm.parse_time("06/01/2025 8am")


# ---------- validation / cleaning ----------
def test_valid_ride_passes(good_ride):
    assert rm.is_valid_ride(good_ride)


@pytest.mark.parametrize("field, bad_value", [
    ("end_station", ""),                         # missing station
    ("rider_type", "unknown"),                   # bad category
    ("end_time", "2025-06-01 07:00:00"),         # ends before it starts
    ("start_time", "not-a-time"),                # unparseable
])
def test_invalid_rides_are_rejected(good_ride, field, bad_value):
    good_ride[field] = bad_value
    assert not rm.is_valid_ride(good_ride)


def test_clean_rides_splits_everything(fake_csv):
    rides = rm.load_rides(fake_csv)
    valid, rejected = rm.clean_rides(rides)
    assert len(valid) + len(rejected) == len(rides)
    assert len(rejected) > 0, "generator injects dirty rows, so some must be rejected"
    assert all(rm.is_valid_ride(r) for r in valid)


# ---------- geo + speed ----------
def test_haversine_same_point_is_zero():
    assert rm.haversine_km(42.36, -71.06, 42.36, -71.06) == 0


def test_haversine_known_distance():
    # One degree of latitude is roughly 111.2 km
    assert rm.haversine_km(0, 0, 1, 0) == pytest.approx(111.19, abs=0.1)


def test_average_speed():
    assert rm.average_speed_kmh(5, 30) == pytest.approx(10.0)


@pytest.mark.parametrize("minutes", [0, -5])
def test_average_speed_rejects_non_positive(minutes):
    with pytest.raises(ValueError):
        rm.average_speed_kmh(3, minutes)


# ---------- fares ----------
@pytest.mark.parametrize("minutes, rider, bike, expected", [
    (10, "casual", "classic", 2.50),   # 1 + 10*0.15
    (10, "casual", "electric", 4.00),  # 1 + 10*0.30
    (30, "member", "classic", 0.00),   # inside 45 free minutes
    (65, "member", "electric", 3.00),  # 20 billable * 0.30 * 0.5
])
def test_estimate_fare(minutes, rider, bike, expected):
    assert rm.estimate_fare(minutes, rider, bike) == expected


@pytest.mark.parametrize("args", [
    (10, "casual", "scooter"),
    (10, "tourist", "classic"),
    (-1, "casual", "classic"),
])
def test_estimate_fare_bad_inputs(args):
    with pytest.raises(ValueError):
        rm.estimate_fare(*args)


# ---------- aggregates ----------
def test_peak_hour_tie_goes_to_earlier_hour():
    rides = [{"start_time": "2025-06-01 17:00:00"}, {"start_time": "2025-06-01 08:00:00"}]
    assert rm.peak_hour(rides) == 8


def test_peak_hour_empty():
    assert rm.peak_hour([]) is None


def test_station_summary(good_ride):
    second = dict(good_ride, end_time="2025-06-01 08:40:00")
    summary = rm.station_summary([good_ride, second])
    assert summary == {"Old Mill": {"rides": 2, "avg_minutes": 30.0}}


def test_generator_is_reproducible():
    assert generate(rows=50, seed=9) == generate(rows=50, seed=9)
