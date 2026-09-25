"""Validate generated CSV data before database loading."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from utils.logging_config import get_logger

log = get_logger(__name__)


def validate(data_dir: Path) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    required = ["suppliers", "parts", "bom", "purchase_orders", "inventory", "sales_orders"]
    frames = {name: pd.read_csv(data_dir / f"{name}.csv") for name in required}

    def add(table: str, message: str) -> None:
        issues.setdefault(table, []).append(message)

    for name, df in frames.items():
        if df.empty:
            add(name, "table is empty")
        if df.duplicated().any():
            add(name, "duplicate rows detected")

    supplier_ids = set(frames["suppliers"]["supplier_id"])
    part_ids = set(frames["parts"]["part_id"])
    if not frames["parts"]["supplier_id"].dropna().isin(supplier_ids).all():
        add("parts", "unknown supplier_id")
    if (
        not frames["bom"]["parent_part_id"].isin(part_ids).all()
        or not frames["bom"]["child_part_id"].isin(part_ids).all()
    ):
        add("bom", "unknown part reference")
    if (frames["bom"]["parent_part_id"] == frames["bom"]["child_part_id"]).any():
        add("bom", "self-reference detected")
    if not frames["purchase_orders"]["supplier_id"].isin(supplier_ids).all():
        add("purchase_orders", "unknown supplier_id")
    if not frames["purchase_orders"]["part_id"].isin(part_ids).all():
        add("purchase_orders", "unknown part_id")
    if not frames["inventory"]["part_id"].isin(part_ids).all():
        add("inventory", "unknown part_id")
    if not frames["sales_orders"]["product_id"].isin(part_ids).all():
        add("sales_orders", "unknown product_id")
    for table in ["parts", "purchase_orders", "inventory", "sales_orders"]:
        if frames[table].isna().all(axis=0).any():
            add(table, "column entirely missing")
    if (frames["parts"]["unit_cost"] < 0).any():
        add("parts", "negative unit cost")
    if (frames["purchase_orders"]["quantity"] <= 0).any():
        add("purchase_orders", "non-positive purchase quantity")
    report = data_dir.parent / "processed" / "validation_report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    if issues:
        report.write_text("\n".join(f"[{k}] {v}" for k, v in issues.items()), encoding="utf-8")
    else:
        report.write_text(
            "VALIDATION PASSED\nAll structural and referential checks passed.\n", encoding="utf-8"
        )
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    issues = validate(args.input)
    if issues:
        for table, messages in issues.items():
            for message in messages:
                log.error("validation_issue", table=table, issue=message)
        raise SystemExit(1)
    log.info("validation_passed")


if __name__ == "__main__":
    main()
