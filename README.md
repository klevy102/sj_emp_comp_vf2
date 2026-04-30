# San Jose Employee Compensation ETL Dashboard

## Project Overview
This repository contains a complete ETL pipeline for San Jose employee compensation data and a Streamlit dashboard for interactive exploration.

- `extract.py` downloads raw compensation data from the San Jose Open Data API.
- `transform.py` cleans and normalizes the raw data into a single consolidated CSV.
- `load.py` creates the PostgreSQL schema and loads cleaned data into the database.
- `dashboard/app.py` launches a Streamlit dashboard that reads data from PostgreSQL.

## API Used
Data is retrieved from the San Jose Open Data OData API:
- `https://data.sanjoseca.gov/datastore/odata3.0/{resource_id}`

This service is public and does not require an API key.

## Run with Docker Compose
No manual setup is required. Run the following from the repository root:

```bash
docker compose up --build
```

Docker Compose will:
1. Start PostgreSQL
2. Run the ETL pipeline (`extract` → `transform` → `load`)
3. Launch the Streamlit dashboard automatically

## Access the Dashboard
Open the dashboard at:

- `http://localhost:8501`

## Environment Configuration
This repo includes only `.env.sample` and does not store real credentials.
Copy `.env.sample` to `.env` to override values locally, or rely on the defaults provided in Docker Compose.



## Team Members and Contributions
- **Ali Abouelazm** — ETL pipeline design, extraction and transformation logic
- **Saketh Thippireddy** — PostgreSQL loading, schema integration, and deployment
- **Kayla Levy** — Streamlit dashboard wrapper, Docker Compose orchestration
- **Harshini Srinivasan** — Documentation and project overview

## Files of Interest
- `extract.py`
- `transform.py`
- `load.py`
- `streamlit_app.py`
- `Dockerfile`
- `docker-compose.yml`
- `.env.sample`
- `README.md`
