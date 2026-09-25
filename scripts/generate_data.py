"""Generate reproducible synthetic ERP data for the project."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

from utils.config import settings
from utils.logging_config import get_logger

log = get_logger(__name__)

COUNTRIES = ["Germany", "Switzerland", "Austria", "Czechia", "Poland", "Netherlands", "Spain", "Italy"]
REGIONS = {"Germany": "DACH", "Switzerland": "DACH", "Austria": "DACH", "Czechia": "CEE", "Poland": "CEE", "Netherlands": "Benelux", "Spain": "Iberia", "Italy": "Southern Europe"}
CATEGORIES = ["electronics", "mechanical", "hydraulics", "fasteners", "materials", "packaging"]
PART_TYPES = ["raw_material", "component", "subassembly", "assembly", "finished_good"]


def _rng() -> np.random.Generator:
    return np.random.default_rng(settings.random_seed)


def generate_suppliers(fake: Faker) -> pd.DataFrame:
    rng = _rng()
    rows = []
    for i in range(1, settings.n_suppliers + 1):
        country = str(rng.choice(COUNTRIES))
        rows.append({
            "supplier_id": f"SUP-{i:04d}",
            "supplier_name": f"{fake.last_name()} Components {fake.company_suffix()}",
            "country": country,
            "region": REGIONS[country],
            "supplier_category": str(rng.choice(CATEGORIES)),
        })
    return pd.DataFrame(rows)


def generate_parts(suppliers: pd.DataFrame, fake: Faker) -> pd.DataFrame:
    rng = _rng()
    rows = []
    # Fixed hierarchy bands make the generated BOM structurally meaningful.
    n = settings.n_parts
    boundaries = [int(n * 0.45), int(n * 0.70), int(n * 0.85), int(n * 0.95), n]
    types = ["raw_material", "component", "subassembly", "assembly", "finished_good"]
    for i in range(1, n + 1):
        idx = i - 1
        ptype = types[next(j for j, b in enumerate(boundaries) if idx < b)]
        supplier_id = None if ptype == "finished_good" else str(rng.choice(suppliers.supplier_id.to_numpy()))
        rows.append({
            "part_id": f"PART-{i:05d}",
            "part_name": f"{fake.word().title()} {fake.word().title()} Module {i:04d}",
            "part_type": ptype,
            "category": str(rng.choice(CATEGORIES)),
            "unit_cost": round(float(rng.lognormal(mean=3.2, sigma=1.0)), 2),
            "lead_time_days": int(rng.integers(3, 46)),
            "safety_stock": int(rng.integers(20, 500)),
            "supplier_id": supplier_id,
        })
    return pd.DataFrame(rows)


def generate_bom(parts: pd.DataFrame) -> pd.DataFrame:
    rng = _rng()
    rows: list[dict] = []
    groups = {t: parts.loc[parts.part_type == t, "part_id"].tolist() for t in PART_TYPES}

    def add(parent: str, child: str) -> None:
        rows.append({"parent_part_id": parent, "child_part_id": child, "quantity_required": round(float(rng.integers(1, 9)), 3)})

    # Guarantee a meaningful 5-level path: finished_good -> assembly -> subassembly -> component -> raw_material.
    for fg in groups["finished_good"]:
        assembly = str(rng.choice(groups["assembly"]))
        subassembly = str(rng.choice(groups["subassembly"]))
        component = str(rng.choice(groups["component"]))
        raw = str(rng.choice(groups["raw_material"]))
        add(fg, assembly)
        add(assembly, subassembly)
        add(subassembly, component)
        add(component, raw)

    existing = {(r["parent_part_id"], r["child_part_id"]) for r in rows}
    # Add cross-links between adjacent levels until the configured edge count is reached.
    adjacent = [("assembly", "subassembly"), ("subassembly", "component"), ("component", "raw_material"), ("finished_good", "assembly")]
    attempts = 0
    while len(rows) < settings.n_bom_relationships and attempts < settings.n_bom_relationships * 10:
        parent_type, child_type = adjacent[int(rng.integers(0, len(adjacent)))]
        parent = str(rng.choice(groups[parent_type]))
        child = str(rng.choice(groups[child_type]))
        key = (parent, child)
        if key not in existing:
            add(parent, child)
            existing.add(key)
        attempts += 1
    return pd.DataFrame(rows[: settings.n_bom_relationships])


def generate_purchase_orders(parts: pd.DataFrame, suppliers: pd.DataFrame) -> pd.DataFrame:
    rng = _rng()
    fake = Faker()
    fake.seed_instance(settings.random_seed + 1)
    dates = pd.date_range(end=pd.Timestamp("2026-06-30"), periods=730, freq="D")
    eligible = parts[parts.supplier_id.notna()].copy()
    supplier_map = suppliers.set_index("supplier_id")
    rows = []
    for i in range(1, settings.n_purchase_orders + 1):
        part = eligible.iloc[int(rng.integers(0, len(eligible)))]
        supplier_id = part.supplier_id
        order_date = pd.Timestamp(rng.choice(dates)).normalize()
        lead = int(max(2, part.lead_time_days + rng.normal(0, 3)))
        promised = order_date + pd.Timedelta(days=lead)
        reliability = 0.94 - 0.46 * ((int(supplier_id.split("-")[1]) % 11) / 10)
        delivered = bool(rng.random() < 0.94)
        if delivered:
            is_late = rng.random() < (1.0 - reliability)
            if is_late:
                delay = int(rng.integers(2, 9))
            else:
                delay = int(rng.integers(-2, 1))
            actual = promised + pd.Timedelta(days=delay)
            status = "delivered"
        else:
            actual = pd.NaT
            status = "open" if rng.random() < 0.8 else "cancelled"
        qty = int(rng.integers(10, 1000))
        rows.append({
            "po_id": f"PO-{i:07d}",
            "supplier_id": supplier_id,
            "part_id": part.part_id,
            "order_date": order_date.date(),
            "promised_date": promised.date(),
            "actual_delivery_date": None if pd.isna(actual) else actual.date(),
            "quantity": qty,
            "unit_price": round(float(part.unit_cost * rng.uniform(0.9, 1.15)), 2),
            "status": status,
        })
    return pd.DataFrame(rows)


def generate_sales_orders(parts: pd.DataFrame) -> pd.DataFrame:
    rng = _rng()
    products = parts[parts.part_type == "finished_good"]
    if products.empty:
        products = parts.tail(max(1, min(30, len(parts))))
    dates = pd.date_range(end=pd.Timestamp("2026-06-30"), periods=730, freq="D")
    rows = []
    for i in range(1, settings.n_sales_orders + 1):
        product = products.iloc[int(rng.integers(0, len(products)))]
        date = pd.Timestamp(rng.choice(dates)).normalize()
        quantity = int(max(1, rng.poisson(35)))
        rows.append({"order_id": f"SO-{i:07d}", "product_id": product.part_id, "order_date": date.date(), "quantity": quantity})
    return pd.DataFrame(rows)


def generate_inventory(parts: pd.DataFrame) -> pd.DataFrame:
    rng = _rng()
    dates = pd.date_range(end=pd.Timestamp("2026-06-30"), periods=365, freq="D")
    n_parts = min(len(parts), max(1, settings.n_inventory_records // len(dates) + 1))
    selected = parts.sample(n=n_parts, random_state=settings.random_seed)
    rows = []
    for _, part in selected.iterrows():
        # A controlled demand/supply process creates both healthy and stressed inventory states.
        demand_factor = 0.90 + ((int(part.part_id.split("-")[1]) % 9) / 6)
        stock = int(part.safety_stock * rng.uniform(0.9, 1.8))
        for date in dates:
            demand_mean = max(2.0, (part.safety_stock / 12.0) * demand_factor)
            demand = int(max(0, rng.poisson(demand_mean)))
            receipt = 0
            if rng.random() < 0.24:
                receipt = int(max(1, rng.normal(part.safety_stock * 0.70, part.safety_stock * 0.15)))
            closing = max(0, stock + receipt - demand)
            rows.append({
                "part_id": part.part_id,
                "date": date.date(),
                "opening_stock": stock,
                "received_quantity": receipt,
                "consumed_quantity": demand,
                "closing_stock": closing,
            })
            stock = closing
            if len(rows) >= settings.n_inventory_records:
                return pd.DataFrame(rows)
    return pd.DataFrame(rows)


def write_csvs(out_dir: Path, frames: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        path = out_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        log.info("dataset_written", table=name, rows=len(frame), path=str(path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    fake = Faker("en_US")
    fake.seed_instance(settings.random_seed)
    np.random.seed(settings.random_seed)
    log.info("data_generation_started", seed=settings.random_seed)
    suppliers = generate_suppliers(fake)
    parts = generate_parts(suppliers, fake)
    bom = generate_bom(parts)
    purchase_orders = generate_purchase_orders(parts, suppliers)
    sales_orders = generate_sales_orders(parts)
    inventory = generate_inventory(parts)
    frames = {
        "suppliers": suppliers,
        "parts": parts,
        "bom": bom,
        "purchase_orders": purchase_orders,
        "inventory": inventory,
        "sales_orders": sales_orders,
    }
    write_csvs(args.output, frames)
    log.info("data_generation_complete", tables=list(frames), total_rows=sum(len(x) for x in frames.values()))


if __name__ == "__main__":
    main()
