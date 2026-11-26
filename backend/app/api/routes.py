from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import DEFAULT_RECORD_COUNT, RANDOM_SEED
from app.database import get_session
from app.models import Recommendation, RiskAlert, Vehicle
from app.models.schemas import (
    DashboardSummaryOut,
    GenerationResultOut,
    HealthOut,
    RecommendationOut,
    RecommendationPage,
    RiskAlertOut,
    RiskAlertPage,
    VehicleDetailOut,
    VehicleOut,
    VehiclePage,
)
from app.services.csv_export import records_to_csv
from app.services.dashboard import build_dashboard_summary
from app.services.fleet_loader import clear_fleet_data, load_synthetic_fleet
from app.services.queries import PRIORITY_ORDER, count_rows, paginate
from app.services.vehicle_detail import build_vehicle_detail, vehicle_to_record

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthOut)
def health_check(session: Session = Depends(get_session)):
    try:
        vehicle_count = count_rows(session, Vehicle)
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="The database is not available.")
    return HealthOut(status="ok", database="connected", vehicle_count=vehicle_count)


@router.get("/dashboard/summary", response_model=DashboardSummaryOut)
def dashboard_summary(session: Session = Depends(get_session)):
    return build_dashboard_summary(session)


@router.get("/vehicles", response_model=VehiclePage)
def list_vehicles(
    search: str | None = Query(None, max_length=50),
    vehicle_type: str | None = Query(None, max_length=20),
    status_filter: str | None = Query(None, alias="status", max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    statement = select(Vehicle).order_by(Vehicle.vehicle_id)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(Vehicle.vehicle_id.ilike(pattern), Vehicle.vehicle_type.ilike(pattern))
        )
    if vehicle_type:
        statement = statement.where(Vehicle.vehicle_type == vehicle_type)
    if status_filter:
        statement = statement.where(Vehicle.status == status_filter)
    total, rows = paginate(session, statement, page, page_size)
    return VehiclePage(
        total=total,
        page=page,
        page_size=page_size,
        items=[VehicleOut.model_validate(row) for row in rows],
    )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleDetailOut)
def vehicle_detail(vehicle_id: str, session: Session = Depends(get_session)):
    vehicle = session.get(Vehicle, vehicle_id.strip().upper())
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} was not found.")
    return build_vehicle_detail(session, vehicle)


@router.get("/recommendations", response_model=RecommendationPage)
def list_recommendations(
    category: str | None = Query(None, max_length=30),
    priority: str | None = Query(None, max_length=10),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    filters = []
    if category:
        filters.append(Recommendation.category == category)
    if priority:
        filters.append(Recommendation.priority == priority)
    statement = (
        select(Recommendation).where(*filters).order_by(PRIORITY_ORDER, Recommendation.id)
    )
    total, rows = paginate(session, statement, page, page_size)
    total_saving = session.scalar(
        select(func.sum(Recommendation.estimated_annual_saving_inr)).where(*filters)
    )
    return RecommendationPage(
        total=total,
        page=page,
        page_size=page_size,
        total_estimated_annual_saving_inr=round(total_saving or 0, 2),
        items=[RecommendationOut.model_validate(row) for row in rows],
    )


@router.get("/alerts", response_model=RiskAlertPage)
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    statement = select(RiskAlert).order_by(RiskAlert.risk_score.desc(), RiskAlert.id)
    total, rows = paginate(session, statement, page, page_size)
    return RiskAlertPage(
        total=total,
        page=page,
        page_size=page_size,
        items=[RiskAlertOut.model_validate(row) for row in rows],
    )


@router.post("/data/generate", response_model=GenerationResultOut)
def generate_data(
    count: int = Query(DEFAULT_RECORD_COUNT, ge=100, le=10000),
    seed: int = Query(RANDOM_SEED),
    force: bool = Query(False),
    session: Session = Depends(get_session),
):
    existing_count = count_rows(session, Vehicle)
    if existing_count and not force:
        return GenerationResultOut(
            generated=False,
            vehicle_count=existing_count,
            message=f"The database already contains {existing_count} vehicles. Use force=true to regenerate.",
        )
    clear_fleet_data(session)
    generated_count = load_synthetic_fleet(session, count, seed)
    return GenerationResultOut(
        generated=True,
        vehicle_count=generated_count,
        message=f"Generated and stored {generated_count} synthetic vehicles.",
    )


@router.get("/data/export")
def export_dataset(session: Session = Depends(get_session)):
    vehicles = session.scalars(select(Vehicle).order_by(Vehicle.vehicle_id)).all()
    csv_text = records_to_csv([vehicle_to_record(vehicle) for vehicle in vehicles])
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="synthetic_fleet_data.csv"'},
    )
