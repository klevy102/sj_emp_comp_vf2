# San Jose Employee Compensation ETL Dashboard

An end-to-end data pipeline and interactive dashboard for exploring San Jose city employee compensation from 2021 to 2024.

---

## What It Does

- Pulls raw compensation data from the San Jose Open Data API (no API key needed)
- Cleans and normalizes it across fiscal years
- Loads it into a PostgreSQL database
- Serves an interactive Streamlit dashboard for filtering and exploring the data

---

## How to Run

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Steps

**1. Clone the repo**
```bash
git clone https://github.com/klevy102/sj_emp_comp_vf2.git
cd sj_emp_comp_vf2
```

**2. Set up your environment file**
```bash
cp .env.sample .env
```
The defaults in `.env.sample` work out of the box. You only need to edit `.env` if you want to use a different database password or port.

**3. Start everything**
```bash
docker compose up --build
```

Docker Compose will handle the rest — it starts Postgres, runs the ETL pipeline (extract → transform → load), and launches the dashboard.

**4. Open the dashboard**

Once you see `Uvicorn server started` in the logs, go to:

```
http://localhost:8501
```

The ETL step usually takes 1–2 minutes on first run since it fetches data from the API. The dashboard won't be usable until that finishes.

---

## Port Conflict

If port `5432` is already in use (e.g. a local Postgres instance), edit the `docker-compose.yml` and change the db port mapping from `5432:5432` to `5433:5432`. The containers communicate internally so this won't break anything.

---

## Project Structure

```
extract.py        — fetches raw CSV data from the San Jose OData API
transform.py      — cleans and consolidates data across years
load.py           — creates the schema and loads data into PostgreSQL
main.py           — runs extract → transform → load in sequence
dashboard/app.py  — Streamlit dashboard
Dockerfile        — container definition for ETL and dashboard
docker-compose.yml
.env.sample       — copy this to .env before running
```

---

## Data Source

San Jose Open Data OData API — public, no authentication required.

---

## Team

- **Ali Abouelazm** — ETL pipeline, extraction and transformation logic
- **Saketh Thippireddy** — PostgreSQL schema and data loading
- **Kayla Levy** — Streamlit dashboard, Docker Compose orchestration
- **Harshini Srinivasan** — Documentation
