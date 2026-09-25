WITH RECURSIVE bom_tree AS (
    SELECT
        b.parent_part_id AS root_part_id,
        b.child_part_id AS part_id,
        1 AS level,
        b.quantity_required::numeric AS cumulative_quantity,
        ARRAY[b.parent_part_id::text, b.child_part_id::text]::text[] AS path 
    FROM bom b
    WHERE b.parent_part_id = :root_part_id

    UNION ALL

    SELECT
        bt.root_part_id,
        b.child_part_id,
        bt.level + 1,
        bt.cumulative_quantity * b.quantity_required,
        bt.path || b.child_part_id::text
    FROM bom_tree bt
    JOIN bom b ON b.parent_part_id = bt.part_id
    WHERE NOT (b.child_part_id = ANY(bt.path))
)
SELECT
    bt.root_part_id,
    bt.part_id,
    p.part_name,
    p.part_type,
    p.category,
    bt.level,
    bt.cumulative_quantity,
    ROUND((bt.cumulative_quantity * p.unit_cost)::numeric, 2) AS cumulative_cost,
    array_to_string(bt.path, ' -> ') AS dependency_path
FROM bom_tree bt
JOIN parts p ON p.part_id = bt.part_id
ORDER BY bt.level, bt.part_id;
