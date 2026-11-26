import os
import sys
import tempfile
from datetime import date
from pathlib import Path

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

TEMPORARY_DIRECTORY = tempfile.mkdtemp(prefix="rfie_tests_")
os.environ.setdefault(
    "RFIE_DATABASE_URL",
    f"sqlite:///{Path(TEMPORARY_DIRECTORY, 'test.db').as_posix()}",
)
os.environ.setdefault("RFIE_DEFAULT_RECORD_COUNT", "200")

from app.scoring import score_vehicle  # noqa: E402


def sample_vehicle(**overrides):
    vehicle = {
        "vehicle_id": "VEH-TEST",
        "vehicle_type": "Scooter",
        "manufacturing_year": 2018,
        "retrofit_date": date(2023, 11, 25),
        "total_distance_km": 27000,
        "monthly_distance_km": 750,
        "battery_capacity_kwh": 2.4,
        "battery_health_pct": 88.0,
        "motor_health_pct": 90.0,
        "electrical_health_pct": 86.0,
        "energy_consumption_kwh_per_100km": 3.6,
        "charge_cycles": 405,
        "fast_charge_pct": 40.0,
        "maintenance_cost_inr": 12000.0,
        "breakdowns": 3,
        "accidents": 1,
        "utilization_pct": 60.0,
        "maintenance_status": "Due Soon",
        "vehicle_condition": "Fair",
        "operating_cost_inr": 700.0,
    }
    vehicle.update(overrides)
    return vehicle


def scored_vehicle(**overrides):
    vehicle = sample_vehicle(**overrides)
    return {**vehicle, **score_vehicle(vehicle)}


def healthy_vehicle(**overrides):
    values = {
        "vehicle_id": "VEH-GOOD",
        "manufacturing_year": 2022,
        "retrofit_date": date(2025, 11, 25),
        "total_distance_km": 9000,
        "monthly_distance_km": 750,
        "battery_capacity_kwh": 2.4,
        "battery_health_pct": 98.0,
        "motor_health_pct": 97.0,
        "electrical_health_pct": 96.0,
        "energy_consumption_kwh_per_100km": 3.2,
        "charge_cycles": 120,
        "fast_charge_pct": 20.0,
        "maintenance_cost_inr": 3000.0,
        "breakdowns": 0,
        "accidents": 0,
        "utilization_pct": 65.0,
        "maintenance_status": "On Schedule",
        "vehicle_condition": "Excellent",
        "operating_cost_inr": 620.0,
    }
    values.update(overrides)
    return scored_vehicle(**values)
