import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
YEARS = [2021, 2022, 2023, 2024]

MONETARY_COLS = [
    "total_cash_compensation",
    "base_pay",
    "overtime",
    "sick_and_vacation_payouts",
    "other_cash_compensation",
    "defined_contribution_city_paid",
    "medical_dental_vision",
    "retirement_contributions_city_paid",
    "long_term_disability_life_medicare",
    "misc_employment_related_costs",
]


def to_snake(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name.lower()


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=to_snake)

    job_col = [c for c in df.columns if c.startswith("job_title")]
    if job_col:
        df = df.rename(columns={job_col[0]: "job_title"})

    renames = {
        "defined_contribution_plan_contributions__city_paid": "defined_contribution_city_paid",
        "retirement_contributions_normal_cost__city_paid": "retirement_contributions_city_paid",
        "fiscalyear": "fiscal_year",
    }
    return df.rename(columns=renames)


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())
    return df


def normalize_capitalization(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["name", "department", "job_title"]:
        if col in df.columns:
            df[col] = df[col].str.title()
    return df


def parse_monetary_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in MONETARY_COLS:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                       .str.replace(",", "", regex=False)
                       .str.replace("$", "", regex=False)
                       .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fill_missing_monetary(df: pd.DataFrame) -> pd.DataFrame:
    for col in MONETARY_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)
    return df


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped:
        print(f"  Dropped {dropped} duplicate rows")
    return df

CLEANING_PIPELINE = [
    normalize_column_names,
    strip_whitespace,
    normalize_capitalization,
    parse_monetary_columns,
    fill_missing_monetary,
    drop_duplicate_rows,
]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    for fn in CLEANING_PIPELINE:
        df = fn(df)
    return df


def main():
    cleaned_frames = []

    for year in YEARS:
        raw_path = DATA_DIR / f"compensation_{year}.csv"
        print(f"\n[{year}] Loading raw file: {raw_path}")
        df = pd.read_csv(raw_path)
        df = clean(df)
        print(f"[{year}] Cleaned shape: {df.shape}")
        cleaned_frames.append(df)

    combined = pd.concat(cleaned_frames, ignore_index=True)
    output_path = DATA_DIR / "compensation_clean.csv"
    combined.to_csv(output_path, index=False)
    print(f"\nSaved cleaned dataset: {output_path}")
    print("Transformation complete.")


if __name__ == "__main__":
    main()
