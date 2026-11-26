GOOD_HEALTH_THRESHOLD = 75.0
CRITICAL_HEALTH_THRESHOLD = 50.0
MEDIUM_RISK_THRESHOLD = 40.0
HIGH_RISK_THRESHOLD = 70.0

HEALTH_STATUSES = ("Good", "Needs Attention", "Critical")
RISK_LEVELS = ("Low", "Medium", "High")
VEHICLE_STATUSES = ("Operational", "Maintenance Due", "Needs Inspection", "High Risk")


def health_status(health_score):
    if health_score >= GOOD_HEALTH_THRESHOLD:
        return "Good"
    if health_score >= CRITICAL_HEALTH_THRESHOLD:
        return "Needs Attention"
    return "Critical"


def risk_level(risk_score):
    if risk_score >= HIGH_RISK_THRESHOLD:
        return "High"
    if risk_score >= MEDIUM_RISK_THRESHOLD:
        return "Medium"
    return "Low"


def operational_status(health_score, risk_score, maintenance_status):
    if risk_score >= HIGH_RISK_THRESHOLD:
        return "High Risk"
    if health_score < CRITICAL_HEALTH_THRESHOLD:
        return "Needs Inspection"
    if maintenance_status == "Overdue":
        return "Maintenance Due"
    return "Operational"
