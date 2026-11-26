import pandas as pd

from app.services.data_generator import RAW_COLUMNS

SCORE_COLUMNS = [
    "health_score",
    "efficiency_score",
    "risk_score",
    "health_status",
    "risk_level",
    "status",
]
DATASET_COLUMNS = RAW_COLUMNS + SCORE_COLUMNS


def records_to_csv(records):
    return pd.DataFrame(records, columns=DATASET_COLUMNS).to_csv(index=False)
