-- ============================================================
--  San Jose Employee Compensation  |  Normalized Schema
--  Run this in psql:  \i database/schema.sql
--  Or in pgAdmin:     open & execute this file
-- ============================================================

-- ------------------------------------------------------------
-- 0. Clean slate
-- ------------------------------------------------------------
DROP TABLE IF EXISTS compensation      CASCADE;
DROP TABLE IF EXISTS employees         CASCADE;
DROP TABLE IF EXISTS job_titles        CASCADE;
DROP TABLE IF EXISTS departments       CASCADE;
DROP TABLE IF EXISTS fiscal_years      CASCADE;


-- ------------------------------------------------------------
-- 1. Lookup / dimension tables
-- ------------------------------------------------------------

CREATE TABLE departments (
    id              SERIAL       PRIMARY KEY,
    name            TEXT         NOT NULL UNIQUE
);

CREATE TABLE job_titles (
    id              SERIAL       PRIMARY KEY,
    title           TEXT         NOT NULL UNIQUE
);

CREATE TABLE fiscal_years (
    year            SMALLINT     PRIMARY KEY   -- e.g. 2021, 2022 …
);

CREATE TABLE employees (
    id              SERIAL       PRIMARY KEY,
    name            TEXT         NOT NULL,
    department_id   INT          NOT NULL  REFERENCES departments (id),
    job_title_id    INT          NOT NULL  REFERENCES job_titles  (id)
);


-- ------------------------------------------------------------
-- 2. Fact table  (one row = one employee × one fiscal year)
-- ------------------------------------------------------------

CREATE TABLE compensation (
    id                                              SERIAL        PRIMARY KEY,
    employee_id                                     INT           NOT NULL  REFERENCES employees   (id),
    fiscal_year                                     SMALLINT      NOT NULL  REFERENCES fiscal_years (year),

    -- cash
    base_pay                                        NUMERIC(12,2),
    overtime                                        NUMERIC(12,2),
    sick_and_vacation_payouts                       NUMERIC(12,2),
    other_cash_compensation                         NUMERIC(12,2),
    total_cash_compensation                         NUMERIC(12,2),

    -- benefits
    defined_contribution_plan_contributions         NUMERIC(12,2),
    medical_dental_vision                           NUMERIC(12,2),
    retirement_contributions_normal_cost            NUMERIC(12,2),
    long_term_disability_life_medicare              NUMERIC(12,2),
    misc_employment_related_costs                   NUMERIC(12,2),

    UNIQUE (employee_id, fiscal_year)               -- one record per person per year
);


-- ------------------------------------------------------------
-- 3. Indexes for common query patterns
-- ------------------------------------------------------------

CREATE INDEX idx_comp_employee    ON compensation (employee_id);
CREATE INDEX idx_comp_year        ON compensation (fiscal_year);
CREATE INDEX idx_emp_department   ON employees    (department_id);
CREATE INDEX idx_emp_job_title    ON employees    (job_title_id);
