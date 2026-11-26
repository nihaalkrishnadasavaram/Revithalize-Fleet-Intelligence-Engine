from app.config import RANDOM_SEED
from app.scoring import score_fleet
from app.services.data_generator import generate_vehicle_dataframe


def build_scored_dataset(count, seed=RANDOM_SEED):
    raw_vehicles = generate_vehicle_dataframe(count, seed)
    scored_vehicles = score_fleet(raw_vehicles.to_dict("records"))
    return raw_vehicles, scored_vehicles
