from sqlalchemy import func, select

from app.models import Recommendation, RiskAlert, Vehicle
from app.models.schemas import DashboardSummaryOut, RecommendationOut, RiskAlertOut, VehicleOut
from app.fleet_profiles import VEHICLE_PROFILES
from app.scoring.status import HEALTH_STATUSES, HIGH_RISK_THRESHOLD, RISK_LEVELS
from app.services.queries import PRIORITY_ORDER, count_by_label

RECENT_VEHICLE_LIMIT = 8
SUMMARY_LIST_LIMIT = 5


def build_dashboard_summary(session):
    total, average_health, average_battery, average_efficiency, total_cost = session.execute(
        select(
            func.count(Vehicle.vehicle_id),
            func.avg(Vehicle.health_score),
            func.avg(Vehicle.battery_health_pct),
            func.avg(Vehicle.efficiency_score),
            func.sum(Vehicle.maintenance_cost_inr),
        )
    ).one()
    estimated_savings = (
        session.scalar(select(func.sum(Recommendation.estimated_annual_saving_inr))) or 0
    )
    high_risk_count = (
        session.scalar(
            select(func.count()).select_from(Vehicle).where(Vehicle.risk_score >= HIGH_RISK_THRESHOLD)
        )
        or 0
    )

    recent_vehicles = session.scalars(
        select(Vehicle).order_by(Vehicle.vehicle_id.desc()).limit(RECENT_VEHICLE_LIMIT)
    ).all()
    recent_recommendations = session.scalars(
        select(Recommendation)
        .order_by(PRIORITY_ORDER, Recommendation.id.desc())
        .limit(SUMMARY_LIST_LIMIT)
    ).all()
    important_alerts = session.scalars(
        select(RiskAlert).order_by(RiskAlert.risk_score.desc()).limit(SUMMARY_LIST_LIMIT)
    ).all()

    return DashboardSummaryOut(
        total_vehicles=total,
        average_health_score=round(average_health or 0, 1),
        average_battery_health_pct=round(average_battery or 0, 1),
        fleet_efficiency_score=round(average_efficiency or 0, 1),
        high_risk_vehicles=high_risk_count,
        total_maintenance_cost_inr=round(total_cost or 0, 2),
        estimated_annual_savings_inr=round(estimated_savings, 2),
        type_distribution=count_by_label(session, Vehicle.vehicle_type, tuple(VEHICLE_PROFILES)),
        health_distribution=count_by_label(session, Vehicle.health_status, HEALTH_STATUSES),
        risk_distribution=count_by_label(session, Vehicle.risk_level, RISK_LEVELS),
        recent_vehicles=[VehicleOut.model_validate(item) for item in recent_vehicles],
        recent_recommendations=[RecommendationOut.model_validate(item) for item in recent_recommendations],
        important_alerts=[RiskAlertOut.model_validate(item) for item in important_alerts],
    )
