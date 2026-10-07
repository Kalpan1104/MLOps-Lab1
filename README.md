# Ride Analytics CI — GitHub Actions Lab

A hands-on lab for learning GitHub Actions by testing a small data-science module two ways: **pytest** and **unittest**. Instead of a calculator, this repo works on a **fake bike-share rides dataset**: it generates the data, cleans out bad rows, computes distances, speeds and fares, and summarizes rides per station. Three workflows run the tests and a scheduled data-quality report.

## Project structure

```
ride-analytics-ci/
├── .github/workflows/
│   ├── pytest_action.yml      # pytest on Python 3.10–3.12 + coverage + artifacts
│   ├── unittest_action.yml    # built-in unittest, zero installs
│   └── data_quality.yml       # nightly (cron) data-quality report
├── data/
│   ├── __init__.py
│   ├── generate_data.py       # fake dataset generator (seeded, reproducible)
│   └── rides.csv              # 500 sample rows (≈4% deliberately dirty)
├── src/
│   ├── __init__.py
│   └── ride_metrics.py        # functions under test
├── tests/
│   ├── __init__.py
│   ├── test_pytest.py         # fixtures, parametrize, tmp_path
│   └── test_unittest.py       # TestCase classes, subTest, setUpClass
├── pytest.ini
├── requirements.txt
└── .gitignore
```

## The fake dataset

`data/generate_data.py` builds rides between six made-up stations with rush-hour-heavy start times. Each row has: `ride_id, start_time, end_time, start_station, end_station, start_lat, start_lon, end_lat, end_lon, rider_type, bike_type`.

About 4% of rows are corrupted on purpose (missing end station, end time before start time, or `rider_type = unknown`) so the cleaning function has real work to do.

```bash
python data/generate_data.py                          # default: 500 rows, seed 42
python data/generate_data.py --rows 2000 --seed 7     # custom
```

## Functions under test (`src/ride_metrics.py`)

| Function | What it does |
|---|---|
| `load_rides(path)` | Reads the CSV, casts coordinates to float |
| `parse_time(value)` | Parses `YYYY-MM-DD HH:MM:SS` |
| `duration_minutes(start, end)` | Ride length in minutes |
| `is_valid_ride(ride)` / `clean_rides(rides)` | Validation and valid/rejected split |
| `haversine_km(...)` | Great-circle distance between two coordinates |
| `average_speed_kmh(km, minutes)` | Speed, errors on non-positive time |
| `estimate_fare(minutes, rider, bike)` | Fictional pricing (casual vs. member, classic vs. electric) |
| `peak_hour(rides)` | Busiest start hour |
| `station_summary(rides)` | Ride count and average duration per station |

---

## Step-by-step lab

### Step 1 — Create the repository
1. On GitHub, click **New repository**, name it `ride-analytics-ci`, keep it public, and do not add a README (you already have one).
2. Locally:
   ```bash
   unzip ride-analytics-ci.zip && cd ride-analytics-ci
   git init
   git branch -M main
   ```

### Step 2 — Set up a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Generate the fake data
```bash
python data/generate_data.py
```

### Step 4 — Run the tests locally (always do this before pushing)
```bash
pytest                                       # pytest suite
pytest --cov=src --cov-report=term-missing   # with coverage
python -m unittest tests.test_unittest -v    # unittest suite
```
All tests should pass: 16 unittest cases and roughly 28 pytest cases (parametrized cases count separately).

### Step 5 — Understand the workflows
Every workflow lives in `.github/workflows/`. Each file has three key parts: **`on`** (what triggers it), **`jobs`** (what machine runs it), and **`steps`** (what commands run, in order).

- **`pytest_action.yml`** runs on every push and pull request to `main`. It uses a **matrix** to test on Python 3.10, 3.11 and 3.12 in parallel, caches pip downloads, regenerates the dataset, runs pytest with coverage, and uploads JUnit XML + `coverage.xml` as artifacts (even if tests fail, thanks to `if: always()`).
- **`unittest_action.yml`** runs on the same triggers but needs no `pip install`, because `unittest` ships with Python. It writes a short message to the job summary page.
- **`data_quality.yml`** runs on a **cron schedule** (daily, 12:00 UTC) or manually. It generates a new batch, writes a Markdown report (row counts, reject rate, per-station table) to the run's summary page, uploads the batch as an artifact, and **fails the run if more than 10% of rows are rejected**. This is a data-quality gate, not just a code test.

All three include `workflow_dispatch`, so you can trigger them by hand from the **Actions** tab.

### Step 6 — Push to GitHub
```bash
git add .
git commit -m "Initial commit: ride analytics + CI workflows"
git remote add origin https://github.com/<your-username>/ride-analytics-ci.git
git push -u origin main
```

### Step 7 — Watch the workflows run
1. Open your repo → **Actions** tab.
2. You'll see **Pytest CI** (3 matrix jobs) and **Unittest CI** start automatically.
3. Click into a run to see each step's logs. Download the test report from the **Artifacts** section at the bottom of the run page.
4. To try the nightly job now: **Actions → Nightly Data Quality Report → Run workflow**. The report appears on the run's summary page.

### Step 8 — Break something on purpose
This is the best way to see CI doing its job.
```bash
git checkout -b break-fares
```
In `src/ride_metrics.py`, change `UNLOCK_FEE = 1.00` to `UNLOCK_FEE = 1.50`, then:
```bash
git commit -am "Raise unlock fee"
git push -u origin break-fares
```
Open a **pull request** into `main`. Both workflows run on the PR and the fare tests go red. Revert the change, push again, and watch them turn green.

### Step 9 — Protect `main` (optional but recommended)
**Settings → Branches → Add branch ruleset** (or *branch protection rule*) for `main`, enable **Require status checks to pass**, and select the `pytest` and `unittest` jobs. Now nobody can merge a PR that breaks the tests.

### Step 10 — Add a status badge
Add these to the top of this README (replace `<your-username>`):
```markdown
![Pytest CI](https://github.com/<your-username>/ride-analytics-ci/actions/workflows/pytest_action.yml/badge.svg)
![Unittest CI](https://github.com/<your-username>/ride-analytics-ci/actions/workflows/unittest_action.yml/badge.svg)
```

---

## pytest vs. unittest in this repo

| | `test_pytest.py` | `test_unittest.py` |
|---|---|---|
| Style | Plain functions + `assert` | `unittest.TestCase` classes |
| Shared setup | `@pytest.fixture` (function and module scope) | `setUp` / `setUpClass` / `tearDownClass` |
| Many inputs | `@pytest.mark.parametrize` | `self.subTest(...)` |
| Exceptions | `pytest.raises(ValueError)` | `self.assertRaises(ValueError)` |
| Floats | `pytest.approx` | `assertAlmostEqual` |
| Temp files | `tmp_path_factory` | `tempfile.TemporaryDirectory` |
| Install | `pip install pytest` | Built in |

## Ideas to extend it
- Add a `lint` job with `ruff` or `flake8` and make the test jobs depend on it with `needs: lint`.
- Add a test that fails when coverage drops below a threshold (`--cov-fail-under=90`).
- Train a small model (e.g. predict ride duration) and add a workflow that fails if accuracy regresses.
