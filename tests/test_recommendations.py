import unittest
from datetime import date

import support
from app.recommendations import analyse_fleet, build_risk_alert, generate_recommendations
from app.recommendations.formatting import format_inr
from app.services.dataset_builder import build_scored_dataset

VALID_CATEGORIES = {"Cost Reduction", "Maintenance", "Utilization", "Risk Management"}
VALID_PRIORITIES = {"High", "Medium", "Low"}


def risky_vehicle():
    return support.scored_vehicle(
        manufacturing_year=2010,
        retrofit_date=date(2021, 1, 1),
        total_distance_km=60000,
        battery_health_pct=55.0,
        motor_health_pct=50.0,
        electrical_health_pct=55.0,
        maintenance_cost_inr=60000,
        breakdowns=14,
        accidents=3,
        maintenance_status="Overdue",
        vehicle_condition="Poor",
    )


def find(recommendations, category):
    return [item for item in recommendations if item["category"] == category]


def titles(recommendations):
    return [item["title"] for item in recommendations]


class FormattingTests(unittest.TestCase):
    def test_indian_digit_grouping(self):
        self.assertEqual(format_inr(250), "₹250")
        self.assertEqual(format_inr(2500), "₹2,500")
        self.assertEqual(format_inr(15000), "₹15,000")
        self.assertEqual(format_inr(125000), "₹1,25,000")
        self.assertEqual(format_inr(12345678), "₹1,23,45,678")
        self.assertEqual(format_inr(-4200), "-₹4,200")


class RuleTests(unittest.TestCase):
    def test_healthy_vehicle_gets_no_recommendations_and_no_alert(self):
        vehicle = support.healthy_vehicle()
        self.assertEqual(generate_recommendations(vehicle), [])
        self.assertIsNone(build_risk_alert(vehicle))

    def test_low_health_triggers_immediate_inspection(self):
        vehicle = support.scored_vehicle(
            battery_health_pct=82.0,
            motor_health_pct=80.0,
            electrical_health_pct=80.0,
            breakdowns=8,
            vehicle_condition="Poor",
            maintenance_cost_inr=30000,
        )
        self.assertLess(vehicle["health_score"], 50)
        maintenance = find(generate_recommendations(vehicle), "Maintenance")
        self.assertEqual(len(maintenance), 1)
        self.assertEqual(maintenance[0]["priority"], "High")
        self.assertEqual(maintenance[0]["title"], "Immediate inspection required")

    def test_very_low_battery_health_triggers_replacement_assessment(self):
        vehicle = support.healthy_vehicle(battery_health_pct=64.0)
        maintenance = find(generate_recommendations(vehicle), "Maintenance")
        self.assertEqual(maintenance[0]["title"], "Battery replacement assessment")
        self.assertEqual(maintenance[0]["priority"], "High")

    def test_moderate_battery_degradation_triggers_inspection(self):
        vehicle = support.healthy_vehicle(battery_health_pct=76.0)
        maintenance = find(generate_recommendations(vehicle), "Maintenance")
        self.assertEqual(maintenance[0]["title"], "Schedule battery inspection")
        self.assertEqual(maintenance[0]["priority"], "Medium")

    def test_weak_motor_triggers_system_inspection(self):
        vehicle = support.healthy_vehicle(motor_health_pct=55.0)
        maintenance = find(generate_recommendations(vehicle), "Maintenance")
        self.assertEqual(maintenance[0]["title"], "Inspect motor and electrical system")

    def test_heavy_fast_charging_with_worn_battery_is_flagged(self):
        vehicle = support.healthy_vehicle(fast_charge_pct=75.0, battery_health_pct=82.0)
        self.assertIn("Reduce fast charging", titles(generate_recommendations(vehicle)))

    def test_overdue_maintenance_alone_gives_medium_priority(self):
        vehicle = support.healthy_vehicle(maintenance_status="Overdue")
        maintenance = find(generate_recommendations(vehicle), "Maintenance")
        self.assertEqual(maintenance[0]["priority"], "Medium")

    def test_low_utilization_triggers_reassignment(self):
        vehicle = support.healthy_vehicle(utilization_pct=18.0, monthly_distance_km=250)
        utilization = find(generate_recommendations(vehicle), "Utilization")
        self.assertEqual(len(utilization), 1)
        self.assertIn("Reassign", utilization[0]["title"])

    def test_high_maintenance_cost_gives_rupee_saving_estimate(self):
        vehicle = support.healthy_vehicle(maintenance_cost_inr=12000.0)
        cost = find(generate_recommendations(vehicle), "Cost Reduction")
        self.assertEqual(len(cost), 1)
        self.assertEqual(cost[0]["priority"], "High")
        self.assertIn("preventive maintenance", cost[0]["suggested_action"])
        self.assertIn("₹", cost[0]["reason"])
        self.assertGreater(cost[0]["estimated_annual_saving_inr"], 0)

    def test_high_energy_consumption_triggers_cost_reduction_with_saving(self):
        vehicle = support.healthy_vehicle(energy_consumption_kwh_per_100km=4.4, operating_cost_inr=680.0)
        cost = find(generate_recommendations(vehicle), "Cost Reduction")
        self.assertEqual(cost[0]["title"], "Investigate high energy consumption")
        self.assertIn("kWh/100 km", cost[0]["reason"])
        self.assertGreater(cost[0]["estimated_annual_saving_inr"], 0)

    def test_only_cost_reduction_recommendations_carry_savings(self):
        for item in generate_recommendations(risky_vehicle()):
            if item["category"] != "Cost Reduction":
                self.assertIsNone(item["estimated_annual_saving_inr"])

    def test_high_risk_vehicle_gets_alert_and_high_priority_risk_recommendation(self):
        vehicle = risky_vehicle()
        self.assertGreaterEqual(vehicle["risk_score"], 70)
        risk = find(generate_recommendations(vehicle), "Risk Management")
        self.assertEqual(risk[0]["priority"], "High")
        alert = build_risk_alert(vehicle)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["vehicle_id"], vehicle["vehicle_id"])
        self.assertEqual(alert["risk_level"], "High")
        self.assertTrue(alert["reason"].endswith("."))
        self.assertIn("overdue", alert["reason"].lower())
        self.assertIn("battery health", alert["reason"].lower())
        self.assertIn("battery pack", alert["recommended_action"])

    def test_alert_is_not_created_below_threshold(self):
        vehicle = support.scored_vehicle()
        self.assertLess(vehicle["risk_score"], 70)
        self.assertIsNone(build_risk_alert(vehicle))


class FleetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.vehicles = build_scored_dataset(1500)
        cls.recommendations, cls.alerts = analyse_fleet(cls.vehicles)

    def test_each_category_appears_at_most_once_per_vehicle(self):
        seen = set()
        for item in self.recommendations:
            key = (item["vehicle_id"], item["category"])
            self.assertNotIn(key, seen)
            seen.add(key)

    def test_recommendations_have_valid_fields(self):
        self.assertGreater(len(self.recommendations), 0)
        for item in self.recommendations:
            self.assertIn(item["category"], VALID_CATEGORIES)
            self.assertIn(item["priority"], VALID_PRIORITIES)
            for field in ("vehicle_id", "title", "reason", "suggested_action"):
                self.assertTrue(item[field])

    def test_every_category_is_produced(self):
        produced = {item["category"] for item in self.recommendations}
        self.assertEqual(produced, VALID_CATEGORIES)

    def test_ev_specific_recommendations_are_produced(self):
        produced = set(titles(self.recommendations))
        self.assertIn("Schedule battery inspection", produced)
        self.assertIn("Battery replacement assessment", produced)

    def test_no_petrol_or_engine_wording_remains(self):
        text = " ".join(item["reason"] + item["suggested_action"] + item["title"] for item in self.recommendations)
        for word in ("fuel", "petrol", "engine", "litre"):
            self.assertNotIn(word, text.lower())

    def test_alerts_match_high_risk_vehicles_exactly(self):
        high_risk_ids = {v["vehicle_id"] for v in self.vehicles if v["risk_score"] >= 70}
        self.assertEqual({alert["vehicle_id"] for alert in self.alerts}, high_risk_ids)

    def test_every_high_risk_vehicle_has_a_risk_recommendation(self):
        risk_ids = {
            item["vehicle_id"]
            for item in self.recommendations
            if item["category"] == "Risk Management" and item["priority"] == "High"
        }
        self.assertEqual(risk_ids, {alert["vehicle_id"] for alert in self.alerts})


if __name__ == "__main__":
    unittest.main()
