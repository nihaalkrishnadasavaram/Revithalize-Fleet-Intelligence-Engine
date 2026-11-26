from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vehicle_type: Mapped[str] = mapped_column(String(20), index=True)
    manufacturing_year: Mapped[int] = mapped_column(Integer)
    retrofit_date: Mapped[date] = mapped_column(Date)
    total_distance_km: Mapped[float] = mapped_column(Float)
    monthly_distance_km: Mapped[float] = mapped_column(Float)
    battery_capacity_kwh: Mapped[float] = mapped_column(Float)
    battery_health_pct: Mapped[float] = mapped_column(Float, index=True)
    motor_health_pct: Mapped[float] = mapped_column(Float)
    electrical_health_pct: Mapped[float] = mapped_column(Float)
    energy_consumption_kwh_per_100km: Mapped[float] = mapped_column(Float)
    charge_cycles: Mapped[int] = mapped_column(Integer)
    fast_charge_pct: Mapped[float] = mapped_column(Float)
    maintenance_cost_inr: Mapped[float] = mapped_column(Float)
    breakdowns: Mapped[int] = mapped_column(Integer)
    accidents: Mapped[int] = mapped_column(Integer)
    utilization_pct: Mapped[float] = mapped_column(Float)
    maintenance_status: Mapped[str] = mapped_column(String(20))
    vehicle_condition: Mapped[str] = mapped_column(String(20))
    operating_cost_inr: Mapped[float] = mapped_column(Float)
    health_score: Mapped[float] = mapped_column(Float, index=True)
    efficiency_score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float, index=True)
    health_status: Mapped[str] = mapped_column(String(20), index=True)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)

    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    trips: Mapped[list["Trip"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    risk_alerts: Mapped[list["RiskAlert"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.vehicle_id"), index=True)
    service_date: Mapped[date] = mapped_column(Date)
    service_type: Mapped[str] = mapped_column(String(50))
    cost_inr: Mapped[float] = mapped_column(Float)
    is_breakdown_repair: Mapped[bool] = mapped_column(default=False)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="maintenance_records")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.vehicle_id"), index=True)
    trip_month: Mapped[str] = mapped_column(String(7))
    trips_count: Mapped[int] = mapped_column(Integer)
    distance_km: Mapped[float] = mapped_column(Float)
    energy_consumed_kwh: Mapped[float] = mapped_column(Float)
    energy_cost_inr: Mapped[float] = mapped_column(Float)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="trips")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.vehicle_id"), index=True)
    category: Mapped[str] = mapped_column(String(30), index=True)
    priority: Mapped[str] = mapped_column(String(10), index=True)
    title: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(Text)
    suggested_action: Mapped[str] = mapped_column(Text)
    estimated_annual_saving_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="recommendations")


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.vehicle_id"), index=True)
    risk_score: Mapped[float] = mapped_column(Float, index=True)
    risk_level: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="risk_alerts")
