import unittest
from datetime import date

import support
from app.scoring import score_breakdown, score_vehicle
from app.scoring.efficiency import EFFICIENCY_WEIGHTS, calculate_efficiency_score
from app.scoring.health import HEALTH_WEIGHTS, calculate_health_score
from app.scoring.risk import RISK_WEIGHTS, calculate_risk_score
from app.scoring.status import health_status, operational_status, risk_level
from app.services.dataset_builder import build_scored_dataset


class WeightTests(unittest.TestCase):
    def test_every_weight_set_adds_up_to_one(self):
        for weights in (HEALTH_WEIGHTS, EFFICIENCY_WEIGHTS, RISK_WEIGHTS):
            self.assertAlmostEqual(sum(weights.values()), 1.0)


class WorkedExampleTests(unittest.TestCase):
    def setUp(self):
        self.vehicle = support.sample_vehicle()

    def test_health_score_matches_hand_calculation(self):
        self.assertAlmostEqual(calculate_health_score(self.vehicle), 66.8, delta=0.05)

    def test_efficiency_score_matches_hand_calculation(self):
        self.assertAlmostEqual(calculate_efficiency_score(self.vehicle), 70.0, delta=0.05)

    def test_risk_score_matches_hand_calculation(self):
        self.assertAlmostEqual(calculate_risk_score(self.vehicle), 46.2, delta=0.05)

    def test_breakdown_lists_every_component(self):
        breakdown = score_breakdown(self.vehicle)
        self.assertEqual(set(breakdown["health"]), set(HEALTH_WEIGHTS))
        self.assertEqual(set(breakdown["efficiency"]), set(EFFICIENCY_WEIGHTS))
        self.assertEqual(set(breakdown["risk"]), set(RISK_WEIGHTS))


class ScoreBehaviourTests(unittest.TestCase):
    def test_all_scores_stay_between_0_and_100(self):
        _, scored = build_scored_dataset(1000)
        for vehicle in scored:
            for key in ("health_score", "efficiency_score", "risk_score"):
                self.assertGreaterEqual(vehicle[key], 0)
                self.assertLessEqual(vehicle[key], 100)

    def test_extreme_inputs_are_clamped(self):
        worst = support.sample_vehicle(
            manufacturing_year=2000,
            retrofit_date=date(2020, 1, 1),
            total_distance_km=900000,
            battery_health_pct=0.0,
            motor_health_pct=0.0,
            electrical_health_pct=0.0,
            maintenance_cost_inr=900000,
            breakdowns=60,
            accidents=10,
            maintenance_status="Overdue",
            vehicle_condition="Poor",
            utilization_pct=0,
            monthly_distance_km=0,
            operating_cost_inr=50000,
        )
        scores = score_vehicle(worst)
        for key in ("health_score", "efficiency_score", "risk_score"):
            self.assertGreaterEqual(scores[key], 0)
            self.assertLessEqual(scores[key], 100)

    def test_new_well_kept_vehicle_has_high_health_and_low_risk(self):
        vehicle = support.healthy_vehicle()
        self.assertGreater(vehicle["health_score"], 85)
        self.assertLess(vehicle["risk_score"], 10)

    def test_old_unreliable_vehicle_has_low_health(self):
        vehicle = support.scored_vehicle(
            manufacturing_year=2008,
            retrofit_date=date(2021, 1, 1),
            total_distance_km=90000,
            battery_health_pct=58.0,
            motor_health_pct=55.0,
            electrical_health_pct=60.0,
            maintenance_cost_inr=60000,
            breakdowns=15,
            vehicle_condition="Poor",
        )
        self.assertLess(vehicle["health_score"], 40)

    def test_lower_battery_health_lowers_health_and_raises_risk(self):
        strong = support.scored_vehicle(battery_health_pct=95.0)
        weak = support.scored_vehicle(battery_health_pct=65.0)
        self.assertLess(weak["health_score"], strong["health_score"])
        self.assertGreater(weak["risk_score"], strong["risk_score"])

    def test_weak_motor_or_electrical_system_lowers_health(self):
        sound = support.scored_vehicle()
        worn_motor = support.scored_vehicle(motor_health_pct=40.0)
        worn_wiring = support.scored_vehicle(electrical_health_pct=40.0)
        self.assertLess(worn_motor["health_score"], sound["health_score"])
        self.assertLess(worn_wiring["health_score"], sound["health_score"])

    def test_failing_electrical_system_raises_critical_condition_risk(self):
        sound = support.scored_vehicle(vehicle_condition="Excellent")
        failing = support.scored_vehicle(vehicle_condition="Excellent", motor_health_pct=30.0)
        self.assertGreater(failing["risk_score"], sound["risk_score"])

    def test_overdue_maintenance_raises_risk(self):
        on_schedule = support.scored_vehicle(maintenance_status="On Schedule")
        overdue = support.scored_vehicle(maintenance_status="Overdue")
        self.assertGreater(overdue["risk_score"], on_schedule["risk_score"])

    def test_more_breakdowns_raise_risk_and_lower_health(self):
        few = support.scored_vehicle(breakdowns=1)
        many = support.scored_vehicle(breakdowns=6)
        self.assertGreater(many["risk_score"], few["risk_score"])
        self.assertLess(many["health_score"], few["health_score"])

    def test_accidents_raise_risk(self):
        none = support.scored_vehicle(accidents=0)
        several = support.scored_vehicle(accidents=3)
        self.assertGreater(several["risk_score"], none["risk_score"])

    def test_lower_energy_consumption_raises_efficiency_score(self):
        frugal = support.scored_vehicle(energy_consumption_kwh_per_100km=2.9)
        thirsty = support.scored_vehicle(energy_consumption_kwh_per_100km=4.4)
        self.assertGreater(frugal["efficiency_score"], thirsty["efficiency_score"])

    def test_higher_utilization_raises_efficiency_score(self):
        busy = support.scored_vehicle(utilization_pct=85.0)
        idle = support.scored_vehicle(utilization_pct=20.0)
        self.assertGreater(busy["efficiency_score"], idle["efficiency_score"])

    def test_lower_operating_cost_raises_efficiency_score(self):
        cheap = support.scored_vehicle(operating_cost_inr=600.0)
        costly = support.scored_vehicle(operating_cost_inr=1100.0)
        self.assertGreater(cheap["efficiency_score"], costly["efficiency_score"])

    def test_older_vehicle_and_older_retrofit_lower_health_when_rates_are_equal(self):
        newer = support.scored_vehicle(
            manufacturing_year=2022,
            retrofit_date=date(2025, 5, 25),
            breakdowns=1,
            maintenance_cost_inr=4000.0,
        )
        older = support.scored_vehicle(
            manufacturing_year=2012,
            retrofit_date=date(2021, 5, 25),
            breakdowns=5,
            maintenance_cost_inr=22000.0,
        )
        self.assertGreater(newer["health_score"], older["health_score"])

    def test_motorcycle_is_scored_against_its_own_benchmark(self):
        scooter = support.scored_vehicle(energy_consumption_kwh_per_100km=3.2)
        motorcycle = support.scored_vehicle(
            vehicle_type="Motorcycle", energy_consumption_kwh_per_100km=4.6
        )
        self.assertAlmostEqual(
            score_breakdown(scooter)["efficiency"]["energy"],
            score_breakdown(motorcycle)["efficiency"]["energy"],
            delta=0.05,
        )

    def test_unknown_vehicle_type_is_rejected(self):
        for old_type in ("Truck", "Car", "Van", "Bus", "Pickup", "Hovercraft"):
            with self.assertRaises(ValueError):
                score_vehicle(support.sample_vehicle(vehicle_type=old_type))

    def test_unknown_condition_is_rejected(self):
        with self.assertRaises(ValueError):
            score_vehicle(support.sample_vehicle(vehicle_condition="Shiny"))


class StatusTests(unittest.TestCase):
    def test_health_status_boundaries(self):
        self.assertEqual(health_status(75), "Good")
        self.assertEqual(health_status(74.9), "Needs Attention")
        self.assertEqual(health_status(50), "Needs Attention")
        self.assertEqual(health_status(49.9), "Critical")

    def test_risk_level_boundaries(self):
        self.assertEqual(risk_level(70), "High")
        self.assertEqual(risk_level(69.9), "Medium")
        self.assertEqual(risk_level(40), "Medium")
        self.assertEqual(risk_level(39.9), "Low")

    def test_operational_status_priority(self):
        self.assertEqual(operational_status(30, 80, "Overdue"), "High Risk")
        self.assertEqual(operational_status(30, 50, "Overdue"), "Needs Inspection")
        self.assertEqual(operational_status(80, 20, "Overdue"), "Maintenance Due")
        self.assertEqual(operational_status(80, 20, "On Schedule"), "Operational")


if __name__ == "__main__":
    unittest.main()
