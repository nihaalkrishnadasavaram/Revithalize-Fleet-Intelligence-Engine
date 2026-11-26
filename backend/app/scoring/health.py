from app.config import REFERENCE_DATE
from app.scoring.metrics import (
    MAX_RETROFIT_YEARS,
    MAX_VEHICLE_AGE_YEARS,
    WORST_BREAKDOWNS_PER_YEAR,
    breakdowns_per_year,
    clamp_score,
    condition_score,
    maintenance_cost_ratio,
    retrofit_age_years,
    vehicle_age,
    weighted_score,
)

HEALTH_WEIGHTS = {
    "battery": 0.25,
    "motor": 0.10,
    "electrical": 0.10,
    "age": 0.10,
    "maintenance": 0.15,
    "breakdowns": 0.20,
    "condition": 0.10,
}


def health_components(vehicle, reference_date=REFERENCE_DATE):
    age_share = vehicle_age(vehicle, reference_date) / MAX_VEHICLE_AGE_YEARS
    retrofit_share = retrofit_age_years(vehicle, reference_date) / MAX_RETROFIT_YEARS
    return {
        "battery": clamp_score(vehicle["battery_health_pct"]),
        "motor": clamp_score(vehicle["motor_health_pct"]),
        "electrical": clamp_score(vehicle["electrical_health_pct"]),
        "age": clamp_score(100 * (1 - 0.5 * age_share - 0.5 * retrofit_share)),
        "maintenance": clamp_score(100 - 30 * maintenance_cost_ratio(vehicle, reference_date)),
        "breakdowns": clamp_score(
            100 * (1 - breakdowns_per_year(vehicle, reference_date) / WORST_BREAKDOWNS_PER_YEAR)
        ),
        "condition": condition_score(vehicle),
    }


def calculate_health_score(vehicle, reference_date=REFERENCE_DATE):
    return weighted_score(health_components(vehicle, reference_date), HEALTH_WEIGHTS)
