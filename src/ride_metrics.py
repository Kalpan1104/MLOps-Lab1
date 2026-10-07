"""
Ride analytics functions for the fake bike-share dataset.

Pure standard library on purpose, so CI installs stay tiny and fast.
"""
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime

TIME_FMT = "%Y-%m-%d %H:%M:%S"
VALID_RIDER_TYPES = {"member", "casual"}
REQUIRED_FIELDS = ("ride_id", "start_time", "end_time", "start_station", "end_station")

# Pricing (fictional)
UNLOCK_FEE = 1.00
PER_MINUTE = {"classic": 0.15, "electric": 0.30}
MEMBER_DISCOUNT = 0.5          # members pay 50% of the per-minute rate
INCLUDED_MEMBER_MINUTES = 45   # members ride free for the first 45 minutes


def load_rides(path):
    """Read the CSV into a list of dicts, converting coordinates to float."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key in ("start_lat", "start_lon", "end_lat", "end_lon"):
            row[key] = float(row[key])
    return rows


def parse_time(value):
    """Parse 'YYYY-MM-DD HH:MM:SS' into a datetime. Raises ValueError if malformed."""
    return datetime.strptime(value, TIME_FMT)


def duration_minutes(start_time, end_time):
    """Minutes between two timestamps (strings or datetimes)."""
    if isinstance(start_time, str):
        start_time = parse_time(start_time)
    if isinstance(end_time, str):
        end_time = parse_time(end_time)
    return (end_time - start_time).total_seconds() / 60


def is_valid_ride(ride):
    """Valid if required fields exist, rider type is known, and end > start."""
    if any(not ride.get(field) for field in REQUIRED_FIELDS):
        return False
    if ride.get("rider_type") not in VALID_RIDER_TYPES:
        return False
    try:
        return duration_minutes(ride["start_time"], ride["end_time"]) > 0
    except ValueError:
        return False


def clean_rides(rides):
    """Split rides into (valid, rejected) lists."""
    valid, rejected = [], []
    for ride in rides:
        (valid if is_valid_ride(ride) else rejected).append(ride)
    return valid, rejected


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points on Earth, in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def average_speed_kmh(distance_km, minutes):
    """Average speed in km/h. Raises ValueError for non-positive durations."""
    if minutes <= 0:
        raise ValueError("Duration must be positive")
    return distance_km / (minutes / 60)


def estimate_fare(minutes, rider_type, bike_type):
    """
    Fictional pricing:
      casual: $1 unlock fee + per-minute rate
      member: no unlock fee, first 45 min free, then half the per-minute rate
    """
    if bike_type not in PER_MINUTE:
        raise ValueError(f"Unknown bike type: {bike_type}")
    if rider_type not in VALID_RIDER_TYPES:
        raise ValueError(f"Unknown rider type: {rider_type}")
    if minutes < 0:
        raise ValueError("Minutes cannot be negative")

    rate = PER_MINUTE[bike_type]
    if rider_type == "casual":
        return round(UNLOCK_FEE + minutes * rate, 2)
    billable = max(0, minutes - INCLUDED_MEMBER_MINUTES)
    return round(billable * rate * MEMBER_DISCOUNT, 2)


def peak_hour(rides):
    """Most common start hour (0-23). Ties go to the earlier hour. None if empty."""
    if not rides:
        return None
    counts = Counter(parse_time(r["start_time"]).hour for r in rides)
    return min(counts, key=lambda h: (-counts[h], h))


def station_summary(rides):
    """Per start station: ride count and average duration in minutes (2 dp)."""
    buckets = defaultdict(list)
    for r in rides:
        buckets[r["start_station"]].append(duration_minutes(r["start_time"], r["end_time"]))
    return {
        station: {"rides": len(d), "avg_minutes": round(sum(d) / len(d), 2)}
        for station, d in buckets.items()
    }
