import unittest
from collections import Counter
from datetime import date

import pandas as pd

import support
from app.config import REFERENCE_DATE
from app.fleet_profiles import ELECTRICITY_TARIFF_INR_PER_KWH, VEHICLE_PROFILES
from app.services.csv_export import DATASET_COLUMNS, records_to_csv
from app.services.data_generator import (
    REPAIR_COST_WEIGHTS,
    SERVICE_COST_WEIGHTS,
    RAW_COLUMNS,
    generate_maintenance_records,
    generate_trips,
    generate_vehicle_dataframe,
    recent_month_labels,
)
from app.services.dataset_builder import build_scored_dataset


def add_retrofit_age(frame):
    retrofit = pd.to_datetime(frame["retrofit_date"])
    frame["retrofit_age"] = (pd.Timestamp(REFERENCE_DATE) - retrofit).dt.days / 365.25
    return frame


class VehicleDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.scored = build_scored_dataset(1500)
        cls.frame = add_retrofit_age(pd.DataFrame(cls.scored))
        cls.frame["age"] = REFERENCE_DATE.year - cls.frame["manufacturing_year"]

    def test_requested_number_of_records_is_generated(self):
        self.assertEqual(len(self.raw), 1500)
        self.assertEqual(len(generate_vehicle_dataframe(3000, 1)), 3000)

    def test_vehicle_ids_are_unique(self):
        self.assertTrue(self.raw["vehicle_id"].is_unique)

    def test_all_required_fields_exist(self):
        self.assertEqual(list(self.raw.columns), RAW_COLUMNS)
        for field in (
            "retrofit_date",
            "battery_capacity_kwh",
            "battery_health_pct",
            "motor_health_pct",
            "electrical_health_pct",
            "energy_consumption_kwh_per_100km",
            "charge_cycles",
            "fast_charge_pct",
            "maintenance_cost_inr",
            "operating_cost_inr",
        ):
            self.assertIn(field, RAW_COLUMNS)

    def test_no_petrol_fields_or_usd_remain(self):
        for column in DATASET_COLUMNS:
            self.assertNotIn("fuel", column)
            self.assertNotIn("litre", column)
            self.assertNotIn("usd", column.lower())

    def test_only_motorcycles_and_scooters_exist(self):
        self.assertEqual(set(self.raw["vehicle_type"]), {"Motorcycle", "Scooter"})
        self.assertEqual(set(VEHICLE_PROFILES), {"Motorcycle", "Scooter"})
        share = (self.raw["vehicle_type"] == "Scooter").mean()
        self.assertTrue(0.5 < share < 0.7)

    def test_no_missing_values(self):
        self.assertFalse(self.raw.isna().any().any())

    def test_value_ranges_are_realistic(self):
        self.assertTrue(self.raw["utilization_pct"].between(0, 100).all())
        for column in ("battery_health_pct", "motor_health_pct", "electrical_health_pct", "fast_charge_pct"):
            self.assertTrue(self.raw[column].between(0, 100).all(), column)
        self.assertTrue((self.raw["total_distance_km"] >= 0).all())
        self.assertTrue((self.raw["maintenance_cost_inr"] > 0).all())
        self.assertTrue((self.raw["operating_cost_inr"] > 0).all())
        self.assertTrue((self.raw["breakdowns"] >= 0).all())
        self.assertTrue((self.raw["accidents"] >= 0).all())
        self.assertTrue(self.raw["energy_consumption_kwh_per_100km"].between(1.5, 8).all())

    def test_battery_capacities_come_from_each_type_profile(self):
        for vehicle in self.raw.to_dict("records"):
            options = VEHICLE_PROFILES[vehicle["vehicle_type"]].battery_capacity_options_kwh
            self.assertIn(vehicle["battery_capacity_kwh"], options)

    def test_retrofit_dates_are_valid_and_after_manufacture(self):
        for vehicle in self.raw.to_dict("records"):
            self.assertIsInstance(vehicle["retrofit_date"], date)
            self.assertLessEqual(vehicle["retrofit_date"], REFERENCE_DATE)
            self.assertLess(vehicle["manufacturing_year"], vehicle["retrofit_date"].year)

    def test_charge_cycles_follow_distance_energy_and_battery_size(self):
        for vehicle in self.raw.to_dict("records"):
            expected = (
                vehicle["total_distance_km"]
                * vehicle["energy_consumption_kwh_per_100km"]
                / 100
                / vehicle["battery_capacity_kwh"]
            )
            self.assertAlmostEqual(vehicle["charge_cycles"], expected, delta=max(2, expected * 0.01))

    def test_categorical_values_are_valid(self):
        self.assertTrue(set(self.raw["vehicle_condition"]) <= {"Excellent", "Good", "Fair", "Poor"})
        self.assertTrue(set(self.raw["maintenance_status"]) <= {"On Schedule", "Due Soon", "Overdue"})

    def test_same_seed_gives_same_data(self):
        pd.testing.assert_frame_equal(generate_vehicle_dataframe(200, 7), generate_vehicle_dataframe(200, 7))

    def test_different_seed_gives_different_data(self):
        self.assertFalse(generate_vehicle_dataframe(200, 7).equals(generate_vehicle_dataframe(200, 8)))

    def test_more_charge_cycles_mean_lower_battery_health(self):
        self.assertLess(self.frame["charge_cycles"].corr(self.frame["battery_health_pct"]), -0.5)

    def test_longer_retrofit_history_means_higher_maintenance_cost(self):
        self.assertGreater(self.frame["retrofit_age"].corr(self.frame["maintenance_cost_inr"]), 0.3)

    def test_older_retrofits_break_down_more(self):
        old = self.frame[self.frame["retrofit_age"] >= 3.5]["breakdowns"].mean()
        young = self.frame[self.frame["retrofit_age"] <= 1.0]["breakdowns"].mean()
        self.assertGreater(old, young * 2)

    def test_frequent_breakdowns_mean_higher_risk(self):
        breakdown_rate = self.frame["breakdowns"] / self.frame["retrofit_age"].clip(lower=1)
        self.assertGreater(breakdown_rate.corr(self.frame["risk_score"]), 0.4)

    def test_overdue_maintenance_means_higher_risk(self):
        means = self.frame.groupby("maintenance_status")["risk_score"].mean()
        self.assertGreater(means["Overdue"], means["Due Soon"])
        self.assertGreater(means["Due Soon"], means["On Schedule"])

    def test_lower_battery_health_means_higher_risk_and_lower_health_score(self):
        self.assertLess(self.frame["battery_health_pct"].corr(self.frame["risk_score"]), -0.3)
        self.assertGreater(self.frame["battery_health_pct"].corr(self.frame["health_score"]), 0.4)

    def test_lower_energy_consumption_means_better_efficiency_score(self):
        benchmark = {name: profile.energy_kwh_per_100km for name, profile in VEHICLE_PROFILES.items()}
        ratio = self.frame["energy_consumption_kwh_per_100km"] / self.frame["vehicle_type"].map(benchmark)
        self.assertLess(ratio.corr(self.frame["efficiency_score"]), -0.2)

    def test_poorer_condition_means_lower_health(self):
        means = self.frame.groupby("vehicle_condition")["health_score"].mean()
        self.assertGreater(means["Excellent"], means["Good"])
        self.assertGreater(means["Good"], means["Fair"])
        self.assertGreater(means["Fair"], means["Poor"])

    def test_financial_assumptions_are_plausible_in_rupees(self):
        yearly_operating = self.frame["operating_cost_inr"].mean() * 12
        self.assertTrue(4000 < yearly_operating < 20000)
        yearly_maintenance = self.frame["maintenance_cost_inr"] / self.frame["retrofit_age"].clip(lower=1)
        self.assertTrue(2000 < yearly_maintenance.mean() < 12000)

    def test_dataset_contains_a_useful_spread_of_outcomes(self):
        statuses = Counter(self.frame["status"])
        for expected in ("Operational", "Maintenance Due", "Needs Inspection", "High Risk"):
            self.assertGreater(statuses[expected], 0)

    def test_csv_export_has_header_and_one_row_per_vehicle(self):
        lines = records_to_csv(self.scored).strip().splitlines()
        self.assertEqual(lines[0].split(","), DATASET_COLUMNS)
        self.assertEqual(len(lines), len(self.scored) + 1)
        self.assertIn("maintenance_cost_inr", lines[0])
        self.assertIn("battery_health_pct", lines[0])


class RelatedRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = generate_vehicle_dataframe(300, 11)
        cls.maintenance = generate_maintenance_records(cls.raw, 11)
        cls.trips = generate_trips(cls.raw, 11)
        cls.retrofit_dates = dict(zip(cls.raw["vehicle_id"], cls.raw["retrofit_date"]))

    def test_every_vehicle_has_maintenance_history(self):
        ids = {record["vehicle_id"] for record in self.maintenance}
        self.assertEqual(ids, set(self.raw["vehicle_id"]))

    def test_maintenance_records_add_up_to_vehicle_total(self):
        totals = {}
        for record in self.maintenance:
            totals[record["vehicle_id"]] = totals.get(record["vehicle_id"], 0) + record["cost_inr"]
        for vehicle in self.raw.to_dict("records"):
            self.assertAlmostEqual(totals[vehicle["vehicle_id"]], vehicle["maintenance_cost_inr"], delta=0.05)

    def test_maintenance_dates_fall_between_retrofit_and_reference_date(self):
        for record in self.maintenance:
            self.assertIsInstance(record["service_date"], date)
            self.assertLess(record["service_date"], REFERENCE_DATE)
            self.assertGreaterEqual(record["service_date"], self.retrofit_dates[record["vehicle_id"]])

    def test_service_types_are_ev_specific(self):
        known = set(SERVICE_COST_WEIGHTS) | set(REPAIR_COST_WEIGHTS)
        seen = {record["service_type"] for record in self.maintenance}
        self.assertTrue(seen <= known)
        self.assertTrue(seen & {"Motor Repair", "Controller Repair", "Battery Cell Repair"})
        self.assertIn("Battery Health Check", seen)

    def test_repair_types_are_flagged_as_breakdown_repairs(self):
        for record in self.maintenance:
            self.assertEqual(
                record["is_breakdown_repair"], record["service_type"] in REPAIR_COST_WEIGHTS
            )

    def test_trips_only_cover_months_after_retrofit(self):
        counts = Counter(trip["vehicle_id"] for trip in self.trips)
        self.assertEqual(set(counts), set(self.raw["vehicle_id"]))
        self.assertTrue(all(1 <= count <= 6 for count in counts.values()))
        for trip in self.trips:
            retrofit_month = self.retrofit_dates[trip["vehicle_id"]].strftime("%Y-%m")
            self.assertGreaterEqual(trip["trip_month"], retrofit_month)

    def test_trip_energy_values_are_positive_and_priced_in_rupees(self):
        for trip in self.trips:
            self.assertGreater(trip["trips_count"], 0)
            self.assertGreater(trip["distance_km"], 0)
            self.assertGreater(trip["energy_consumed_kwh"], 0)
            self.assertAlmostEqual(
                trip["energy_cost_inr"],
                trip["energy_consumed_kwh"] * ELECTRICITY_TARIFF_INR_PER_KWH,
                delta=0.05,
            )

    def test_month_labels_wrap_across_years(self):
        self.assertEqual(
            recent_month_labels(date(2026, 2, 10), 4),
            ["2025-11", "2025-12", "2026-01", "2026-02"],
        )


if __name__ == "__main__":
    unittest.main()
