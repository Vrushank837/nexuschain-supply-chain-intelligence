CREATE OR REPLACE VIEW supplier_performance AS
SELECT
    s.supplier_id,
    s.supplier_name,
    s.country,
    s.region,
    COUNT(po.po_id) AS total_orders,
    COUNT(*) FILTER (WHERE po.actual_delivery_date IS NOT NULL) AS delivered_orders,
    ROUND(100.0 * AVG(CASE WHEN po.actual_delivery_date <= po.promised_date THEN 1.0 ELSE 0.0 END)::numeric, 2) AS on_time_rate_pct,
    ROUND(AVG(GREATEST(0, po.actual_delivery_date - po.promised_date))::numeric, 2) AS avg_delay_days,
    ROUND(AVG(po.actual_delivery_date - po.order_date)::numeric, 2) AS avg_actual_lead_time_days,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY GREATEST(0, po.actual_delivery_date - po.promised_date))::numeric, 2) AS median_delay_days,
    ROUND(100.0 * PERCENT_RANK() OVER (ORDER BY AVG(CASE WHEN po.actual_delivery_date <= po.promised_date THEN 1.0 ELSE 0.0 END))::numeric, 2) AS reliability_percentile
FROM suppliers s
JOIN purchase_orders po ON po.supplier_id = s.supplier_id
WHERE po.status = 'delivered' AND po.actual_delivery_date IS NOT NULL
GROUP BY s.supplier_id, s.supplier_name, s.country, s.region;

CREATE OR REPLACE VIEW inventory_summary AS
SELECT
    i.part_id,
    p.part_name,
    p.category,
    p.safety_stock,
    MAX(i.date) AS latest_date,
    (ARRAY_AGG(i.closing_stock ORDER BY i.date DESC))[1] AS current_stock,
    ROUND(AVG(i.closing_stock)::numeric, 2) AS avg_stock,
    SUM(i.consumed_quantity) AS total_consumed,
    SUM(i.received_quantity) AS total_received,
    COUNT(*) FILTER (WHERE i.closing_stock <= p.safety_stock) AS safety_stock_days,
    COUNT(*) FILTER (WHERE i.closing_stock = 0) AS stockout_days
FROM inventory i
JOIN parts p ON p.part_id = i.part_id
GROUP BY i.part_id, p.part_name, p.category, p.safety_stock;

CREATE OR REPLACE VIEW monthly_supplier_delivery AS
SELECT
    supplier_id,
    DATE_TRUNC('month', actual_delivery_date)::date AS month,
    COUNT(*) AS delivered_orders,
    ROUND(100.0 * AVG(CASE WHEN actual_delivery_date <= promised_date THEN 1.0 ELSE 0.0 END)::numeric, 2) AS on_time_rate_pct
FROM purchase_orders
WHERE status = 'delivered' AND actual_delivery_date IS NOT NULL
GROUP BY supplier_id, DATE_TRUNC('month', actual_delivery_date);
