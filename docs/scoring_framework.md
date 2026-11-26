# Fleet Scoring Framework

RFIE calculates three scores for every electric motorcycle and scooter in the ReVithalize retrofit fleet. All scores are on a **0–100 scale**, computed with **explainable, rule-based formulas** (no machine learning). The code lives in separate modules under `backend/app/scoring/`.

| Score | Meaning | Module |
|-------|---------|--------|
| Vehicle Health Score | Higher = healthier | `health.py` |
| Fleet Efficiency Score | Higher = more efficient | `efficiency.py` |
| Operational Risk Score | Higher = **riskier** | `risk.py` |

> **Synthetic benchmarks.** The reference values below are illustrative figures chosen for an academic project. They are **not measured ReVithalize fleet specifications**, and ReVithalize did not supply them.

## How every score is built

1. Each input is converted to a **component score** between 0 and 100 (clamped).
2. Component scores are combined with a **weighted sum**. The weights add up to 1.
3. The result is rounded to one decimal place.

```
Score = Σ (weight_i × component_i)
```

## Reference values (illustrative)

Motorcycles and scooters are compared with **their own type's benchmark**. Benchmarks are in `backend/app/fleet_profiles.py`.

| Benchmark | Scooter | Motorcycle |
|-----------|--------:|-----------:|
| Typical annual distance | 9,000 km | 11,000 km |
| Battery capacity options | 1.8 / 2.4 / 3.0 / 3.6 kWh | 3.0 / 3.6 / 4.5 / 5.0 kWh |
| Energy consumption | 3.2 kWh/100 km | 4.6 kWh/100 km |
| Fixed monthly cost (insurance, connectivity) | ₹400 | ₹550 |
| Maintenance per year | ₹3,500 | ₹4,500 |
| Operating cost per km (derived) | ₹0.83 | ₹1.01 |

Operating cost per km = electricity (energy × ₹9 per kWh) + fixed monthly cost spread over a typical month (62 % of the monthly capacity).

Global constants: `MAX_VEHICLE_AGE_YEARS = 20`, `MAX_RETROFIT_YEARS = 8`, `WORST_BREAKDOWNS_PER_YEAR = 1.5`, `BATTERY_DEGRADATION_LIMIT_PCT = 40`.

- `vehicle age = reference year − manufacturing year` (age of the original two-wheeler)
- `retrofit age = years since the EV retrofit date`
- Per-year rates use `max(retrofit age, 1)`, because the electric system has only been in service since the retrofit.

Condition scores: Excellent = 100, Good = 75, Fair = 45, Poor = 15.
Maintenance status risk: On Schedule = 0, Due Soon = 50, Overdue = 100.

## A. Vehicle Health Score

| Component | Weight | Formula |
|-----------|-------:|---------|
| Battery health | 0.25 | `battery health %` |
| Motor health | 0.10 | `motor health %` |
| Electrical system health | 0.10 | `electrical health %` |
| Vehicle and retrofit age | 0.10 | `100 × (1 − 0.5 × vehicle age / 20 − 0.5 × retrofit age / 8)` |
| Maintenance history | 0.15 | `100 − 30 × (yearly maintenance cost / benchmark)` |
| Breakdown frequency | 0.20 | `100 × (1 − breakdowns per year / 1.5)` |
| Vehicle condition | 0.10 | condition score table |

The battery is the most valuable and fastest-ageing part of a retrofitted two-wheeler, so it carries the largest weight.

## B. Fleet Efficiency Score

| Component | Weight | Formula |
|-----------|-------:|---------|
| Utilization | 0.25 | `utilization %` |
| Distance travelled | 0.20 | `80 × monthly km / (annual km / 12)` |
| Energy efficiency | 0.30 | `80 × benchmark kWh/100 km / actual kWh/100 km` |
| Operating cost per km | 0.25 | `80 × benchmark ₹/km / actual ₹/km` |

A vehicle that exactly matches its benchmark scores **80** on a benchmark-based component; doing better scores up to 100. `cost per km = monthly operating cost / monthly distance`.

## C. Operational Risk Score

| Component | Weight | Formula |
|-----------|-------:|---------|
| Repeated breakdowns | 0.25 | `100 × breakdowns per year / 1.5` |
| Maintenance overdue status | 0.20 | status table (0 / 50 / 100) |
| Battery degradation | 0.25 | `100 × (100 − battery health %) / 40` |
| Operational incidents | 0.15 | `25 × accidents` |
| Critical condition | 0.15 | `max(100 − condition score, 100 − weakest of motor and electrical health)` |

## Status labels

| Label | Rule |
|-------|------|
| Health status | Good ≥ 75 · Needs Attention 50–74.9 · Critical < 50 |
| Risk level | Low < 40 · Medium 40–69.9 · High ≥ 70 |
| Vehicle status | High Risk (risk ≥ 70) → Needs Inspection (health < 50) → Maintenance Due (overdue) → Operational |

## Worked example

An electric scooter built in 2018 (age 8) and retrofitted on 25 Nov 2023 (3.0 years ago): 27,000 km since retrofit, 750 km per month, 2.4 kWh battery at 88 % health, motor 90 %, electrical system 86 %, 3.6 kWh/100 km, 3 breakdowns, 1 accident, 60 % utilization, maintenance *Due Soon*, condition *Fair*, maintenance cost ₹12,000, operating cost ₹700 per month.

**Health**

| Component | Score | × Weight | = |
|-----------|------:|---------:|--:|
| Battery health | 88.0 | 0.25 | 22.00 |
| Motor health | 90.0 | 0.10 | 9.00 |
| Electrical system | 86.0 | 0.10 | 8.60 |
| Age: 100 × (1 − 0.5 × 8/20 − 0.5 × 3.0/8) | 61.2 | 0.10 | 6.13 |
| Maintenance: ₹3,999 per year / ₹3,500 = 1.14 → 100 − 30 × 1.14 | 65.7 | 0.15 | 9.86 |
| Breakdowns: 1.0 per year → 100 × (1 − 1.0 / 1.5) | 33.3 | 0.20 | 6.67 |
| Condition: Fair | 45.0 | 0.10 | 4.50 |
| **Health score** | | | **66.8** |

**Efficiency:** utilization 60 × 0.25 = 15.0; distance 80.0 × 0.20 = 16.0; energy (3.2 / 3.6) 71.1 × 0.30 = 21.3; cost (₹0.83 / ₹0.93 per km) 70.8 × 0.25 = 17.7 → **70.0**

**Risk:** breakdowns 66.7 × 0.25 = 16.7; maintenance 50 × 0.20 = 10.0; battery (12 % loss) 30.0 × 0.25 = 7.5; accidents 25 × 0.15 = 3.75; condition 55 × 0.15 = 8.25 → **46.2** (Medium)

These exact numbers are asserted in `tests/test_scoring.py`.

## Why this design

- **Transparent:** every score can be explained term by term; the dashboard's vehicle panel shows the component scores.
- **EV-specific:** battery, motor and electrical-system condition drive health and risk.
- **Fair across vehicle types:** each type is judged against its own benchmark.
- **Easy to tune:** all weights and constants are named values at the top of each module.
