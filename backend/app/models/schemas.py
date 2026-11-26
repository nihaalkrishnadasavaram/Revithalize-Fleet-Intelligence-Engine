from datetime import date

from pydantic import BaseModel, ConfigDict


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class VehicleOut(OrmModel):
    vehicle_id: str
    vehicle_type: str
    manufacturing_year: int
    retrofit_date: date
    total_distance_km: float
    monthly_distance_km: float
    battery_capacity_kwh: float
    battery_health_pct: float
    motor_health_pct: float
    electrical_health_pct: float
    energy_consumption_kwh_per_100km: float
    charge_cycles: int
    fast_charge_pct: float
    maintenance_cost_inr: float
    breakdowns: int
    accidents: int
    utilization_pct: float
    maintenance_status: str
    vehicle_condition: str
    operating_cost_inr: float
    health_score: float
    efficiency_score: float
    risk_score: float
    health_status: str
    risk_level: str
    status: str


class MaintenanceRecordOut(OrmModel):
    service_date: date
    service_type: str
    cost_inr: float
    is_breakdown_repair: bool


class TripOut(OrmModel):
    trip_month: str
    trips_count: int
    distance_km: float
    energy_consumed_kwh: float
    energy_cost_inr: float


class RecommendationOut(OrmModel):
    id: int
    vehicle_id: str
    category: str
    priority: str
    title: str
    reason: str
    suggested_action: str
    estimated_annual_saving_inr: float | None = None


class RiskAlertOut(OrmModel):
    id: int
    vehicle_id: str
    risk_score: float
    risk_level: str
    reason: str
    recommended_action: str


class ScoreBreakdownOut(BaseModel):
    health: dict[str, float]
    efficiency: dict[str, float]
    risk: dict[str, float]


class VehicleDetailOut(VehicleOut):
    age_years: int
    retrofit_age_years: float
    score_breakdown: ScoreBreakdownOut
    maintenance_records: list[MaintenanceRecordOut]
    trips: list[TripOut]
    recommendations: list[RecommendationOut]
    risk_alerts: list[RiskAlertOut]


class VehiclePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[VehicleOut]


class RecommendationPage(BaseModel):
    total: int
    page: int
    page_size: int
    total_estimated_annual_saving_inr: float
    items: list[RecommendationOut]


class RiskAlertPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RiskAlertOut]


class DashboardSummaryOut(BaseModel):
    total_vehicles: int
    average_health_score: float
    average_battery_health_pct: float
    fleet_efficiency_score: float
    high_risk_vehicles: int
    total_maintenance_cost_inr: float
    estimated_annual_savings_inr: float
    type_distribution: dict[str, int]
    health_distribution: dict[str, int]
    risk_distribution: dict[str, int]
    recent_vehicles: list[VehicleOut]
    recent_recommendations: list[RecommendationOut]
    important_alerts: list[RiskAlertOut]


class HealthOut(BaseModel):
    status: str
    database: str
    vehicle_count: int


class GenerationResultOut(BaseModel):
    generated: bool
    vehicle_count: int
    message: str
