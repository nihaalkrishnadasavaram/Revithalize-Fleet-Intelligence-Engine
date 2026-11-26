from app.config import REFERENCE_DATE
from app.recommendations.alerts import build_risk_alert
from app.recommendations.rules import (
    cost_reduction_rules,
    maintenance_rules,
    risk_management_rules,
    utilization_rules,
)

PRIORITY_RANK = {"High": 3, "Medium": 2, "Low": 1}

CATEGORY_RULES = (
    cost_reduction_rules,
    maintenance_rules,
    utilization_rules,
    risk_management_rules,
)


def generate_recommendations(vehicle, reference_date=REFERENCE_DATE):
    recommendations = []
    for apply_rules in CATEGORY_RULES:
        matches = apply_rules(vehicle, reference_date)
        if matches:
            best_match = max(matches, key=lambda match: PRIORITY_RANK[match["priority"]])
            recommendations.append({"vehicle_id": vehicle["vehicle_id"], **best_match})
    return recommendations


def analyse_fleet(vehicles, reference_date=REFERENCE_DATE):
    recommendations = []
    alerts = []
    for vehicle in vehicles:
        recommendations.extend(generate_recommendations(vehicle, reference_date))
        alert = build_risk_alert(vehicle, reference_date)
        if alert is not None:
            alerts.append(alert)
    return recommendations, alerts
