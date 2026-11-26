from app.config import REFERENCE_DATE
from app.fleet_profiles import get_profile

MAX_VEHICLE_AGE_YEARS = 20
MAX_RETROFIT_YEARS = 8
WORST_BREAKDOWNS_PER_YEAR = 1.5
BATTERY_DEGRADATION_LIMIT_PCT = 40.0

CONDITION_SCORES = {
    "Excellent": 100.0,
    "Good": 75.0,
    "Fair": 45.0,
    "Poor": 15.0,
}

MAINTENANCE_STATUS_RISK = {
    "On Schedule": 0.0,
    "Due Soon": 50.0,
    "Overdue": 100.0,
}


def clamp_score(value):
    return max(0.0, min(100.0, float(value)))


def weighted_score(components, weights):
    return round(sum(weights[name] * components[name] for name in weights), 1)


def vehicle_age(vehicle, reference_date=REFERENCE_DATE):
    return max(reference_date.year - int(vehicle["manufacturing_year"]), 0)


def retrofit_age_years(vehicle, reference_date=REFERENCE_DATE):
    return max((reference_date - vehicle["retrofit_date"]).days / 365.25, 0.0)


def service_years(vehicle, reference_date=REFERENCE_DATE):
    return max(retrofit_age_years(vehicle, reference_date), 1.0)


def breakdowns_per_year(vehicle, reference_date=REFERENCE_DATE):
    return vehicle["breakdowns"] / service_years(vehicle, reference_date)


def yearly_maintenance_cost(vehicle, reference_date=REFERENCE_DATE):
    return vehicle["maintenance_cost_inr"] / service_years(vehicle, reference_date)


def maintenance_cost_ratio(vehicle, reference_date=REFERENCE_DATE):
    profile = get_profile(vehicle["vehicle_type"])
    return yearly_maintenance_cost(vehicle, reference_date) / profile.annual_maintenance_cost_inr


def energy_ratio(vehicle):
    profile = get_profile(vehicle["vehicle_type"])
    return vehicle["energy_consumption_kwh_per_100km"] / profile.energy_kwh_per_100km


def cost_per_km(vehicle):
    return vehicle["operating_cost_inr"] / max(vehicle["monthly_distance_km"], 1.0)


def cost_per_km_ratio(vehicle):
    profile = get_profile(vehicle["vehicle_type"])
    return cost_per_km(vehicle) / profile.cost_per_km_inr


def battery_degradation_pct(vehicle):
    return max(100.0 - vehicle["battery_health_pct"], 0.0)


def weakest_system_health(vehicle):
    return min(vehicle["motor_health_pct"], vehicle["electrical_health_pct"])


def condition_score(vehicle):
    try:
        return CONDITION_SCORES[vehicle["vehicle_condition"]]
    except KeyError:
        raise ValueError(f"Unknown vehicle condition: {vehicle['vehicle_condition']}") from None


def maintenance_status_risk(vehicle):
    try:
        return MAINTENANCE_STATUS_RISK[vehicle["maintenance_status"]]
    except KeyError:
        raise ValueError(f"Unknown maintenance status: {vehicle['maintenance_status']}") from None
