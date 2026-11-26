import sqlite3
import tempfile
import unittest
from pathlib import Path

import support
from sqlalchemy import create_engine, inspect, text

from app.config import SCHEMA_VERSION
from app.database.initializer import prepare_schema


def read_user_version(database_path):
    with sqlite3.connect(database_path) as connection:
        return connection.execute("PRAGMA user_version").fetchone()[0]


class SchemaResetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.directory.name, "legacy.db")
        self.engine = create_engine(f"sqlite:///{self.database_path.as_posix()}")

    def tearDown(self):
        self.engine.dispose()
        self.directory.cleanup()

    def create_legacy_petrol_database(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "CREATE TABLE vehicles (vehicle_id TEXT PRIMARY KEY, vehicle_type TEXT, "
                "fuel_consumption_l_per_100km REAL, maintenance_cost REAL)"
            )
            connection.execute("INSERT INTO vehicles VALUES ('VEH-0001', 'Truck', 30.0, 5000.0)")

    def test_legacy_database_is_rebuilt_with_the_ev_schema(self):
        self.create_legacy_petrol_database()
        prepare_schema(self.engine)
        columns = {column["name"] for column in inspect(self.engine).get_columns("vehicles")}
        self.assertIn("battery_health_pct", columns)
        self.assertIn("maintenance_cost_inr", columns)
        self.assertNotIn("fuel_consumption_l_per_100km", columns)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM vehicles")).scalar(), 0)
        self.assertEqual(read_user_version(self.database_path), SCHEMA_VERSION)

    def test_fresh_database_gets_all_tables_and_version(self):
        prepare_schema(self.engine)
        tables = set(inspect(self.engine).get_table_names())
        self.assertEqual(
            tables, {"vehicles", "maintenance_records", "trips", "recommendations", "risk_alerts"}
        )
        self.assertEqual(read_user_version(self.database_path), SCHEMA_VERSION)

    def test_current_database_is_left_untouched(self):
        prepare_schema(self.engine)
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO vehicles (vehicle_id, vehicle_type, manufacturing_year, retrofit_date, "
                    "total_distance_km, monthly_distance_km, battery_capacity_kwh, battery_health_pct, "
                    "motor_health_pct, electrical_health_pct, energy_consumption_kwh_per_100km, "
                    "charge_cycles, fast_charge_pct, maintenance_cost_inr, breakdowns, accidents, "
                    "utilization_pct, maintenance_status, vehicle_condition, operating_cost_inr, "
                    "health_score, efficiency_score, risk_score, health_status, risk_level, status) "
                    "VALUES ('VEH-0001', 'Scooter', 2019, '2024-01-01', 1000, 500, 2.4, 95, 95, 95, 3.2, "
                    "40, 20, 1000, 0, 0, 60, 'On Schedule', 'Good', 600, 80, 70, 10, 'Good', 'Low', 'Operational')"
                )
            )
        prepare_schema(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM vehicles")).scalar(), 1)


if __name__ == "__main__":
    unittest.main()
