# NexusChain — Supply Chain Intelligence System

LIVE DEMO : https://nexuschain-supply-chain-intelligence.streamlit.app/

An end-to-end supply-chain intelligence platform built on reproducible synthetic ERP data. It combines PostgreSQL, advanced SQL, Python data engineering, leakage-safe XGBoost models, SHAP explanations, a Streamlit application, automated tests, Docker and free-tier deployment.

## Project goal

Answer two operational questions:

1. **Which supplier orders are likely to arrive late?**
2. **Which parts are likely to reach or fall below safety stock within the next 14 days?**

The system also exposes multi-level BOM dependencies, supplier performance and inventory analytics.

## Architecture

```text
Python/Faker ERP simulation
        ↓
Validation
        ↓
PostgreSQL
        ↓
┌───────────────┬────────────────┬────────────────┐
│ Recursive BOM │ Supplier SQL   │ Inventory SQL  │
└───────────────┴────────────────┴────────────────┘
        ↓
Leakage-safe feature engineering
        ↓
┌─────────────────────┬──────────────────────┐
│ XGBoost delay model │ XGBoost risk model   │
└─────────────────────┴──────────────────────┘
        ↓
SHAP explanations + serialized inference
        ↓
Streamlit dashboard
        ↓
Docker / Streamlit Community Cloud
```

## What makes the data useful

The core dataset is generated locally with Python/Faker rather than downloaded from a single Kaggle table. This is deliberate: the project needs a coherent relational ERP environment linking suppliers, parts, a five-level BOM, purchase orders, inventory and sales. The generator is deterministic (`RANDOM_SEED=42`) and produces relationships rather than independent random rows.

Default scale:

- 60 suppliers
- 600 parts
- 1,200 BOM relationships
- 55,000 purchase orders
- 110,000 inventory records
- 55,000 sales orders

That is roughly **222k business records** and about **10 MB of CSV data** before PostgreSQL indexing.

## Core data model

- `suppliers` — supplier identity, country, region and category
- `parts` — raw materials through finished goods, cost, lead time and safety stock
- `bom` — parent/child component relationships
- `purchase_orders` — promised vs actual delivery, quantity and price
- `inventory` — daily stock movement and closing stock
- `sales_orders` — demand events for finished goods

## Advanced SQL

The project intentionally demonstrates more than basic CRUD SQL:

- Recursive CTE for multi-level BOM traversal
- Cumulative quantity and cost rollups
- Supplier on-time delivery rate
- Delay statistics and reliability percentile
- Window functions for time-series demand analysis
- Inventory turnover / safety-stock analytics
- Indexed relational tables and reusable views

## ML design

### Supplier-delay model

Target: `delay_flag` for delivered purchase orders.

Features are constructed from information available before the actual delivery date, including historical supplier behavior, lead time, order quantity/value and calendar information. The pipeline compares Logistic Regression against XGBoost and reports precision, recall, F1, ROC-AUC, PR-AUC and a confusion matrix.

### Stockout-risk model

Target: `stockout_risk_within_14d`, defined as reaching or falling below the part's safety-stock level within the next 14 days. Actual zero-stock days are tracked separately in the inventory analytics.

Features include current stock, safety stock, lead time, lagged demand statistics, recent receipts, days of cover and safety-stock gap. The target is future-looking while features use current/past information.

### Explainability

SHAP is used to show the main factors behind an individual prediction. Models are serialized with `joblib` and loaded for inference; the dashboard does not retrain models at startup.

## Repository

```text
supply-chain-intelligence/
├── app/                 Streamlit dashboard + six pages
├── analytics/           SQL-backed data access
├── database/            schema, views and analytical SQL
├── ml/                  features, training, evaluation, SHAP
├── services/            business/prediction service layer
├── scripts/             generation, validation, loading, pipeline
├── tests/               unit tests
├── data/raw/            generated CSVs (git-ignored)
├── data/processed/      validation output (git-ignored)
├── models/              trained models/metrics (git-ignored)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Free-resource strategy

The project can be built and demonstrated without paid APIs or proprietary datasets.

- Python / PostgreSQL / scikit-learn / XGBoost / SHAP: open-source
- Neon or Supabase: free PostgreSQL tier for a portfolio-scale database
- Streamlit Community Cloud: free demo hosting where the current account limits allow
- GitHub: source control and CI
- Docker: local reproducibility
- Synthetic data: no paid dataset/API required

Free tiers have quotas, so the default dataset can also be generated at smaller sizes through environment variables.

## Local setup

### Option A — Docker PostgreSQL

```bash
docker compose up -d postgres
```

### Python environment

```bash
python3.11 -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows, copy `.env.example` to `.env` manually if `cp` is unavailable.

### Generate and validate data

```bash
python -m scripts.generate_data
python -m scripts.validate_data
```

### Create schema and load PostgreSQL

```bash
python -m scripts.load_database
```

### Train both models

```bash
python -m ml.train_delay_model
python -m ml.train_stockout_model
```

Or run the complete local pipeline:

```bash
python -m scripts.run_pipeline
```

Use `--skip-load` if PostgreSQL is not running and you only want to generate/validate/train.

### Run tests

```bash
pytest
```

### Run the dashboard

```bash
streamlit run app/Home.py
```

## Dashboard pages

1. **Executive dashboard** — network KPIs and current risk snapshot
2. **BOM explorer** — recursive hierarchy, dependency graph and cost roll-up
3. **Supplier intelligence** — supplier register and on-time delivery trends
4. **Inventory intelligence** — stockout/safety-stock pressure and inventory metrics
5. **Supplier delay risk** — order-level delay probability + SHAP factors
6. **Stockout risk** — 14-day safety-stock breach probability + SHAP factors

## Docker

Build and run the application with the included Compose file:

```bash
docker compose build
docker compose up
```

For a full populated demo, generate/load data and train models before opening the Streamlit application, or run the pipeline from a Python environment connected to the Compose PostgreSQL service.

## Deployment

The intended low-cost deployment is:

1. PostgreSQL on Neon or Supabase
2. Streamlit application on Streamlit Community Cloud
3. GitHub as the source repository
4. Database URL supplied as a deployment secret
5. Models either committed only if small and policy-appropriate, or generated during a controlled build process

Do not commit `.env`, passwords or database credentials.

## Testing and quality gates

The project includes tests for configuration, synthetic hierarchy generation, evaluation helpers and leakage-safe feature construction. CI runs Ruff, Black, MyPy and pytest in GitHub Actions when dependencies are available.

Before calling the project finished, verify:

- data generation is reproducible
- validation passes
- schema and views load successfully
- recursive BOM queries return expected hierarchies
- models are trained with a time-aware split
- no target leakage exists
- metrics are generated from real test predictions
- SHAP explanations work on saved models
- dashboard pages load from the database
- no credentials are exposed
- README instructions reproduce the project

## Portfolio positioning

This is intentionally broader than a notebook ML project. It demonstrates **data engineering + advanced SQL + applied ML + explainability + software structure + testing + deployment** in one coherent business problem.

## Easiest deployment path

### 1. Local one-command demo

With Docker installed:

```bash
docker compose up --build
```

Open `http://localhost:8501`.

The Compose stack waits for PostgreSQL to become healthy, generates the synthetic ERP data, validates it, creates the schema/views, loads the database, trains both models, and only then starts Streamlit. The database and model volumes persist between runs.

To rebuild the demo database from scratch:

```bash
docker compose down -v
docker compose up --build
```

### 2. Hosted demo with a free PostgreSQL tier

Use a hosted PostgreSQL database such as Neon or Supabase. Set the same `DATABASE_URL` locally and run:

```bash
python -m scripts.bootstrap --force --skip-models
```

Then push the repository to GitHub. The trained model artifacts in `models/` are included for the Streamlit demo, so the hosted app does not need to retrain models on startup.

For a database you do not want to initialize from your laptop, the repository includes a GitHub Actions **Bootstrap hosted database** workflow. Add a repository secret named `DATABASE_URL`, open Actions → Bootstrap hosted database → Run workflow, and choose whether to replace existing contents.

### 3. Streamlit deployment settings

Deploy the repository as a Streamlit app with the entrypoint:

```text
app/Home.py
```

Add the database connection as the deployment secret/environment value:

```text
DATABASE_URL = postgresql://...
```

The application reads all credentials from environment/secrets and never requires a committed `.env` file.

### 4. Deployment smoke test

After deployment, verify:

- Executive dashboard loads KPI values.
- BOM Explorer returns a multi-level hierarchy.
- Supplier Intelligence displays supplier metrics.
- Inventory Intelligence displays inventory data.
- Supplier Delay Risk returns a probability and SHAP explanation.
- Stockout Risk returns a 14-day probability and SHAP explanation.

If the database is empty, initialize it with the bootstrap workflow before testing the application.
