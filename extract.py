import requests
import pandas as pd
from pathlib import Path

BASE_URL = "https://data.sanjoseca.gov/datastore/odata3.0/{resource_id}"
PAGE_SIZE = 1000

DATASETS = {
    2021: "205afc93-b3d2-4199-8d44-14a435b84dd7",
    2022: "efbf228b-f436-4297-aef2-48980ae1f579",
    2023: "6f269eb5-7d88-45d3-8911-881545c6e521",
    2024: "bc7e0721-8467-43e1-a9c1-1beedcf442f1",
}

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def download_dataset(year: int, resource_id: str) -> pd.DataFrame:
    all_records = []
    skip = 0

    while True:
        params = {"$format": "json", "$top": PAGE_SIZE, "$skip": skip}
        response = requests.get(BASE_URL.format(resource_id=resource_id), params=params, timeout=60)
        response.raise_for_status()
        records = response.json().get("value", [])
        if not records:
            break

        all_records.extend(records)
        print(f"  [{year}] Fetched rows {skip + 1}–{skip + len(records)}")
        if len(records) < PAGE_SIZE:
            break
        skip += PAGE_SIZE

    return pd.DataFrame(all_records)


def main():
    for year, resource_id in DATASETS.items():
        print(f"\n[{year}] Starting download...")
        df = download_dataset(year, resource_id)
        df["fiscal_year"] = year

        output_path = DATA_DIR / f"compensation_{year}.csv"
        df.to_csv(output_path, index=False)
        print(f"[{year}] Completed: {len(df)} rows -> {output_path}")

    print("\nExtraction complete.")


if __name__ == "__main__":
    main()
