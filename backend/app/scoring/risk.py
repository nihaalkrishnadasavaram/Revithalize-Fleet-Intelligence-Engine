from app.config import REFERENCE_DATE
from app.scoring.metrics import (
    BATTERY_DEGRADATION_LIMIT_PCT,
    WORST_BREAKDOWNS_PER_YEAR,
    battery_degradation_pct,
    breakdowns_per_year,
    clamp_score,
    condition_score,
    maintenance_status_risk,
    weakest_system_health,
    weighted_score,
)

RISK_WEIGHTS = {
    "breakdowns": 0.25,
    "maintenance": 0.20,
    "battery": 0.25,
    "accidents": 0.15,
    "condition": 0.15,
}


def risk_components(vehicle, reference_date=REFERENCE_DATE):
    condition_risk = 100 - condition_score(vehicle)
    system_risk = 100 - weakest_system_health(vehicle)
    return {
        "breakdowns": clamp_score(
            100 * breakdowns_per_year(vehicle, reference_date) / WORST_BREAKDOWNS_PER_YEAR
        ),
        "maintenance": maintenance_status_risk(vehicle),
        "battery": clamp_score(100 * battery_degradation_pct(vehicle) / BATTERY_DEGRADATION_LIMIT_PCT),
        "accidents": clamp_score(25 * vehicle["accidents"]),
        "condition": clamp_score(max(condition_risk, system_risk)),
    }


def calculate_risk_score(vehicle, reference_date=REFERENCE_DATE):
    return weighted_score(risk_components(vehicle, reference_date), RISK_WEIGHTS)
