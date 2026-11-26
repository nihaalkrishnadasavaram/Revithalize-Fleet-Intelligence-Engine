from app.config import REFERENCE_DATE
from app.scoring.efficiency import calculate_efficiency_score, efficiency_components
from app.scoring.health import calculate_health_score, health_components
from app.scoring.risk import calculate_risk_score, risk_components
from app.scoring.status import health_status, operational_status, risk_level


def score_vehicle(vehicle, reference_date=REFERENCE_DATE):
    health = calculate_health_score(vehicle, reference_date)
    efficiency = calculate_efficiency_score(vehicle)
    risk = calculate_risk_score(vehicle, reference_date)
    return {
        "health_score": health,
        "efficiency_score": efficiency,
        "risk_score": risk,
        "health_status": health_status(health),
        "risk_level": risk_level(risk),
        "status": operational_status(health, risk, vehicle["maintenance_status"]),
    }


def score_fleet(vehicles, reference_date=REFERENCE_DATE):
    return [{**vehicle, **score_vehicle(vehicle, reference_date)} for vehicle in vehicles]


def score_breakdown(vehicle, reference_date=REFERENCE_DATE):
    return {
        "health": {k: round(v, 1) for k, v in health_components(vehicle, reference_date).items()},
        "efficiency": {k: round(v, 1) for k, v in efficiency_components(vehicle).items()},
        "risk": {k: round(v, 1) for k, v in risk_components(vehicle, reference_date).items()},
    }
