"""Leakage-safe feature construction for both ML tasks."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW / f"{name}.csv")


def supplier_delay_features() -> pd.DataFrame:
    po = _load("purchase_orders")
    parts = _load("parts")[['part_id', 'lead_time_days', 'category']]
    po["order_date"] = pd.to_datetime(po["order_date"])
    po["promised_date"] = pd.to_datetime(po["promised_date"])
    po["actual_delivery_date"] = pd.to_datetime(po["actual_delivery_date"], errors="coerce")
    po = po[po.status == "delivered"].copy()
    po["delay_days"] = (po["actual_delivery_date"] - po["promised_date"]).dt.days.clip(lower=0)
    po["delay_flag"] = (po["delay_days"] > 0).astype(int)
    po = po.sort_values("order_date").reset_index(drop=True)

    # Features are calculated from prior orders only, avoiding target leakage.
    historical = []
    for _supplier_id, group in po.groupby("supplier_id", sort=False):
        g = group.copy()
        g["supplier_prior_delay_rate"] = g["delay_flag"].shift(1).expanding().mean()
        g["supplier_prior_avg_delay"] = g["delay_days"].shift(1).expanding().mean()
        g["supplier_prior_orders"] = np.arange(len(g), dtype=float)
        historical.append(g)
    po = pd.concat(historical).sort_index()
    po = po.merge(parts, on="part_id", how="left")
    po["supplier_prior_delay_rate"] = po["supplier_prior_delay_rate"].fillna(0.0)
    po["supplier_prior_avg_delay"] = po["supplier_prior_avg_delay"].fillna(0.0)
    po["supplier_prior_orders"] = po["supplier_prior_orders"].fillna(0)
    po["month"] = po.order_date.dt.month
    po["day_of_week"] = po.order_date.dt.dayofweek
    return po[[
        "order_date", "supplier_id", "part_id", "category", "lead_time_days", "quantity", "unit_price",
        "month", "day_of_week", "supplier_prior_delay_rate", "supplier_prior_avg_delay",
        "supplier_prior_orders", "delay_flag", "delay_days"
    ]]


def stockout_features() -> pd.DataFrame:
    inv = _load("inventory")
    parts = _load("parts")[['part_id', 'lead_time_days', 'safety_stock', 'category']]
    inv["date"] = pd.to_datetime(inv["date"])
    inv = inv.sort_values(["part_id", "date"]).reset_index(drop=True)
    inv = inv.merge(parts, on="part_id", how="left")

    g = inv.groupby("part_id", group_keys=False)
    inv["demand_avg_7d"] = g["consumed_quantity"].transform(lambda s: s.shift(1).rolling(7, min_periods=2).mean())
    inv["demand_std_7d"] = g["consumed_quantity"].transform(lambda s: s.shift(1).rolling(7, min_periods=2).std())
    inv["receipt_avg_14d"] = g["received_quantity"].transform(lambda s: s.shift(1).rolling(14, min_periods=2).mean())

    # Target uses future observations only. A risk event means inventory reaches or falls below safety stock within 14 days.
    # A direct forward-window calculation that is easy to audit.
    targets = []
    for _, group in inv.groupby("part_id", sort=False):
        values = group["closing_stock"].to_numpy()
        target = np.zeros(len(values), dtype=int)
        for i in range(len(values)):
            future = values[i + 1 : i + 15]
            target[i] = int(len(future) > 0 and future.min() <= group["safety_stock"].iloc[i])
        targets.append(pd.Series(target, index=group.index))
    inv["stockout_risk_within_14d"] = pd.concat(targets).sort_index()

    inv["demand_avg_7d"] = inv["demand_avg_7d"].fillna(inv["consumed_quantity"].median())
    inv["demand_std_7d"] = inv["demand_std_7d"].fillna(0)
    inv["receipt_avg_14d"] = inv["receipt_avg_14d"].fillna(inv["received_quantity"].median())
    inv["days_of_cover"] = inv["closing_stock"] / inv["demand_avg_7d"].clip(lower=1)
    inv["safety_stock_gap"] = inv["closing_stock"] - inv["safety_stock"]
    inv["month"] = inv.date.dt.month
    inv["day_of_week"] = inv.date.dt.dayofweek
    return inv[[
        "date", "part_id", "category", "closing_stock", "safety_stock", "lead_time_days",
        "demand_avg_7d", "demand_std_7d", "receipt_avg_14d", "days_of_cover",
        "safety_stock_gap", "month", "day_of_week", "stockout_risk_within_14d"
    ]]
