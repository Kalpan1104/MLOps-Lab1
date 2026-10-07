"""
Generate a synthetic (fake) bike-share rides dataset.

Every value here is made up. Stations are placed around a fictional city
center, and a small number of rows are deliberately "dirty" so the cleaning
functions in src/ride_metrics.py have something real to do.

Usage:
    python data/generate_data.py                 # 500 rows -> data/rides.csv
    python data/generate_data.py --rows 2000 --seed 7 --out data/rides.csv
"""
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

STATIONS = {
    "Harbor Point":   (42.3550, -71.0500),
    "Library Square": (42.3601, -71.0589),
    "Riverside Park": (42.3662, -71.0621),
    "Tech Campus":    (42.3398, -71.0892),
    "Market Hall":    (42.3605, -71.0560),
    "Old Mill":       (42.3480, -71.0750),
}
RIDER_TYPES = ["member", "casual"]
BIKE_TYPES = ["classic", "electric"]
FIELDS = [
    "ride_id", "start_time", "end_time", "start_station", "end_station",
    "start_lat", "start_lon", "end_lat", "end_lon", "rider_type", "bike_type",
]
# Rush-hour heavy distribution of start hours (index = hour of day)
HOUR_WEIGHTS = [1, 1, 1, 1, 1, 2, 4, 8, 9, 5, 4, 4, 5, 4, 4, 5, 7, 9, 8, 5, 3, 2, 2, 1]


def make_ride(i, rng, base_day):
    start_station = rng.choice(list(STATIONS))
    end_station = rng.choice(list(STATIONS))
    hour = rng.choices(range(24), weights=HOUR_WEIGHTS)[0]
    start = base_day + timedelta(days=rng.randint(0, 29), hours=hour,
                                 minutes=rng.randint(0, 59))
    duration = max(2, int(rng.gauss(18, 8)))
    end = start + timedelta(minutes=duration)
    s_lat, s_lon = STATIONS[start_station]
    e_lat, e_lon = STATIONS[end_station]
    return {
        "ride_id": f"R{i:05d}",
        "start_time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end.strftime("%Y-%m-%d %H:%M:%S"),
        "start_station": start_station,
        "end_station": end_station,
        "start_lat": round(s_lat + rng.uniform(-0.0005, 0.0005), 6),
        "start_lon": round(s_lon + rng.uniform(-0.0005, 0.0005), 6),
        "end_lat": round(e_lat + rng.uniform(-0.0005, 0.0005), 6),
        "end_lon": round(e_lon + rng.uniform(-0.0005, 0.0005), 6),
        "rider_type": rng.choices(RIDER_TYPES, weights=[7, 3])[0],
        "bike_type": rng.choice(BIKE_TYPES),
    }


def inject_dirty_rows(rows, rng, frac=0.04):
    """Corrupt a few rows on purpose: missing station, end before start, bad rider type."""
    for row in rng.sample(rows, k=max(3, int(len(rows) * frac))):
        problem = rng.choice(["missing_station", "time_travel", "bad_rider"])
        if problem == "missing_station":
            row["end_station"] = ""
        elif problem == "time_travel":
            row["start_time"], row["end_time"] = row["end_time"], row["start_time"]
        else:
            row["rider_type"] = "unknown"
    return rows


def generate(rows=500, seed=42):
    rng = random.Random(seed)
    base_day = datetime(2025, 6, 1)
    data = [make_ride(i, rng, base_day) for i in range(1, rows + 1)]
    return inject_dirty_rows(data, rng)


def write_csv(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(data)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate fake bike-share rides")
    parser.add_argument("--rows", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="data/rides.csv")
    args = parser.parse_args()
    out = write_csv(generate(args.rows, args.seed), args.out)
    print(f"Wrote {args.rows} rows to {out}")
