CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(20) PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    country VARCHAR(80) NOT NULL,
    region VARCHAR(80) NOT NULL,
    supplier_category VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parts (
    part_id VARCHAR(20) PRIMARY KEY,
    part_name VARCHAR(150) NOT NULL,
    part_type VARCHAR(30) NOT NULL CHECK (part_type IN ('raw_material','component','subassembly','assembly','finished_good')),
    category VARCHAR(80) NOT NULL,
    unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0),
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days >= 0),
    safety_stock INTEGER NOT NULL CHECK (safety_stock >= 0),
    supplier_id VARCHAR(20) REFERENCES suppliers(supplier_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bom (
    parent_part_id VARCHAR(20) NOT NULL REFERENCES parts(part_id) ON DELETE CASCADE,
    child_part_id VARCHAR(20) NOT NULL REFERENCES parts(part_id) ON DELETE CASCADE,
    quantity_required NUMERIC(12,3) NOT NULL CHECK (quantity_required > 0),
    PRIMARY KEY (parent_part_id, child_part_id),
    CHECK (parent_part_id <> child_part_id)
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id VARCHAR(30) PRIMARY KEY,
    supplier_id VARCHAR(20) NOT NULL REFERENCES suppliers(supplier_id),
    part_id VARCHAR(20) NOT NULL REFERENCES parts(part_id),
    order_date DATE NOT NULL,
    promised_date DATE NOT NULL,
    actual_delivery_date DATE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('delivered','open','cancelled')),
    CHECK (promised_date >= order_date),
    CHECK (actual_delivery_date IS NULL OR actual_delivery_date >= order_date)
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id BIGSERIAL PRIMARY KEY,
    part_id VARCHAR(20) NOT NULL REFERENCES parts(part_id),
    date DATE NOT NULL,
    opening_stock INTEGER NOT NULL CHECK (opening_stock >= 0),
    received_quantity INTEGER NOT NULL CHECK (received_quantity >= 0),
    consumed_quantity INTEGER NOT NULL CHECK (consumed_quantity >= 0),
    closing_stock INTEGER NOT NULL CHECK (closing_stock >= 0),
    UNIQUE(part_id, date)
);

CREATE TABLE IF NOT EXISTS sales_orders (
    order_id VARCHAR(30) PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL REFERENCES parts(part_id),
    order_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE INDEX IF NOT EXISTS idx_parts_supplier ON parts(supplier_id);
CREATE INDEX IF NOT EXISTS idx_bom_parent ON bom(parent_part_id);
CREATE INDEX IF NOT EXISTS idx_bom_child ON bom(child_part_id);
CREATE INDEX IF NOT EXISTS idx_po_supplier_date ON purchase_orders(supplier_id, order_date);
CREATE INDEX IF NOT EXISTS idx_po_part_date ON purchase_orders(part_id, order_date);
CREATE INDEX IF NOT EXISTS idx_inventory_part_date ON inventory(part_id, date);
CREATE INDEX IF NOT EXISTS idx_sales_product_date ON sales_orders(product_id, order_date);
