from datetime import timedelta

import numpy as np
import pandas as pd

from app.config import REFERENCE_DATE
from app.fleet_profiles import ELECTRICITY_TARIFF_INR_PER_KWH, VEHICLE_PROFILES

RAW_COLUMNS = [
    "vehicle_id",
    "vehicle_type",
    "manufacturing_year",
    "retrofit_date",
    "total_distance_km",
    "monthly_distance_km",
    "battery_capacity_kwh",
    "battery_health_pct",
    "motor_health_pct",
    "electrical_health_pct",
    "energy_consumption_kwh_per_100km",
    "charge_cycles",
    "fast_charge_pct",
    "maintenance_cost_inr",
    "breakdowns",
    "accidents",
    "utilization_pct",
    "maintenance_status",
    "vehicle_condition",
    "operating_cost_inr",
]

SERVICE_COST_WEIGHTS = {
    "Routine Service": 1.0,
    "Brake Service": 1.0,
    "Tyre Replacement": 1.5,
    "Battery Health Check": 0.5,
    "Charging Port Service": 0.7,
}
REPAIR_COST_WEIGHTS = {
    "Motor Repair": 3.0,
    "Controller Repair": 3.0,
    "Battery Cell Repair": 4.0,
    "Wiring and Connector Repair": 1.5,
}

CONDITION_WEAR_LIMITS = (0.145, 0.315, 0.50)
DUE_SOON_PROBABILITY = 0.18
MAX_SERVICE_RECORDS = 8
TRIP_HISTORY_MONTHS = 6
MAX_RETROFIT_HISTORY_YEARS = 5.5


def profile_values(vehicle_types, field_name):
    return np.array([getattr(VEHICLE_PROFILES[name], field_name) for name in vehicle_types])


def generate_vehicle_dataframe(count, seed, reference_date=REFERENCE_DATE):
    rng = np.random.default_rng(seed)

    type_names = list(VEHICLE_PROFILES)
    type_shares = np.array([VEHICLE_PROFILES[name].fleet_share for name in type_names])
    vehicle_types = rng.choice(type_names, size=count, p=type_shares / type_shares.sum())

    retrofit_years = np.clip(rng.gamma(2.0, 1.1, size=count), 0.1, MAX_RETROFIT_HISTORY_YEARS)
    retrofit_dates = [reference_date - timedelta(days=int(years * 365.25)) for years in retrofit_years]
    age_at_retrofit = np.clip(np.round(rng.gamma(2.5, 2.2, size=count)), 1, 14).astype(int)
    manufacturing_years = np.array([item.year for item in retrofit_dates]) - age_at_retrofit
    vehicle_ages = reference_date.year - manufacturing_years
    service_years = np.maximum(retrofit_years, 1.0)

    utilization = np.clip(rng.beta(3.2, 2.4, size=count) * 100, 5, 98)
    monthly_capacity = profile_values(vehicle_types, "monthly_capacity_km")
    monthly_distance = monthly_capacity * utilization / 100 * rng.uniform(0.9, 1.1, count)
    total_distance = monthly_distance * 12 * retrofit_years * rng.lognormal(0, 0.12, count)

    battery_capacity = np.array(
        [rng.choice(VEHICLE_PROFILES[name].battery_capacity_options_kwh) for name in vehicle_types]
    )
    benchmark_energy = profile_values(vehicle_types, "energy_kwh_per_100km")
    energy_consumption = benchmark_energy * rng.lognormal(0, 0.10, count) * (1 + 0.02 * retrofit_years)

    charge_cycles = np.round(total_distance * energy_consumption / 100 / battery_capacity).astype(int)
    fast_charge_share = np.clip(rng.beta(2, 4, size=count) * 100, 0, 90)
    battery_quality = rng.gamma(2.5, 1 / 2.5, count)
    cycle_fade = charge_cycles * 0.02 * battery_quality * (1 + 0.8 * fast_charge_share / 100)
    battery_health = np.clip(
        100 - cycle_fade - 1.0 * retrofit_years - rng.normal(0, 1.5, count), 40, 100
    )

    reliability_factor = rng.gamma(1.0, 1.0, count)
    expected_breakdowns = (
        (0.10 + 0.50 * retrofit_years)
        * (0.7 + 0.6 * utilization / 100)
        * (1 + 0.04 * vehicle_ages)
        * reliability_factor
    )
    breakdowns = np.minimum(rng.poisson(expected_breakdowns), 12)

    rider_risk_factor = rng.gamma(1.2, 1 / 1.2, count)
    expected_accidents = 0.10 * retrofit_years * (0.5 + utilization / 100) * rider_risk_factor
    accidents = np.minimum(rng.poisson(expected_accidents), 5)

    motor_health = np.clip(
        98 - 0.0003 * total_distance - 1.5 * breakdowns + rng.normal(0, 6, count), 30, 100
    )
    electrical_health = np.clip(
        98 - 0.6 * vehicle_ages - 1.5 * retrofit_years - 1.0 * breakdowns + rng.normal(0, 4, count),
        30,
        100,
    )

    breakdown_rate = breakdowns / service_years
    wear = (
        0.25 * vehicle_ages / 20
        + 0.20 * retrofit_years / 8
        + 0.30 * np.minimum(breakdown_rate / 2, 1)
        + 0.10 * np.minimum(accidents / 3, 1)
        + 0.25 * np.minimum((100 - battery_health) / 40, 1)
        + rng.normal(0, 0.06, count)
    )
    vehicle_condition = np.select(
        [wear < CONDITION_WEAR_LIMITS[0], wear < CONDITION_WEAR_LIMITS[1], wear < CONDITION_WEAR_LIMITS[2]],
        ["Excellent", "Good", "Fair"],
        default="Poor",
    )

    overdue_probability = np.clip(0.03 + 0.03 * retrofit_years + 0.25 * (wear > 0.40), 0, 0.6)
    draw = rng.uniform(size=count)
    maintenance_status = np.select(
        [draw < overdue_probability, draw < overdue_probability + DUE_SOON_PROBABILITY],
        ["Overdue", "Due Soon"],
        default="On Schedule",
    )

    annual_maintenance = profile_values(vehicle_types, "annual_maintenance_cost_inr")
    routine_cost = (
        annual_maintenance
        * np.maximum(retrofit_years, 0.5)
        * (0.7 + 0.1 * retrofit_years)
        * rng.lognormal(0, 0.25, count)
    )
    repair_cost = breakdowns * annual_maintenance * 0.35 * rng.lognormal(0, 0.3, count)
    accident_cost = accidents * annual_maintenance * 0.6 * rng.lognormal(0, 0.3, count)
    maintenance_cost = routine_cost + repair_cost + accident_cost

    electricity_cost = (
        monthly_distance
        * ELECTRICITY_TARIFF_INR_PER_KWH
        * energy_consumption
        / 100
        * rng.lognormal(0, 0.05, count)
    )
    fixed_cost = profile_values(vehicle_types, "monthly_fixed_cost_inr") * rng.lognormal(0, 0.08, count)
    operating_cost = electricity_cost + fixed_cost

    return pd.DataFrame(
        {
            "vehicle_id": [f"VEH-{number:04d}" for number in range(1, count + 1)],
            "vehicle_type": vehicle_types,
            "manufacturing_year": manufacturing_years,
            "retrofit_date": retrofit_dates,
            "total_distance_km": np.round(total_distance).astype(int),
            "monthly_distance_km": np.round(monthly_distance).astype(int),
            "battery_capacity_kwh": battery_capacity,
            "battery_health_pct": np.round(battery_health, 1),
            "motor_health_pct": np.round(motor_health, 1),
            "electrical_health_pct": np.round(electrical_health, 1),
            "energy_consumption_kwh_per_100km": np.round(energy_consumption, 2),
            "charge_cycles": charge_cycles,
            "fast_charge_pct": np.round(fast_charge_share, 1),
            "maintenance_cost_inr": np.round(maintenance_cost, 2),
            "breakdowns": breakdowns,
            "accidents": accidents,
            "utilization_pct": np.round(utilization, 1),
            "maintenance_status": maintenance_status,
            "vehicle_condition": vehicle_condition,
            "operating_cost_inr": np.round(operating_cost, 2),
        },
        columns=RAW_COLUMNS,
    )


def generate_maintenance_records(vehicles, seed, reference_date=REFERENCE_DATE):
    rng = np.random.default_rng(seed + 1)
    records = []
    for vehicle in vehicles.to_dict("records"):
        retrofit_days = max((reference_date - vehicle["retrofit_date"]).days, 30)
        breakdown_count = int(vehicle["breakdowns"])
        record_count = int(
            min(MAX_SERVICE_RECORDS, max(1, round(retrofit_days / 365.25 * 1.5) + min(breakdown_count, 3)))
        )
        repair_slots = min(breakdown_count, record_count)

        service_types = []
        for index in range(record_count):
            catalogue = REPAIR_COST_WEIGHTS if index < repair_slots else SERVICE_COST_WEIGHTS
            service_types.append(str(rng.choice(list(catalogue))))

        weights = np.array(
            [
                (REPAIR_COST_WEIGHTS.get(name) or SERVICE_COST_WEIGHTS[name]) * rng.lognormal(0, 0.3)
                for name in service_types
            ]
        )
        total_cost = float(vehicle["maintenance_cost_inr"])
        costs = np.round(weights / weights.sum() * total_cost, 2)
        costs[int(np.argmax(costs))] += round(total_cost - costs.sum(), 2)

        day_offsets = rng.integers(5, retrofit_days, size=record_count)
        for index in range(record_count):
            records.append(
                {
                    "vehicle_id": vehicle["vehicle_id"],
                    "service_date": reference_date - timedelta(days=int(day_offsets[index])),
                    "service_type": service_types[index],
                    "cost_inr": float(costs[index]),
                    "is_breakdown_repair": index < repair_slots,
                }
            )
    return records


def recent_month_labels(reference_date, months):
    labels = []
    year, month = reference_date.year, reference_date.month
    for _ in range(months):
        labels.append(f"{year}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return labels[::-1]


def generate_trips(vehicles, seed, reference_date=REFERENCE_DATE, months=TRIP_HISTORY_MONTHS):
    rng = np.random.default_rng(seed + 2)
    month_labels = recent_month_labels(reference_date, months)
    trips = []
    for vehicle in vehicles.to_dict("records"):
        profile = VEHICLE_PROFILES[vehicle["vehicle_type"]]
        retrofit_month = vehicle["retrofit_date"].strftime("%Y-%m")
        for label in month_labels:
            if label < retrofit_month:
                continue
            distance = float(vehicle["monthly_distance_km"]) * float(rng.uniform(0.8, 1.2))
            energy = (
                distance
                * float(vehicle["energy_consumption_kwh_per_100km"])
                / 100
                * float(rng.uniform(0.97, 1.03))
            )
            average_trip = profile.average_trip_km * float(rng.uniform(0.8, 1.2))
            trips.append(
                {
                    "vehicle_id": vehicle["vehicle_id"],
                    "trip_month": label,
                    "trips_count": max(1, int(round(distance / average_trip))),
                    "distance_km": round(distance, 1),
                    "energy_consumed_kwh": round(energy, 2),
                    "energy_cost_inr": round(energy * ELECTRICITY_TARIFF_INR_PER_KWH, 2),
                }
            )
    return trips
