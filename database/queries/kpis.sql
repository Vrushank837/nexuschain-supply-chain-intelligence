SELECT
    (SELECT COUNT(*) FROM suppliers) AS supplier_count,
    (SELECT COUNT(*) FROM parts) AS part_count,
    (SELECT COALESCE(SUM(closing_stock * p.unit_cost), 0) FROM inventory i JOIN parts p ON p.part_id=i.part_id AND i.date=(SELECT MAX(date) FROM inventory)) AS inventory_value,
    (SELECT ROUND(100.0 * AVG(CASE WHEN actual_delivery_date <= promised_date THEN 1.0 ELSE 0.0 END)::numeric, 1) FROM purchase_orders WHERE status='delivered' AND actual_delivery_date IS NOT NULL) AS on_time_rate,
    (SELECT COUNT(*) FROM inventory WHERE closing_stock=0 AND date=(SELECT MAX(date) FROM inventory)) AS current_stockout_parts;
