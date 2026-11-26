# System Design (Phase 5)

## 1. Overview

```
Browser (React + Vite, port 5173)
        │  /api/*  (Vite dev proxy)
        ▼
FastAPI backend (uvicorn, port 8000)
        │  SQLAlchemy
        ▼
SQLite file  data/rfie.db
```

The browser never talks to the database. It calls REST endpoints; Vite forwards `/api` requests to the backend, and the backend also enables CORS for `localhost:5173` / `127.0.0.1:5173`.

## 2. Backend architecture

| Package | Responsibility |
|---------|---------------|
| `api/routes.py` | HTTP layer: validates query parameters, calls services, returns Pydantic models |
| `models/tables.py` | SQLAlchemy ORM tables |
| `models/schemas.py` | Pydantic response models (also drive `/docs`) |
| `database/` | Engine, sessions, `initialize_database()` |
| `scoring/` | Health, efficiency, risk formulas; status labels |
| `recommendations/` | Rules, alert builder, engine |
| `services/` | Data generator, dataset builder, fleet loader, dashboard queries, vehicle detail, CSV export |
| `fleet_profiles.py`, `config.py` | Benchmarks and settings |

Scoring, recommendation and generator code is plain Python/Pandas with **no web or database dependency**, so it can be unit-tested directly.

## 3. Start-up and data flow

1. `uvicorn` starts `app.main:app`; the lifespan handler calls `initialize_database()`.
2. Tables are created if missing. If `vehicles` is empty the loader runs:
   1. generate 3,000 raw electric motorcycles and scooters (Pandas) →
   2. score each vehicle (health, efficiency, risk, statuses) →
   3. run the recommendation engine and alert builder →
   4. generate maintenance records and monthly trips →
   5. bulk-insert everything in one transaction.
3. The dashboard requests data; the backend reads **stored** scores and recommendations, so requests are fast.

```
Request: Dashboard -> GET /api/dashboard/summary -> routes -> services.dashboard
         -> SQL (COUNT, AVG, SUM, GROUP BY, latest rows) -> Pydantic -> JSON -> React
```

## 4. Database structure

```
vehicles (PK vehicle_id)
   ├──< maintenance_records (vehicle_id FK)
   ├──< trips               (vehicle_id FK)
   ├──< recommendations     (vehicle_id FK)
   └──< risk_alerts         (vehicle_id FK)
```

| Table | Key columns |
|-------|-------------|
| `vehicles` | vehicle_id, vehicle_type (Motorcycle / Scooter), manufacturing_year, retrofit_date, total and monthly distance, battery_capacity_kwh, battery_health_pct, motor_health_pct, electrical_health_pct, energy_consumption_kwh_per_100km, charge_cycles, fast_charge_pct, maintenance_cost_inr, breakdowns, accidents, utilization_pct, maintenance_status, vehicle_condition, operating_cost_inr, health_score, efficiency_score, risk_score, health_status, risk_level, status |
| `maintenance_records` | id, vehicle_id, service_date, service_type, cost_inr, is_breakdown_repair |
| `trips` | id, vehicle_id, trip_month, trips_count, distance_km, energy_consumed_kwh, energy_cost_inr |
| `recommendations` | id, vehicle_id, category, priority, title, reason, suggested_action, estimated_annual_saving_inr, created_at |
| `risk_alerts` | id, vehicle_id, risk_score, risk_level, reason, recommended_action, created_at |

SQLite foreign-key enforcement is switched on for every connection.

### Schema version and safe re-initialisation

`config.SCHEMA_VERSION` is stored in SQLite's `PRAGMA user_version`. On start-up `prepare_schema()` compares it with the stored value. If they differ (a new database has version 0, and a database created by the earlier petrol/USD version of the project also has 0), the five RFIE tables are dropped and recreated with the current schema, and the version is written. The empty tables are then filled with the synthetic EV fleet. A database that already has the current version is left untouched. This prevents schema errors after upgrading, with no manual database steps.

Scores are stored on `vehicles` (denormalised on purpose) so filtering and sorting happen in SQL.

## 5. Insight generation logic

1. **Scores** from formulas (`docs/scoring_framework.md`).
2. **Rules** compare scores and ratios to thresholds (`docs/recommendation_engine.md`).
3. **Alerts** explain high risk with the contributing factors.
4. **Dashboard aggregates** (averages, counts per status) are computed with SQL on demand.

## 6. Frontend architecture

| Folder | Content |
|--------|---------|
| `pages/` | Overview, Vehicles, Recommendations, Risk Alerts |
| `components/` | Sidebar, KPI card, tables, badges, score bars, detail panel, state messages |
| `services/api.js` | The only place that calls `fetch`; turns failures into readable messages |
| `hooks/` | `useApi` (loading / error / data / reload) and `useDebouncedValue` for search |
| `utils/` | Formatting, colour tones, labels |

Navigation is kept in React state in `App.jsx`; the vehicle detail panel opens from any page by vehicle ID.

## 6.1 How the dashboard obtains data

Each page calls a function in `services/api.js` through `useApi`. The hook returns `loading`, `error` and `data`, and the page renders a spinner, an error message with *Try again*, an empty state, or the data. Search text is debounced (300 ms) and the page number resets whenever a filter changes.

## 7. Error handling

- Query validation → HTTP 422; unknown vehicle → 404; database errors → JSON `{"detail": ...}` with 500/503.
- Frontend shows *Cannot reach the RFIE backend* when the API is down and an *API offline* indicator in the sidebar.
- Empty database → Overview offers *Generate synthetic data*, which calls `POST /api/data/generate`.

## 8. Design decisions

| Decision | Reason |
|----------|--------|
| Rule-based scoring | Explainable, no training data needed |
| `vehicle_id` as primary key | Natural key; simplifies bulk inserts and foreign keys |
| Precomputed scores | Fast dashboard queries |
| Vite proxy | Avoids browser CORS problems during development |
| `_inr` suffix on money fields | The currency is explicit in the schema, the API and the CSV |
| Schema version check | An old database can never cause schema errors |
| Server-side paging | 3,000 rows would be slow to render at once |
