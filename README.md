# ReVithalize Fleet Intelligence Engine (RFIE) – EV Edition

## 1. Project overview

ReVithalize is an EV-retrofitting startup that converts petrol-powered two-wheelers into electric vehicles. RFIE is a fleet intelligence dashboard for the resulting **electric motorcycles and electric scooters**. It turns vehicle data into **scores, recommendations and risk alerts** that a fleet manager can act on. It is an academic / internship demonstration project covering five phases: scoring framework, recommendation engine, synthetic dataset, AI service architecture, and dashboard.

> **All data is synthetic.** Vehicle specifications, energy figures, costs and prices are illustrative benchmarks created for this project. They are **not measured ReVithalize fleet specifications** and were not supplied by the company.

What it does:

- **Scores every vehicle (0–100):** Vehicle Health (battery, motor, electrical system, maintenance, breakdowns, age and retrofit age), Fleet Efficiency (energy use, distance, cost per km, utilization), Operational Risk (battery degradation, breakdowns, overdue maintenance, incidents, critical condition).
- **Generates recommendations** in four categories: Cost Reduction, Maintenance, Utilization, Risk Management, with estimated yearly savings in ₹ for cost items.
- **Raises risk alerts** for vehicles with a risk score of 70 or more.
- **Generates 3,000 synthetic EVs** (Motorcycle and Scooter only) with battery capacity and health, motor and electrical health, energy use in kWh/100 km, charge cycles, retrofit date and costs in ₹ – stored in SQLite together with maintenance records and monthly trips.
- **Shows everything in a dashboard:** Overview, Vehicles (searchable, filterable, detail panel), Recommendations, Risk Alerts. All money is shown in Indian rupees, e.g. ₹1,25,000.

## 2. Technology stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, HTML, CSS, JavaScript |
| Backend | Python, FastAPI, Pandas, NumPy |
| Database | SQLite via SQLAlchemy (created automatically) |

No Docker, cloud service or API key is needed.

## Requirements

- Windows 10 / 11 (also works on macOS / Linux with the manual commands)
- **Python 3.10 or newer** – https://www.python.org/downloads/ (tick *Add python.exe to PATH*)
- **Node.js 18 or newer (LTS)** – https://nodejs.org/

```
python --version
node --version
```

## Quick start (Windows)

1. Extract `RFIE_Updated_EV_Project.zip`.
2. Double-click **`start_project.bat`**.

On the first run it creates a virtual environment, installs the backend and frontend dependencies (a few minutes), starts both servers in separate windows and opens the browser.

## 3. Install backend dependencies

Open the extracted `RFIE` folder in VS Code, then **Terminal → New Terminal**:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

If PowerShell blocks `venv\Scripts\activate`, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use Command Prompt.

## 4. Install frontend dependencies

In a second terminal:

```
cd frontend
npm install
```

## 5. Start the backend

```
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On startup the backend creates `data/rfie.db`, creates all tables and – because the database is empty – generates and stores 3,000 electric motorcycles and scooters with their scores, recommendations and alerts. Wait for `Application startup complete.`

## 6. Start the frontend

```
cd frontend
npm run dev
```

## 7. Access the dashboard

http://localhost:5173

## 8. Access the FastAPI Swagger documentation

http://127.0.0.1:8000/docs (health check: http://127.0.0.1:8000/api/health)

## 9. Regenerate the synthetic data

The database fills itself on first start. To rebuild it:

- **Delete and restart:** stop the backend, delete `data/rfie.db`, start the backend again; or
- **Swagger:** open `POST /api/data/generate`, set `force` to `true` (and optionally `count` and `seed`) and execute; or
- **CSV only:** `cd backend` then `python scripts/generate_dataset.py --count 3000` writes `data/synthetic_fleet_data.csv`.

**Upgrading from the earlier petrol/USD version:** nothing to do. The database stores a schema version; when the backend finds an older database it drops and recreates the five RFIE tables and refills them with EV data automatically. The ZIP contains no database file.

**Export:** click *Export CSV* on the Vehicles page, or open http://127.0.0.1:8000/api/data/export. Money columns end in `_inr` (values in rupees).

## 10. Run the tests

From the `RFIE` folder with the backend virtual environment active:

```
pip install -r backend/requirements.txt
pytest
```

Without pytest the same tests run with `python -m unittest discover -s tests`.

| Test file | Covers |
|-----------|--------|
| `tests/test_scoring.py` | EV formulas (hand-calculated example), weights, 0–100 range, battery / motor / energy behaviour, status thresholds |
| `tests/test_recommendations.py` | Every rule incl. battery rules, ₹ savings, Indian number formatting, alerts, no duplicate categories |
| `tests/test_data_generator.py` | Only Motorcycle / Scooter, EV fields, charge-cycle consistency, retrofit dates, realistic relationships, ₹ plausibility, CSV |
| `tests/test_database_init.py` | Old-schema database is rebuilt, current database left untouched |
| `tests/test_api.py` | Every API endpoint, filters, paging, 404 / 422 errors, EV fields, export |

## API summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | API and database status |
| GET | `/api/dashboard/summary` | KPIs, distributions, recent items |
| GET | `/api/vehicles` | Vehicles – `search`, `vehicle_type`, `status`, `page`, `page_size` |
| GET | `/api/vehicles/{vehicle_id}` | One vehicle with score breakdown, history, recommendations |
| GET | `/api/recommendations` | Recommendations – `category`, `priority`, paging; includes total estimated saving in ₹ |
| GET | `/api/alerts` | High-risk alerts, highest risk first |
| POST | `/api/data/generate` | Generate synthetic data (`count`, `seed`, `force`) |
| GET | `/api/data/export` | Download the dataset as CSV |

## Project structure

```
RFIE/
├── start_project.bat          one-click Windows launcher
├── backend/
│   ├── requirements.txt
│   ├── scripts/generate_dataset.py
│   └── app/
│       ├── main.py            FastAPI app, CORS, start-up initialisation
│       ├── config.py          paths, seed, reference date, schema version
│       ├── fleet_profiles.py  Motorcycle / Scooter benchmarks, electricity tariff
│       ├── api/               REST routes
│       ├── database/          engine, sessions, schema check and seeding
│       ├── models/            SQLAlchemy tables and Pydantic schemas
│       ├── scoring/           health, efficiency, risk (separate modules)
│       ├── recommendations/   rules, alerts, engine, ₹ formatting
│       └── services/          data generator, loader, dashboard queries
├── frontend/                  React + Vite dashboard (pages, components, services, hooks)
├── data/synthetic_fleet_data.csv
├── docs/                      scoring, recommendations, dataset, AI architecture, ...
├── presentation/RFIE_Presentation.pptx
└── tests/
```

## Documentation

| Document | Contents |
|----------|----------|
| `docs/scoring_framework.md` | The three EV-based formulas, weights, worked example |
| `docs/recommendation_engine.md` | Rules, thresholds, priorities, ₹ saving estimates, alerts |
| `docs/dataset_documentation.md` | Fields, EV assumptions, financial assumptions, statistics |
| `docs/ai_architecture.md` | Proposed AI services and architecture diagram |
| `docs/model_selection_report.md` | Why each future model was chosen |
| `docs/functional_specification.md` | Features, user stories, API behaviour |
| `docs/system_design.md` | Data flow, database structure, schema versioning, backend architecture |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `'python' is not recognized` | Reinstall Python and tick *Add python.exe to PATH*, then open a new terminal. |
| `'npm' is not recognized` | Install Node.js LTS and open a new terminal. |
| Dashboard shows *Cannot reach the RFIE backend* | The backend is not running. Start it and check http://127.0.0.1:8000/api/health. |
| `Port 8000 is already in use` | Close the other program, or start with `--port 8001` and change the proxy target in `frontend/vite.config.js`. |
| `Port 5173 is already in use` | Close the other Vite window (the port is fixed so the URL stays predictable). |
| `pip install` fails building pandas / numpy | Upgrade pip (`python -m pip install --upgrade pip`) and use a 64-bit Python 3.10–3.13. |
| Empty dashboard after errors | Stop the backend, delete `data/rfie.db`, start again. |
| `venv\Scripts\activate` blocked in PowerShell | Use Command Prompt, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| Backend start-up takes several seconds | Normal on the first run: it is generating and scoring 3,000 vehicles. |
| `npm install` is slow or fails | Check the internet connection; delete `frontend/node_modules` and retry. |

## Scope and honesty note

The scoring and recommendation logic is **rule-based and explainable**. No machine-learning model is trained or deployed in this project; `docs/ai_architecture.md` and `docs/model_selection_report.md` describe *proposed* future models only. All data, specifications and prices are **synthetic illustrations**, not ReVithalize measurements.
