# Functional Specification

## 1. Purpose

RFIE gives fleet managers at ReVithalize, an EV-retrofitting startup that converts petrol two-wheelers to electric, a single dashboard for their fleet of electric motorcycles and scooters. It shows vehicle health (including battery, motor and electrical-system condition), energy efficiency, operational risk, maintenance needs, cost in ₹ and utilization, with automatic recommendations and alerts.

## 2. Users

**Fleet manager** (main user): reviews fleet condition, finds risky vehicles, acts on recommendations.

## 3. Functional requirements

| ID | Requirement | Where |
|----|-------------|-------|
| F1 | Calculate health, efficiency and risk scores (0–100) for every electric motorcycle and scooter | `backend/app/scoring` |
| F2 | Generate rule-based recommendations in four categories with priority, reason and action | `backend/app/recommendations` |
| F3 | Raise risk alerts when risk ≥ 70, with reason and recommended action | `recommendations/alerts.py` |
| F4 | Generate ~3,000 realistic synthetic EVs (motorcycles and scooters only); export CSV | `services/data_generator.py`, `/api/data/export` |
| F5 | Initialise the database, rebuild it if an older schema is found, and seed it automatically when empty | `database/initializer.py` |
| F6 | Overview page with 5 KPI cards, health and risk distribution, recent vehicles, recommendations, alerts | `OverviewPage.jsx` |
| F7 | Vehicles page: search by ID or type, filter by vehicle type (Motorcycle / Scooter) and status, paging, detail panel with battery, motor and electrical data | `VehiclesPage.jsx` |
| F8 | Recommendations page with category and priority filters and estimated annual saving in ₹ | `RecommendationsPage.jsx` |
| F9 | Risk Alerts page ordered by risk score | `AlertsPage.jsx` |
| F10 | Vehicle detail: score breakdown, facts, recommendations, alerts, maintenance history, monthly trips | `VehicleDetailPanel.jsx` |
| F11 | Show loading, empty and error states; offer to generate data if the database is empty | all pages |
| F12 | Show every money value in Indian rupees (₹) with Indian digit grouping (₹1,25,000) | `utils/format.js`, recommendation reasons |
| F13 | Track EV parameters: battery capacity and health, motor and electrical health, energy use (kWh/100 km), charge cycles, fast-charging share, retrofit date | scoring, database, API, dashboard |

## 4. User stories

- As a fleet manager I see total vehicles, average health, efficiency, high-risk count and maintenance cost at a glance.
- I search for `VEH-0123` or filter to "Scooter" and open the vehicle to see its battery health, energy use and *why* its scores are what they are.
- I filter recommendations by *Maintenance* and *High* priority to plan this week's workshop visits, for example battery replacement assessments.
- I see the estimated yearly saving in ₹ for cost recommendations.
- I open Risk Alerts to see which vehicles need urgent attention and what to do.

## 5. Dashboard metrics

| Metric | Definition |
|--------|-----------|
| Total Vehicles | Count of vehicle rows |
| Average Vehicle Health | Mean health score (the card also shows mean battery health) |
| Fleet Efficiency | Mean efficiency score |
| High-Risk Vehicles | Vehicles with risk ≥ 70 |
| Total Maintenance Cost | Sum of maintenance cost, shown in ₹ (lakh / crore) |

## 6. API behaviour

| Endpoint | Success | Errors |
|----------|---------|--------|
| `GET /api/health` | 200 `{status, database, vehicle_count}` | 503 if the database is unavailable |
| `GET /api/dashboard/summary` | 200 | 500 on database error |
| `GET /api/vehicles` | 200 paginated list; filters `search`, `vehicle_type`, `status` | 422 for invalid paging values |
| `GET /api/vehicles/{id}` | 200 detail (ID is case-insensitive) | 404 if unknown |
| `GET /api/recommendations` | 200 paginated list with `total_estimated_annual_saving_inr` | 422 invalid paging |
| `GET /api/alerts` | 200 paginated list | 422 invalid paging |
| `POST /api/data/generate` | 200 `{generated, vehicle_count, message}`; no overwrite unless `force=true` | 422 for `count` outside 100–10,000 |
| `GET /api/data/export` | 200 CSV download | – |

All responses are JSON (except the CSV export) with `detail` messages for errors. CORS allows the local frontend origins.

## 7. Non-functional requirements

- Runs locally on Windows 10/11 with Python and Node.js only; no cloud, Docker or API keys.
- Responsive layout down to phone width.
- Server-side paging keeps the 3,000-vehicle fleet fast.
- Source code has no explanatory comments; clarity comes from naming.
- All data is synthetic; EV benchmarks are illustrative, not measured ReVithalize specifications.

## 8. Out of scope

Real telematics or battery-management-system integration, authentication, trained ML models, multi-user roles, route optimisation, charging-station management.
