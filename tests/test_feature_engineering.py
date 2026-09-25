import pandas as pd

import ml.features as features


def test_delay_features_use_prior_history(tmp_path, monkeypatch):
    suppliers = pd.DataFrame([{"supplier_id": "S1"}])
    parts = pd.DataFrame([{"part_id": "P1", "lead_time_days": 5, "category": "mechanical"}])
    po = pd.DataFrame(
        [
            {
                "po_id": "1",
                "supplier_id": "S1",
                "part_id": "P1",
                "order_date": "2026-01-01",
                "promised_date": "2026-01-05",
                "actual_delivery_date": "2026-01-05",
                "quantity": 10,
                "unit_price": 5,
                "status": "delivered",
            },
            {
                "po_id": "2",
                "supplier_id": "S1",
                "part_id": "P1",
                "order_date": "2026-01-10",
                "promised_date": "2026-01-14",
                "actual_delivery_date": "2026-01-17",
                "quantity": 20,
                "unit_price": 5,
                "status": "delivered",
            },
        ]
    )
    suppliers.to_csv(tmp_path / "suppliers.csv", index=False)
    parts.to_csv(tmp_path / "parts.csv", index=False)
    po.to_csv(tmp_path / "purchase_orders.csv", index=False)
    monkeypatch.setattr(features, "RAW", tmp_path)
    out = features.supplier_delay_features()
    assert out.iloc[0].supplier_prior_delay_rate == 0
    assert out.iloc[1].supplier_prior_delay_rate == 0
    assert out.iloc[1].delay_flag == 1
