from sqlalchemy import func, select

from app.config import DEFAULT_RECORD_COUNT, SCHEMA_VERSION
from app.database.connection import SessionLocal, engine
from app.models import Base, Vehicle
from app.services.fleet_loader import load_synthetic_fleet


def prepare_schema(target_engine=engine):
    with target_engine.begin() as connection:
        stored_version = connection.exec_driver_sql("PRAGMA user_version").scalar()
        if stored_version != SCHEMA_VERSION:
            Base.metadata.drop_all(bind=connection)
            Base.metadata.create_all(bind=connection)
            connection.exec_driver_sql(f"PRAGMA user_version = {SCHEMA_VERSION}")


def initialize_database():
    prepare_schema()
    with SessionLocal() as session:
        vehicle_count = session.scalar(select(func.count()).select_from(Vehicle))
        if vehicle_count == 0:
            load_synthetic_fleet(session, DEFAULT_RECORD_COUNT)
