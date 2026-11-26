# FraudLink — Fraud-Linked Exchange Clustering

A local financial investigation console with a FastAPI analysis service, MongoDB persistence, and an independent Vite/React frontend.

## Quick start

1. Install Docker Desktop or Docker Engine with Compose. Start Docker.
2. Extract the complete archive. Open a terminal in the directory containing `compose.yaml`.
3. Run `docker compose up --build -d`. The first build downloads the runtime images and dependencies.
4. Run `docker compose logs -f api` and wait for “Application startup complete”. Open **http://localhost:8080**. API documentation is at **http://localhost:8000/docs**.
5. The first startup analyzes `datasets/demo.csv`. Subsequent startups reuse the active MongoDB run. For a dependency-free look at the graph rule’s actual sample results, open **OPEN-DEMO.html** in a browser.

Stop the services with `docker compose down`. Named volumes preserve cases, runs and models across restarts.

## Demonstrate an investigation

1. Open **Overview** to review risk counts, the exchange graph, recent alerts, trends and risk distribution.
2. Choose **Import dataset**, drop the supplied demo CSV and wait for the completed analysis. Imports replace the active workspace dataset. Existing cases remain linked to their evidence.
3. In **Transactions**, filter by Critical risk. Open a transaction to see transfer endpoints, UTC time, anomaly score and explanations.
4. In **Exchange network**, select a cluster. Click an account for risk and volume, or an edge to see its transfers. Search an account to highlight its neighbors. Select source and destination to trace a directed path.
5. Choose **Create investigation** on an account. Add a title, save, select transactions from its timeline, enter notes, set In review, and save. Export the saved case as a PDF.
6. Open **Analytics & reports**, select a reporting interval and download CSV or PDF. **Alert feed → Replay alerts** simulates alerts from the dataset.
7. Run `python tests/integration.py` against an isolated demo stack to exercise import, rescoring, clustering, case updates, conflict detection and exports. This test creates an investigation and publishes new runs.

## Development without Docker Compose

Requires Python 3.12, Node.js 22, npm and a running MongoDB 7 server. Run each command from the project root except where indicated.

1. Create an environment with `python -m venv .venv`. Activate with `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux.
2. Run `python -m pip install -r backend/requirements.txt`.
3. Set `MONGO_URI` if MongoDB is outside localhost:27017. Optional settings are `MODEL_DIR` and comma-separated `CORS_ORIGINS`.
4. Run `python -m uvicorn backend.main:app --reload`.
5. In another terminal, run `cd frontend`, `npm install`, then `npm run dev`. Open the local Vite URL. Vite proxies /api to port 8000. For a separate API origin, set `VITE_API_BASE` before building and configure CORS on FastAPI.
6. Run `npm run build` inside frontend for the production bundle.

## Input contract

| Column | Requirement |
| --- | --- |
| id | Unique transaction ID using letters, digits, hyphens or underscores |
| sender, receiver | Account identifiers of 1–64 characters using the same alphabet |
| amount | Positive USD amount, maximum 1 trillion |
| timestamp | ISO 8601 date/time. Missing timezone means UTC |
| label | Optional ground truth. 1 = fraud, 0 = ordinary, blank = unknown |

The UTF-8 CSV must contain 5–10,000 records and fit within 4 MB. Missing identity, monetary or temporal fields produce row-specific validation errors. Blank labels are excluded from evaluation.

## Verification

Run the dependency-light tests from the project root:

```sh
python -m unittest discover -s tests -p test_core.py -v
python documentation/build_walkthrough.py
```

The bundled HTML walkthrough is generated directly from sample transactions and the chronological rule used by the API. The reporting UI displays uncalibrated anomaly scores. Labeled precision and recall describe this dataset. Read **documentation/ARCHITECTURE.md** for thresholds, graph semantics, storage behavior and deployment boundaries.

## API resources

GET /api/dashboard/stats, /api/transactions, /api/transactions/{id}, /api/accounts, /api/alerts, /api/clusters, /api/clusters/{id}, /api/network/graph, /api/cases, /api/cases/{id}, /api/cases/{id}/pdf, /api/reports and /api/reports/export.

POST /api/transactions/upload (multipart file), /api/fraud/detect, /api/clusters/generate and /api/cases. PATCH /api/cases/{id} saves notes, status and evidence with optimistic revision checks. The OpenAPI schema at /openapi.json documents all parameters.

