import os
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"
DATA_DIRECTORY.mkdir(exist_ok=True)

DATABASE_URL = os.getenv(
    "RFIE_DATABASE_URL",
    f"sqlite:///{(DATA_DIRECTORY / 'rfie.db').as_posix()}",
)
CSV_EXPORT_PATH = DATA_DIRECTORY / "synthetic_fleet_data.csv"

REFERENCE_DATE = date(2026, 11, 25)

DEFAULT_RECORD_COUNT = int(os.getenv("RFIE_DEFAULT_RECORD_COUNT", "3000"))
RANDOM_SEED = 42
SCHEMA_VERSION = 2

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
