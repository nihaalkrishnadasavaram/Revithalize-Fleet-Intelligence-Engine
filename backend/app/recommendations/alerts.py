from app.config import REFERENCE_DATE
from app.scoring.metrics import breakdowns_per_year, service_years, weakest_system_health
from app.scoring.status import HIGH_RISK_THRESHOLD

BREAKDOWN_RATE_ALERT = 1.0
ACCIDENT_ALERT_COUNT = 2
BATTERY_ALERT_PCT = 75.0
SYSTEM_ALERT_PCT = 60.0


def build_risk_alert(vehicle, reference_date=REFERENCE_DATE):
    if vehicle["risk_score"] < HIGH_RISK_THRESHOLD:
        return None

    reasons = []
    actions = []

    if breakdowns_per_year(vehicle, reference_date) >= BREAKDOWN_RATE_ALERT:
        years = service_years(vehicle, reference_date)
        reasons.append(f"{vehicle['breakdowns']} breakdowns in {years:.1f} years since retrofit")
        actions.append("diagnose the recurring breakdown causes")
    if vehicle["battery_health_pct"] < BATTERY_ALERT_PCT:
        reasons.append(f"battery health is down to {vehicle['battery_health_pct']:.1f}%")
        actions.append("test the battery pack")
    if vehicle["maintenance_status"] == "Overdue":
        reasons.append("maintenance is overdue")
        actions.append("complete the overdue maintenance")
    if weakest_system_health(vehicle) < SYSTEM_ALERT_PCT:
        reasons.append("motor or electrical system health is low")
        actions.append("inspect the motor and electrical system")
    if vehicle["accidents"] >= ACCIDENT_ALERT_COUNT:
        reasons.append(f"{vehicle['accidents']} accidents on record")
        actions.append("review rider and safety records")
    if vehicle["vehicle_condition"] == "Poor":
        reasons.append("vehicle condition is poor")
        actions.append("schedule a full inspection")

    if not reasons:
        reasons.append("combined risk factors exceed the alert threshold")
        actions.append("review the vehicle assignment")

    reason_text = "; ".join(reasons)
    return {
        "vehicle_id": vehicle["vehicle_id"],
        "risk_score": vehicle["risk_score"],
        "risk_level": vehicle["risk_level"],
        "reason": reason_text[0].upper() + reason_text[1:] + ".",
        "recommended_action": "Restrict to low-risk duty, then " + ", ".join(actions) + ".",
    }
