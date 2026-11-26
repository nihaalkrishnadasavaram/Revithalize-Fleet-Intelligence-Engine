# Synthetic Dataset Documentation

The dataset is produced by `backend/app/services/data_generator.py` with NumPy / Pandas. A fixed random seed (default 42) makes it **reproducible**: the same seed always yields the same fleet.

> **All data is synthetic.** The vehicle specifications, energy figures, costs and prices are illustrative benchmarks for an academic project. They are **not measured ReVithalize fleet data**, and the company did not supply them. Do not quote them as real company figures.

## Business context

ReVithalize converts petrol two-wheelers into electric vehicles. The fleet therefore contains only two vehicle types:

| Type | Share |
|------|------:|
| Scooter | 60 % |
| Motorcycle | 40 % |

## Fields

| Field | Description |
|-------|-------------|
| `vehicle_id` | Unique ID, `VEH-0001` … `VEH-3000` |
| `vehicle_type` | Motorcycle or Scooter |
| `manufacturing_year` | Year the original petrol two-wheeler was built |
| `retrofit_date` | Date of the EV retrofit (up to 5.5 years before the reference date, 25 Nov 2026) |
| `total_distance_km` | Distance travelled **since the retrofit** |
| `monthly_distance_km` | Current monthly distance |
| `battery_capacity_kwh` | Battery size, chosen from per-type options |
| `battery_health_pct` | Remaining battery health, 40–100 % |
| `motor_health_pct` | Motor condition, 30–100 % |
| `electrical_health_pct` | Controller, wiring and connector condition, 30–100 % |
| `energy_consumption_kwh_per_100km` | Electricity used per 100 km |
| `charge_cycles` | Equivalent full charge cycles since retrofit |
| `fast_charge_pct` | Share of charging done with fast charging |
| `maintenance_cost_inr` | Maintenance spend since retrofit, in ₹ |
| `breakdowns`, `accidents` | Counts since retrofit |
| `utilization_pct` | Share of capacity used, 5–98 % |
| `maintenance_status` | On Schedule / Due Soon / Overdue |
| `vehicle_condition` | Excellent / Good / Fair / Poor |
| `operating_cost_inr` | Monthly operating cost in ₹ (electricity + fixed costs) |
| *scores* | `health_score`, `efficiency_score`, `risk_score`, `health_status`, `risk_level`, `status` |

Two related tables are generated for the same vehicles:

- **Maintenance records:** dated services since the retrofit whose costs add up exactly to the vehicle's maintenance cost. Types are EV-specific: Routine Service, Brake Service, Tyre Replacement, Battery Health Check, Charging Port Service, and breakdown repairs (Motor Repair, Controller Repair, Battery Cell Repair, Wiring and Connector Repair). Costs are weighted by type, so a battery cell repair costs more than a routine service.
- **Monthly trips:** up to six months per vehicle (only months after the retrofit), with distance, energy consumed (kWh) and energy cost (₹).

## Financial assumptions (₹)

| Assumption | Value |
|------------|-------|
| Electricity tariff | ₹9 per kWh |
| Scooter / Motorcycle fixed cost | ₹400 / ₹550 per month |
| Scooter / Motorcycle maintenance benchmark | ₹3,500 / ₹4,500 per year |
| Breakdown repair | about 35 % of the yearly benchmark each |
| Accident repair | about 60 % of the yearly benchmark each |

Monthly operating cost = distance × energy use × tariff + fixed cost. Yearly operating cost therefore comes to roughly ₹9,000 per vehicle on average. Prices are illustrative.

## How realistic relationships are built

| Relationship | Mechanism |
|--------------|-----------|
| Battery wears with use | Charge cycles = distance × energy use / battery size; fade grows with cycles, a per-vehicle battery-quality factor, the fast-charging share and calendar age |
| Longer retrofit history needs more maintenance | Yearly cost factor grows with retrofit age; costs per breakdown and accident are added |
| Older retrofits and older base vehicles break down more | Poisson breakdowns with mean `(0.10 + 0.50 × retrofit age) × utilization factor × (1 + 0.04 × vehicle age)` times a per-vehicle reliability factor |
| Motor and electrical systems degrade | Motor health falls with distance and breakdowns; electrical health falls with vehicle age, retrofit age and breakdowns |
| Condition follows wear | A wear value from ages, breakdown rate, accidents and battery loss is cut into Excellent / Good / Fair / Poor |
| Worn vehicles are more often overdue | Overdue probability rises with retrofit age and wear |
| Idle vehicles cost more per km | Operating cost has a fixed part, so low utilization raises cost per km |
| Distance is consistent | Monthly distance = capacity × utilization; total ≈ monthly × 12 × years since retrofit |

## Measured results (3,000 vehicles, seed 42)

| Measure | Value |
|---------|-------|
| Vehicles / maintenance records / trip rows | 3,000 / 12,643 / 17,718 |
| Scooters / motorcycles | 1,816 / 1,184 |
| Mean vehicle age / mean retrofit age | 7.2 years / 2.2 years |
| Mean battery / motor / electrical health | 91.3 % / 89.1 % / 88.8 % |
| Vehicles with battery health below 80 % / below 70 % | 258 / 88 |
| Mean energy use: scooter / motorcycle | 3.34 / 4.85 kWh/100 km |
| Correlation of charge cycles and battery health | −0.75 |
| Correlation of retrofit age and maintenance cost | 0.85 |
| Mean health / efficiency / risk score | 76.0 / 70.3 / 26.5 |
| Health: Good / Needs Attention / Critical | 1,726 / 1,154 / 120 |
| Risk: Low / Medium / High | 2,284 / 667 / 49 |
| Status: Operational / Maintenance Due / Needs Inspection / High Risk | 2,431 / 436 / 84 / 49 |
| Total maintenance cost | ₹3.48 crore (₹34,840,913) |

The generator parameters were adjusted so the fleet contains a useful number of vehicles in every status. These relationship checks run automatically in `tests/test_data_generator.py`.

## Limitations

The relationships are plausible but invented; they are **not calibrated to a real fleet**. Any model trained on this data would learn the generator's own rules, so results must not be presented as real-world performance.

## Storage and export

- Stored in SQLite (`data/rfie.db`) on first start if the database is empty.
- CSV: `data/synthetic_fleet_data.csv`, the Vehicles page's *Export CSV* button, `GET /api/data/export`, or `python backend/scripts/generate_dataset.py`. Money columns carry an `_inr` suffix (values in rupees).
