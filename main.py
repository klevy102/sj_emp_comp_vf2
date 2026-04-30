import sys

import extract
import load
import transform

STEPS = {
    "extract":   (extract.main,   "Downloading raw data..."),
    "transform": (transform.main, "Transforming raw data..."),
    "load":      (load.main,      "Loading cleaned data into PostgreSQL..."),
    "etl":       (lambda: [extract.main(), transform.main(), load.main()], "Running full ETL pipeline..."),
}


def run_step(name):
    fn, msg = STEPS[name]
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")
    fn()


def main():
    args = sys.argv[1:]
    if args:
        for arg in args:
            if arg not in STEPS:
                print(f"Unknown step '{arg}'. Available: {', '.join(STEPS)}")
                sys.exit(1)
            run_step(arg)
    else:
        for name in ["extract", "transform", "load"]:
            run_step(name)

    print("\nDone.")


if __name__ == "__main__":
    main()
