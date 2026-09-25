"""Convenience pipeline for local/demo builds."""
from __future__ import annotations

import argparse
import subprocess
import sys


def run(module: str, *args: str) -> None:
    cmd = [sys.executable, "-m", module, *args]
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-load", action="store_true", help="Generate/validate/train without loading PostgreSQL.")
    args = parser.parse_args()
    run("scripts.generate_data")
    run("scripts.validate_data")
    if not args.skip_load:
        run("scripts.load_database")
    run("ml.train_delay_model")
    run("ml.train_stockout_model")
    print("Pipeline completed.")


if __name__ == "__main__":
    main()
