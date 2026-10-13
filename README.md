# FarmShield AI

**Predict crop stress before it becomes crop damage.**

FarmShield AI is a development-stage crop-risk assessment web application. It provides an authenticated interface for managing farms and crops and requesting a machine-learning risk assessment for a selected crop.

> **Important — demo and research prototype:** The current risk pipeline uses placeholder environmental inputs and a Random Forest model trained on synthetic development data. Its outputs are not validated real-world risk estimates, agronomic diagnoses, or instructions for making farming decisions. Weather and satellite integrations should not be described as live unless separately implemented and verified.

## Table of contents

- [Current capabilities](#current-capabilities)
- [Technology stack](#technology-stack)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Run locally on Windows](#run-locally-on-windows)
- [Configuration and data storage](#configuration-and-data-storage)
- [API routes](#api-routes)
- [Machine-learning pipeline](#machine-learning-pipeline)
- [Demo limitations and responsible use](#demo-limitations-and-responsible-use)
- [Troubleshooting](#troubleshooting)
- [Suggested next steps](#suggested-next-steps)

## Current capabilities

The currently verified development workflow includes:

- Login using an existing registered account.
- Retrieve the authenticated user's profile.
- Create and list farms.
- Create and list crops for a farm.
- Request a crop-risk prediction for a selected farm and crop.
- Display the risk result and returned explanation in the React UI.
- Clearly label predictions as development/demo results.

The application has been tested locally with the frontend on Vite port `5174` and the backend on `127.0.0.1:8000`. Vite may choose another port if the default port is occupied.

Features such as live weather ingestion, satellite-derived NDVI, production notifications, expert consultations, or validated agronomic recommendations are **not claimed as implemented by this README**.

## Technology stack

| Layer | Technology | Role |
|---|---|---|
| Frontend | React, Vite | Browser UI and user interactions |
| API | FastAPI, Uvicorn | HTTP endpoints and application logic |
| Persistence | SQLAlchemy, SQLite by default | Relational data access and local development storage |
| Authentication | Bearer token / JWT helpers | Authenticated API requests |
| Machine learning | scikit-learn Random Forest | Development crop-risk prediction |
| Model artifact | Joblib-loaded model | Loads the saved model file |

## Project structure

The following structure reflects the files and locations used by the current local setup. Additional files may exist in the repository.

```text
farmshield-ai-phase1/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── auth.py
│       ├── database.py
│       ├── main.py
│       ├── ml_service.py
│       ├── models.py
│       └── schemas.py
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   └── index.html
├── ml/
│   └── models/
│       └── farmshield_early_warning_random_forest.joblib
└── venv/                       # Local Python virtual environment
```

`venv/` is local setup state and should generally not be committed to version control.

## Prerequisites

Install the following on Windows:

- Python compatible with the project's installed dependencies.
- Node.js and npm.
- PowerShell.
- The project files, including the saved model artifact at the path expected by `ml_service.py`.

The existing development environment was set up with Python 3.13 and installed packages including FastAPI, Uvicorn, SQLAlchemy, NumPy, pandas, scikit-learn, XGBoost, and Joblib. Exact package versions should be recorded in dependency files for reproducible installation; do not assume these packages alone form a complete pinned requirements list.

## Run locally on Windows

Run each server in a separate PowerShell terminal. Keep both terminals open while using the app.

### 1. Start the backend

```powershell
Set-Location "D:\farmshield-ai-phase1\backend"
& "D:\farmshield-ai-phase1\venv\Scripts\Activate.ps1"
$env:PYTHONPATH = "D:\farmshield-ai-phase1"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Expected local URLs:

- API root: <http://127.0.0.1:8000/>
- Health endpoint: <http://127.0.0.1:8000/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>

If PowerShell blocks virtual-environment activation, you can run Uvicorn directly without activating the environment:

```powershell
Set-Location "D:\farmshield-ai-phase1\backend"
$env:PYTHONPATH = "D:\farmshield-ai-phase1"
& "D:\farmshield-ai-phase1\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Start the frontend

Open a second PowerShell terminal:

```powershell
Set-Location "D:\farmshield-ai-phase1\frontend"
npm run dev
```

Open the URL printed by Vite, commonly <http://localhost:5173/> or <http://localhost:5174/> if the default port is occupied.

### 3. Sign in and test the workflow

1. Open the Vite URL.
2. Sign in with an account already registered in the local database.
3. Confirm that farms and crops load.
4. Select a farm and crop.
5. Run the crop-risk assessment.
6. Verify the result includes its risk category and model explanation.
7. Confirm the development/demo-data disclaimer remains visible.

Do not put real passwords, access tokens, or secret keys in this README or commit them to source control.

## Configuration and data storage

### API URL

The current frontend uses the API base URL:

```js
const API = "http://127.0.0.1:8000";
```

If the backend address or port changes, update this setting in `frontend/src/main.jsx` or replace it with an environment-based configuration appropriate for the project.

### CORS

The backend must allow the exact origin used by the browser. For example, if Vite is running at `http://localhost:5174`, the backend CORS configuration must allow that origin. `localhost` and `127.0.0.1` are different origins.

Keep the CORS allow-list limited to origins needed for local development or the deployed frontend.

### Database

The current SQLAlchemy configuration uses SQLite by default:

```text
sqlite:///./farmshield.db
```

Because this is a relative path, the database file is resolved from the backend process's working directory. The application creates database tables on startup through SQLAlchemy metadata initialization. Keep a backup of the database if you need to preserve demo accounts, farms, and crops.

### Model artifact

The ML service loads the saved Random Forest artifact from:

```text
ml/models/farmshield_early_warning_random_forest.joblib
```

Run the backend with the project root in `PYTHONPATH` as shown above so imports and the model path resolve as expected.

## API routes

These routes are defined in the current FastAPI application. Use `http://127.0.0.1:8000/docs` as the authoritative interactive reference for request schemas and response fields.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Root/status response |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/auth/register` | Register a user |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain a token |
| `GET` | `/api/v1/auth/me` | Retrieve the authenticated user |
| `POST` | `/api/v1/farms` | Create a farm |
| `GET` | `/api/v1/farms` | List farms for the authenticated user |
| `GET` | `/api/v1/farms/{farm_id}` | Retrieve a farm |
| `POST` | `/api/v1/farms/{farm_id}/crops` | Create a crop for a farm |
| `GET` | `/api/v1/farms/{farm_id}/crops` | List crops for a farm |
| `POST` | `/api/v1/farms/{farm_id}/crops/{crop_id}/risk` | Generate a crop-risk assessment |
| `GET` | `/api/v1/dashboard` | Retrieve dashboard summary data |

Authenticated routes use the bearer token returned by login. For exact request bodies, field requirements, and response shapes, consult Swagger UI at `/docs`; this README intentionally avoids inventing payload schemas.

## Machine-learning pipeline

The current ML service loads a saved Random Forest model and prepares features for a prediction. The development feature set includes:

- Temperature
- Humidity
- Rainfall
- Soil moisture
- Soil pH
- Wind speed
- NDVI
- Crop age
- Crop growth stage

The service normalizes named growth stages such as seedling, vegetative, flowering/fruiting, and maturity into numeric categories for the model. The current risk endpoint supplies placeholder environmental values, so the resulting output demonstrates the application pipeline rather than a real measurement of current farm conditions.

The API/UI can return a risk probability, risk level, primary and secondary risk factors, confidence-related output, model name/version, and explanation. Interpret these fields in the context of the prototype. In particular, a model confidence score is not a guarantee that a prediction is correct.

### Model evaluation

Any metrics produced during development must be explicitly described as evaluation on synthetic development data. They must not be presented as evidence of performance on real farms. Before real-world use, the model requires suitable field data, documented labels and methodology, held-out evaluation, calibration/uncertainty analysis, validation across crop types and growing conditions, and review by qualified agricultural specialists.

## Demo limitations and responsible use

- **Placeholder environmental readings:** The current risk endpoint uses hard-coded demo values rather than verified live weather or sensor measurements.
- **Synthetic training data:** The Random Forest model was trained on synthetic development data. Results may not generalize to real farms.
- **Not a diagnosis:** Risk categories and explanations are prototype outputs, not professional agronomic advice.
- **No guaranteed outcomes:** Do not use these results alone to make irrigation, pesticide, fertilizer, or crop-loss decisions.
- **Integrations must be verified:** Do not describe weather services, satellite imagery, alerts, expert consultations, or other integrations as live unless implemented and tested.
- **Development security:** The project uses local development settings. Before deployment, configure strong secret keys, secure token handling, HTTPS, restricted CORS, input validation, appropriate logging, and a production database strategy.

## Troubleshooting

### `Failed to fetch` on login

1. Check the backend health endpoint:

   ```powershell
   Invoke-RestMethod "http://127.0.0.1:8000/health"
   ```

2. If the request fails, start Uvicorn using the backend command above.
3. Confirm the frontend API base URL matches the backend host and port.
4. Check CORS for the exact Vite origin. If Vite uses port `5174`, allow `http://localhost:5174` and, if used, `http://127.0.0.1:5174`.
5. Open browser Developer Tools → Network/Console and inspect the failed request. Do not share bearer tokens in screenshots or logs.

### `Attribute "app" not found` or Uvicorn import errors

Run Uvicorn from the `backend` directory and set the project root as `PYTHONPATH`:

```powershell
Set-Location "D:\farmshield-ai-phase1\backend"
$env:PYTHONPATH = "D:\farmshield-ai-phase1"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Confirm that `backend\app\main.py` defines the FastAPI application.

### Model file not found

Confirm this file exists:

```text
D:\farmshield-ai-phase1\ml\models\farmshield_early_warning_random_forest.joblib
```

Also confirm `PYTHONPATH` points to the project root and that `ml_service.py` uses the same model path.

### Growth-stage conversion error

The ML service expects normalized numeric growth-stage categories. Ensure the current `normalize_growth_stage()` implementation is present in `backend\app\ml_service.py` and that the crop's growth-stage text is handled by the normalization function.

### Farms or crops do not load

- Confirm login succeeded and the browser has a valid session.
- Check the Network tab for `401`, `403`, or `500` responses.
- Verify the selected farm ID is valid and belongs to the authenticated account.
- Inspect the backend terminal for the corresponding traceback.

### Port 8000 is already in use

Stop the process using port 8000, or start the backend on a different port and update the frontend API base URL and CORS configuration to match. Both sides must use the same backend address.

### Vite starts on port 5174 instead of 5173

This normally means port 5173 was occupied. Use the URL Vite prints and ensure that exact origin is allowed by backend CORS.

### Browser shows stale UI

Refresh the page. If necessary, stop and restart Vite. Avoid deleting the database or clearing local storage unless you understand the impact on the saved session and demo records.

## Suggested next steps

1. Add pinned backend dependencies and document the frontend Node version.
2. Move local configuration to environment variables and remove development-only secrets.
3. Add automated API and frontend tests.
4. Store and display actual prediction history if that feature is implemented.
5. Integrate verified weather/sensor/satellite data with clear source and timestamp metadata.
6. Evaluate the model using representative, independently collected agricultural data and expert review before making real-world claims.

---

## License

No license is specified here. Add a license only after choosing the terms under which this project may be used, modified, and distributed.
