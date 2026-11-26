from sqlalchemy import select

from app.models import MaintenanceRecord, Recommendation, RiskAlert, Trip, Vehicle
from app.models.schemas import (
    MaintenanceRecordOut,
    RecommendationOut,
    RiskAlertOut,
    ScoreBreakdownOut,
    TripOut,
    VehicleDetailOut,
    VehicleOut,
)
from app.scoring import score_breakdown
from app.scoring.metrics import retrofit_age_years, vehicle_age
from app.services.queries import PRIORITY_ORDER


def vehicle_to_record(vehicle):
    return {column.name: getattr(vehicle, column.name) for column in Vehicle.__table__.columns}


def build_vehicle_detail(session, vehicle):
    vehicle_id = vehicle.vehicle_id
    record = vehicle_to_record(vehicle)

    maintenance_records = session.scalars(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(MaintenanceRecord.service_date.desc())
    ).all()
    trips = session.scalars(
        select(Trip).where(Trip.vehicle_id == vehicle_id).order_by(Trip.trip_month)
    ).all()
    recommendations = session.scalars(
        select(Recommendation)
        .where(Recommendation.vehicle_id == vehicle_id)
        .order_by(PRIORITY_ORDER, Recommendation.id)
    ).all()
    risk_alerts = session.scalars(
        select(RiskAlert).where(RiskAlert.vehicle_id == vehicle_id).order_by(RiskAlert.id)
    ).all()

    return VehicleDetailOut(
        **VehicleOut.model_validate(vehicle).model_dump(),
        age_years=vehicle_age(record),
        retrofit_age_years=round(retrofit_age_years(record), 1),
        score_breakdown=ScoreBreakdownOut(**score_breakdown(record)),
        maintenance_records=[MaintenanceRecordOut.model_validate(item) for item in maintenance_records],
        trips=[TripOut.model_validate(item) for item in trips],
        recommendations=[RecommendationOut.model_validate(item) for item in recommendations],
        risk_alerts=[RiskAlertOut.model_validate(item) for item in risk_alerts],
    )
