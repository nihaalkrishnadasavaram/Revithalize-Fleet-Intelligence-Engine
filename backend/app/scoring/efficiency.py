from app.fleet_profiles import get_profile
from app.scoring.metrics import clamp_score, cost_per_km_ratio, energy_ratio, weighted_score

EFFICIENCY_WEIGHTS = {
    "utilization": 0.25,
    "distance": 0.20,
    "energy": 0.30,
    "cost": 0.25,
}

BENCHMARK_SCORE = 80.0


def efficiency_components(vehicle):
    profile = get_profile(vehicle["vehicle_type"])
    expected_monthly_distance = profile.annual_km / 12
    return {
        "utilization": clamp_score(vehicle["utilization_pct"]),
        "distance": clamp_score(
            BENCHMARK_SCORE * vehicle["monthly_distance_km"] / expected_monthly_distance
        ),
        "energy": clamp_score(BENCHMARK_SCORE / energy_ratio(vehicle)),
        "cost": clamp_score(BENCHMARK_SCORE / cost_per_km_ratio(vehicle)),
    }


def calculate_efficiency_score(vehicle):
    return weighted_score(efficiency_components(vehicle), EFFICIENCY_WEIGHTS)
