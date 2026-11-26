from app.config import REFERENCE_DATE
from app.fleet_profiles import ELECTRICITY_TARIFF_INR_PER_KWH, get_profile
from app.recommendations.formatting import format_inr
from app.scoring.metrics import (
    cost_per_km,
    cost_per_km_ratio,
    energy_ratio,
    maintenance_cost_ratio,
    weakest_system_health,
    yearly_maintenance_cost,
)
from app.scoring.status import CRITICAL_HEALTH_THRESHOLD, HIGH_RISK_THRESHOLD

ELEVATED_RISK_THRESHOLD = 55.0
HIGH_MAINTENANCE_COST_RATIO = 1.8
VERY_HIGH_MAINTENANCE_COST_RATIO = 2.5
HIGH_COST_PER_KM_RATIO = 1.4
HIGH_ENERGY_RATIO = 1.25
LOW_UTILIZATION_PCT = 30.0
HEAVY_UTILIZATION_PCT = 90.0
WATCH_HEALTH_THRESHOLD = 65.0
BATTERY_REPLACEMENT_PCT = 70.0
BATTERY_WATCH_PCT = 80.0
SYSTEM_WATCH_PCT = 65.0
SYSTEM_CRITICAL_PCT = 50.0
FAST_CHARGE_HIGH_PCT = 60.0
FAST_CHARGE_BATTERY_LIMIT_PCT = 85.0

MAINTENANCE_RECOVERABLE_SHARE = 0.30
OPERATING_COST_RECOVERABLE_SHARE = 0.50
ENERGY_RECOVERABLE_SHARE = 0.50


def build_recommendation(category, priority, title, reason, suggested_action, saving_inr=None):
    return {
        "category": category,
        "priority": priority,
        "title": title,
        "reason": reason,
        "suggested_action": suggested_action,
        "estimated_annual_saving_inr": None if saving_inr is None else round(saving_inr),
    }


def maintenance_rules(vehicle, reference_date=REFERENCE_DATE):
    matches = []
    health = vehicle["health_score"]
    battery = vehicle["battery_health_pct"]
    system_health = weakest_system_health(vehicle)
    status = vehicle["maintenance_status"]

    if health < CRITICAL_HEALTH_THRESHOLD:
        matches.append(
            build_recommendation(
                "Maintenance",
                "High",
                "Immediate inspection required",
                f"Health score is {health:.1f}, below the critical threshold of {CRITICAL_HEALTH_THRESHOLD:.0f}.",
                "Withdraw the vehicle from regular duty and complete a full inspection of the battery, motor and electrical system.",
            )
        )
    if battery < BATTERY_REPLACEMENT_PCT:
        matches.append(
            build_recommendation(
                "Maintenance",
                "High",
                "Battery replacement assessment",
                f"Battery health is {battery:.1f}%, below the {BATTERY_REPLACEMENT_PCT:.0f}% replacement guideline.",
                "Test pack capacity and cell balance, then repair cells or plan a battery pack replacement.",
            )
        )
    elif battery < BATTERY_WATCH_PCT:
        matches.append(
            build_recommendation(
                "Maintenance",
                "Medium",
                "Schedule battery inspection",
                f"Battery health is {battery:.1f}%, below the {BATTERY_WATCH_PCT:.0f}% watch level.",
                "Book a battery health check and review charging habits to slow further degradation.",
            )
        )
    if system_health < SYSTEM_WATCH_PCT:
        priority = "High" if system_health < SYSTEM_CRITICAL_PCT else "Medium"
        matches.append(
            build_recommendation(
                "Maintenance",
                priority,
                "Inspect motor and electrical system",
                f"Motor or electrical system health is {system_health:.1f}%, below {SYSTEM_WATCH_PCT:.0f}%.",
                "Inspect the motor, controller, wiring and connectors and repair worn parts.",
            )
        )
    if status == "Overdue":
        matches.append(
            build_recommendation(
                "Maintenance",
                "Medium",
                "Complete overdue maintenance",
                "Scheduled maintenance is overdue.",
                "Book the pending service within the next week and confirm all checks are completed.",
            )
        )
    if status == "Due Soon" and health < WATCH_HEALTH_THRESHOLD:
        matches.append(
            build_recommendation(
                "Maintenance",
                "Low",
                "Schedule upcoming maintenance",
                f"Maintenance is due soon and the health score is only {health:.1f}.",
                "Plan the next service now so it is not postponed.",
            )
        )
    if (
        vehicle["fast_charge_pct"] >= FAST_CHARGE_HIGH_PCT
        and battery < FAST_CHARGE_BATTERY_LIMIT_PCT
    ):
        matches.append(
            build_recommendation(
                "Maintenance",
                "Medium",
                "Reduce fast charging",
                f"{vehicle['fast_charge_pct']:.0f}% of charging is fast charging and battery health is {battery:.1f}%.",
                "Move routine charging to slower overnight charging to protect the battery.",
            )
        )
    return matches


def cost_reduction_rules(vehicle, reference_date=REFERENCE_DATE):
    matches = []
    profile = get_profile(vehicle["vehicle_type"])
    vehicle_type = vehicle["vehicle_type"]
    yearly_distance = vehicle["monthly_distance_km"] * 12

    maintenance_ratio = maintenance_cost_ratio(vehicle, reference_date)
    if maintenance_ratio >= HIGH_MAINTENANCE_COST_RATIO:
        yearly_cost = yearly_maintenance_cost(vehicle, reference_date)
        excess = yearly_cost - profile.annual_maintenance_cost_inr
        priority = "High" if maintenance_ratio >= VERY_HIGH_MAINTENANCE_COST_RATIO else "Medium"
        matches.append(
            build_recommendation(
                "Cost Reduction",
                priority,
                "Control high maintenance spending",
                f"Yearly maintenance cost is {format_inr(yearly_cost)}, {maintenance_ratio:.1f}x the {format_inr(profile.annual_maintenance_cost_inr)} benchmark for a {vehicle_type}.",
                "Introduce preventive maintenance and track maintenance cost monthly for this vehicle.",
                excess * MAINTENANCE_RECOVERABLE_SHARE,
            )
        )

    operating_ratio = cost_per_km_ratio(vehicle)
    if operating_ratio >= HIGH_COST_PER_KM_RATIO:
        excess_per_km = cost_per_km(vehicle) - profile.cost_per_km_inr
        matches.append(
            build_recommendation(
                "Cost Reduction",
                "Medium",
                "Review operating cost per kilometre",
                f"Operating cost is ₹{cost_per_km(vehicle):.2f} per km, {operating_ratio:.1f}x the ₹{profile.cost_per_km_inr:.2f} benchmark for a {vehicle_type}.",
                "Review route planning and idle time, and compare the cost with similar vehicles.",
                excess_per_km * yearly_distance * OPERATING_COST_RECOVERABLE_SHARE,
            )
        )

    consumption_ratio = energy_ratio(vehicle)
    if consumption_ratio >= HIGH_ENERGY_RATIO:
        excess_kwh = (
            (vehicle["energy_consumption_kwh_per_100km"] - profile.energy_kwh_per_100km)
            / 100
            * yearly_distance
        )
        matches.append(
            build_recommendation(
                "Cost Reduction",
                "Medium",
                "Investigate high energy consumption",
                f"Energy consumption is {vehicle['energy_consumption_kwh_per_100km']:.1f} kWh/100 km, {consumption_ratio:.1f}x the benchmark for a {vehicle_type}.",
                "Check tyre pressure, motor controller settings, regenerative braking and riding behaviour.",
                excess_kwh * ELECTRICITY_TARIFF_INR_PER_KWH * ENERGY_RECOVERABLE_SHARE,
            )
        )
    return matches


def utilization_rules(vehicle, reference_date=REFERENCE_DATE):
    matches = []
    utilization = vehicle["utilization_pct"]

    if utilization < LOW_UTILIZATION_PCT:
        matches.append(
            build_recommendation(
                "Utilization",
                "Medium",
                "Reassign under-used vehicle",
                f"Utilization is only {utilization:.0f}%, below the {LOW_UTILIZATION_PCT:.0f}% minimum.",
                "Reassign the vehicle to busier routes or riders to optimise fleet allocation.",
            )
        )
    if utilization >= HEAVY_UTILIZATION_PCT and vehicle["health_score"] < WATCH_HEALTH_THRESHOLD:
        matches.append(
            build_recommendation(
                "Utilization",
                "Medium",
                "Reduce load on heavily used vehicle",
                f"Utilization is {utilization:.0f}% while the health score is only {vehicle['health_score']:.1f}.",
                "Rotate the vehicle with a lightly used one to reduce battery and motor wear.",
            )
        )
    return matches


def risk_management_rules(vehicle, reference_date=REFERENCE_DATE):
    matches = []
    risk = vehicle["risk_score"]

    if risk >= HIGH_RISK_THRESHOLD:
        matches.append(
            build_recommendation(
                "Risk Management",
                "High",
                "High operational risk",
                f"Operational risk score is {risk:.1f}, above the high-risk threshold of {HIGH_RISK_THRESHOLD:.0f}.",
                "Restrict the vehicle to low-risk duty and start the corrective actions listed in its risk alert.",
            )
        )
    elif risk >= ELEVATED_RISK_THRESHOLD:
        matches.append(
            build_recommendation(
                "Risk Management",
                "Medium",
                "Elevated operational risk",
                f"Operational risk score is {risk:.1f}, approaching the high-risk threshold.",
                "Increase monitoring and resolve outstanding maintenance before the risk rises further.",
            )
        )
    return matches
