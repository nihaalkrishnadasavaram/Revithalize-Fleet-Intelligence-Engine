import unittest

import support
from fastapi.testclient import TestClient

from app.main import app
from app.services.csv_export import DATASET_COLUMNS


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()
        cls.vehicle_count = cls.client.get("/api/health").json()["vehicle_count"]

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_root_points_to_documentation(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["documentation"], "/docs")

    def test_health_reports_database_and_vehicle_count(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["database"], "connected")
        self.assertGreater(body["vehicle_count"], 0)

    def test_database_is_seeded_automatically_on_startup(self):
        self.assertEqual(self.vehicle_count, 200)

    def test_dashboard_summary_contains_all_kpis(self):
        response = self.client.get("/api/dashboard/summary")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_vehicles"], self.vehicle_count)
        self.assertTrue(0 <= body["average_health_score"] <= 100)
        self.assertTrue(0 <= body["fleet_efficiency_score"] <= 100)
        self.assertGreater(body["total_maintenance_cost_inr"], 0)
        self.assertTrue(0 < body["average_battery_health_pct"] <= 100)
        self.assertGreaterEqual(body["estimated_annual_savings_inr"], 0)
        self.assertEqual(set(body["type_distribution"]), {"Motorcycle", "Scooter"})
        self.assertEqual(sum(body["type_distribution"].values()), self.vehicle_count)
        self.assertEqual(sum(body["health_distribution"].values()), self.vehicle_count)
        self.assertEqual(sum(body["risk_distribution"].values()), self.vehicle_count)
        self.assertEqual(body["high_risk_vehicles"], body["risk_distribution"]["High"])
        self.assertLessEqual(len(body["recent_vehicles"]), 8)
        self.assertLessEqual(len(body["recent_recommendations"]), 5)
        self.assertLessEqual(len(body["important_alerts"]), 5)

    def test_vehicle_list_is_paginated(self):
        body = self.client.get("/api/vehicles", params={"page": 1, "page_size": 10}).json()
        self.assertEqual(body["total"], self.vehicle_count)
        self.assertEqual(len(body["items"]), 10)
        second_page = self.client.get("/api/vehicles", params={"page": 2, "page_size": 10}).json()
        self.assertNotEqual(body["items"][0]["vehicle_id"], second_page["items"][0]["vehicle_id"])

    def test_vehicle_search_by_id(self):
        body = self.client.get("/api/vehicles", params={"search": "VEH-0001"}).json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["vehicle_id"], "VEH-0001")

    def test_vehicle_search_by_type(self):
        body = self.client.get("/api/vehicles", params={"search": "scooter", "page_size": 100}).json()
        self.assertGreater(body["total"], 0)
        self.assertTrue(all(item["vehicle_type"] == "Scooter" for item in body["items"]))

    def test_vehicle_type_filter(self):
        for vehicle_type in ("Motorcycle", "Scooter"):
            body = self.client.get(
                "/api/vehicles", params={"vehicle_type": vehicle_type, "page_size": 100}
            ).json()
            self.assertGreater(body["total"], 0)
            self.assertTrue(all(item["vehicle_type"] == vehicle_type for item in body["items"]))

    def test_vehicles_expose_ev_fields_and_no_petrol_fields(self):
        item = self.client.get("/api/vehicles", params={"page_size": 1}).json()["items"][0]
        for field in (
            "battery_capacity_kwh",
            "battery_health_pct",
            "motor_health_pct",
            "electrical_health_pct",
            "energy_consumption_kwh_per_100km",
            "charge_cycles",
            "fast_charge_pct",
            "retrofit_date",
            "maintenance_cost_inr",
            "operating_cost_inr",
        ):
            self.assertIn(field, item)
        self.assertNotIn("fuel_consumption_l_per_100km", item)
        self.assertIn(item["vehicle_type"], {"Motorcycle", "Scooter"})

    def test_vehicle_status_filter(self):
        body = self.client.get("/api/vehicles", params={"status": "Operational", "page_size": 100}).json()
        self.assertTrue(all(item["status"] == "Operational" for item in body["items"]))

    def test_vehicle_list_rejects_invalid_paging(self):
        self.assertEqual(self.client.get("/api/vehicles", params={"page_size": 0}).status_code, 422)
        self.assertEqual(self.client.get("/api/vehicles", params={"page": 0}).status_code, 422)
        self.assertEqual(self.client.get("/api/vehicles", params={"page_size": 1000}).status_code, 422)

    def test_vehicle_detail_includes_scores_history_and_breakdown(self):
        response = self.client.get("/api/vehicles/VEH-0001")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["vehicle_id"], "VEH-0001")
        self.assertEqual(set(body["score_breakdown"]), {"health", "efficiency", "risk"})
        self.assertGreater(len(body["maintenance_records"]), 0)
        self.assertTrue(1 <= len(body["trips"]) <= 6)
        self.assertGreater(body["retrofit_age_years"], 0)
        self.assertIn("energy_cost_inr", body["trips"][0])
        self.assertIn("cost_inr", body["maintenance_records"][0])
        self.assertIn("recommendations", body)
        self.assertIn("risk_alerts", body)

    def test_vehicle_detail_accepts_lowercase_id(self):
        self.assertEqual(self.client.get("/api/vehicles/veh-0002").status_code, 200)

    def test_unknown_vehicle_returns_404_json(self):
        response = self.client.get("/api/vehicles/VEH-9999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_recommendations_are_returned_with_required_fields(self):
        body = self.client.get("/api/recommendations", params={"page_size": 50}).json()
        self.assertGreater(body["total"], 0)
        self.assertGreaterEqual(body["total_estimated_annual_saving_inr"], 0)
        for item in body["items"]:
            for field in ("vehicle_id", "category", "priority", "title", "reason", "suggested_action"):
                self.assertTrue(item[field])
            self.assertIn("estimated_annual_saving_inr", item)

    def test_cost_recommendations_carry_rupee_savings(self):
        body = self.client.get(
            "/api/recommendations", params={"category": "Cost Reduction", "page_size": 100}
        ).json()
        self.assertGreater(body["total"], 0)
        self.assertGreater(body["total_estimated_annual_saving_inr"], 0)
        for item in body["items"]:
            self.assertGreater(item["estimated_annual_saving_inr"], 0)

    def test_recommendations_are_sorted_by_priority(self):
        items = self.client.get("/api/recommendations", params={"page_size": 100}).json()["items"]
        rank = {"High": 0, "Medium": 1, "Low": 2}
        ranks = [rank[item["priority"]] for item in items]
        self.assertEqual(ranks, sorted(ranks))

    def test_recommendations_can_be_filtered(self):
        body = self.client.get(
            "/api/recommendations", params={"category": "Maintenance", "priority": "High", "page_size": 100}
        ).json()
        for item in body["items"]:
            self.assertEqual(item["category"], "Maintenance")
            self.assertEqual(item["priority"], "High")

    def test_alerts_only_contain_high_risk_vehicles_sorted_by_risk(self):
        body = self.client.get("/api/alerts", params={"page_size": 100}).json()
        scores = [item["risk_score"] for item in body["items"]]
        self.assertTrue(all(score >= 70 for score in scores))
        self.assertEqual(scores, sorted(scores, reverse=True))
        for item in body["items"]:
            self.assertTrue(item["reason"])
            self.assertTrue(item["recommended_action"])

    def test_alert_count_matches_dashboard_high_risk_count(self):
        summary = self.client.get("/api/dashboard/summary").json()
        alerts = self.client.get("/api/alerts", params={"page_size": 1}).json()
        self.assertEqual(alerts["total"], summary["high_risk_vehicles"])

    def test_generate_does_not_overwrite_existing_data_by_default(self):
        response = self.client.post("/api/data/generate")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["generated"])
        self.assertEqual(body["vehicle_count"], self.vehicle_count)

    def test_generate_rejects_counts_outside_allowed_range(self):
        self.assertEqual(self.client.post("/api/data/generate", params={"count": 5}).status_code, 422)
        self.assertEqual(self.client.post("/api/data/generate", params={"count": 99999}).status_code, 422)

    def test_force_generate_rebuilds_the_database(self):
        response = self.client.post("/api/data/generate", params={"count": 200, "force": True})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["generated"])
        self.assertEqual(self.client.get("/api/health").json()["vehicle_count"], 200)

    def test_csv_export_contains_every_vehicle(self):
        response = self.client.get("/api/data/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["content-type"])
        lines = response.text.strip().splitlines()
        self.assertEqual(lines[0].split(","), DATASET_COLUMNS)
        self.assertEqual(len(lines), self.vehicle_count + 1)


if __name__ == "__main__":
    unittest.main()
