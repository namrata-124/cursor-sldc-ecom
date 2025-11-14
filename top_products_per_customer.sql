WITH customer_product AS (
  SELECT
    o.customer_id,
    c.name AS customer_name,
    oi.product_id,
    p.name AS product_name,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.quantity * oi.unit_price) AS total_spent
  FROM order_items oi
  JOIN orders o ON oi.order_id = o.order_id
  JOIN customers c ON o.customer_id = c.customer_id
  JOIN products p ON oi.product_id = p.product_id
  GROUP BY o.customer_id, oi.product_id
),
ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_quantity DESC) AS rn
  FROM customer_product
)
SELECT customer_id, customer_name, product_id, product_name, total_quantity, total_spent
FROM ranked
WHERE rn <= 3
ORDER BY customer_id, total_quantity DESC;
