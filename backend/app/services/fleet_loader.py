from datetime import datetime

from sqlalchemy import delete, insert

from app.config import RANDOM_SEED
from app.models import MaintenanceRecord, Recommendation, RiskAlert, Trip, Vehicle
from app.recommendations import analyse_fleet
from app.services.data_generator import generate_maintenance_records, generate_trips
from app.services.dataset_builder import build_scored_dataset


def insert_rows(session, model, rows):
    if rows:
        session.execute(insert(model), rows)


def clear_fleet_data(session):
    for model in (RiskAlert, Recommendation, Trip, MaintenanceRecord, Vehicle):
        session.execute(delete(model))


def load_synthetic_fleet(session, count, seed=RANDOM_SEED):
    raw_vehicles, scored_vehicles = build_scored_dataset(count, seed)
    recommendations, alerts = analyse_fleet(scored_vehicles)
    created_at = datetime.now()

    insert_rows(session, Vehicle, scored_vehicles)
    insert_rows(session, MaintenanceRecord, generate_maintenance_records(raw_vehicles, seed))
    insert_rows(session, Trip, generate_trips(raw_vehicles, seed))
    insert_rows(
        session, Recommendation, [{**item, "created_at": created_at} for item in recommendations]
    )
    insert_rows(session, RiskAlert, [{**item, "created_at": created_at} for item in alerts])
    session.commit()
    return len(scored_vehicles)
