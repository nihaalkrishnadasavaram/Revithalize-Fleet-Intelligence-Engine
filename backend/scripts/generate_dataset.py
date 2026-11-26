import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import CSV_EXPORT_PATH, RANDOM_SEED
from app.services.csv_export import records_to_csv
from app.services.dataset_builder import build_scored_dataset


def main():
    parser = argparse.ArgumentParser(description="Generate the RFIE synthetic fleet dataset as a CSV file.")
    parser.add_argument("--count", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--output", type=Path, default=CSV_EXPORT_PATH)
    arguments = parser.parse_args()

    _, scored_vehicles = build_scored_dataset(arguments.count, arguments.seed)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(records_to_csv(scored_vehicles), encoding="utf-8", newline="")
    print(f"Wrote {len(scored_vehicles)} vehicles to {arguments.output}")


if __name__ == "__main__":
    main()
