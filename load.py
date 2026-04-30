import csv
import os
import time
from pathlib import Path

import psycopg2
from psycopg2 import OperationalError


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value and value.isdigit() else default


DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     _env_int("DB_PORT", 5432),
    "dbname":   os.getenv("DB_NAME", "sj_emp_comp"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_SQL = BASE_DIR / "database" / "schema.sql"
DATA_CSV = BASE_DIR / "data" / "compensation_clean.csv"


def _num(value: str):
    v = str(value).strip().replace(",", "")
    return float(v) if v else None


def get_or_create(cur, table: str, column: str, value: str) -> int:
    cur.execute(
        f"INSERT INTO {table} ({column}) VALUES (%s) ON CONFLICT ({column}) DO NOTHING",
        (value,),
    )
    cur.execute(f"SELECT id FROM {table} WHERE {column} = %s", (value,))
    return cur.fetchone()[0]


def get_employee_id(cur, name: str, department_id: int, job_title_id: int) -> int:
    cur.execute(
        "SELECT id FROM employees WHERE name = %s AND department_id = %s AND job_title_id = %s LIMIT 1",
        (name, department_id, job_title_id),
    )
    found = cur.fetchone()
    if found:
        return found[0]

    cur.execute(
        "INSERT INTO employees (name, department_id, job_title_id) VALUES (%s, %s, %s) RETURNING id",
        (name, department_id, job_title_id),
    )
    return cur.fetchone()[0]


def create_schema(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL.read_text())
    conn.commit()
    print("Schema created.")


def load_csv(conn, csv_path: Path | None = None):
    csv_path = csv_path or DATA_CSV
    rows = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with conn.cursor() as cur:
            for row in reader:
                dept_id = get_or_create(cur, "departments", "name", row["department"])
                title_id = get_or_create(cur, "job_titles", "title", row["job_title"])
                employee_id = get_employee_id(cur, row["name"].strip(), dept_id, title_id)

                year_value = row.get("fiscal_year") or row.get("fiscalyear")
                if year_value is None:
                    raise KeyError("Missing fiscal_year or fiscalyear column in cleaned CSV")
                year = int(year_value)
                cur.execute(
                    "INSERT INTO fiscal_years (year) VALUES (%s) ON CONFLICT DO NOTHING",
                    (year,),
                )
                cur.execute(
                    """INSERT INTO compensation (
                           employee_id, fiscal_year,
                           base_pay, overtime, sick_and_vacation_payouts,
                           other_cash_compensation, total_cash_compensation,
                           defined_contribution_plan_contributions,
                           medical_dental_vision,
                           retirement_contributions_normal_cost,
                           long_term_disability_life_medicare,
                           misc_employment_related_costs
                       ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (employee_id, fiscal_year) DO NOTHING""",
                    (
                        employee_id,
                        year,
                        _num(row.get("base_pay", "")),
                        _num(row.get("overtime", "")),
                        _num(row.get("sick_and_vacation_payouts", "")),
                        _num(row.get("other_cash_compensation", "")),
                        _num(row.get("total_cash_compensation", "")),
                        _num(row.get("defined_contribution_city_paid", "")),
                        _num(row.get("medical_dental_vision", "")),
                        _num(row.get("retirement_contributions_city_paid", "")),
                        _num(row.get("long_term_disability_life_medicare", "")),
                        _num(row.get("misc_employment_related_costs", "")),
                    ),
                )
                rows += 1

    conn.commit()
    print(f"Loaded {rows} rows from {csv_path}.")


def connect_with_retry(max_attempts: int = 20, delay: int = 3):
    for attempt in range(1, max_attempts + 1):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except OperationalError:
            print(f"PostgreSQL unavailable, retrying in {delay}s... ({attempt}/{max_attempts})")
            time.sleep(delay)
    raise RuntimeError("Unable to connect to PostgreSQL after multiple attempts.")


def main():
    conn = connect_with_retry()
    try:
        create_schema(conn)
        load_csv(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
