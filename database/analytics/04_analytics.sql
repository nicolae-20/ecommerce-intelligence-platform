-- ============================================================
-- E-COMMERCE INTELLIGENCE PLATFORM
-- BUSINESS ANALYTICS
-- ============================================================


-- ============================================================
-- 1. TOTAL REVENUE
-- ============================================================

SELECT
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.status = 'COMPLETED';


-- ============================================================
-- 2. MONTHLY REVENUE
-- ============================================================

SELECT
    TO_CHAR(o.order_date, 'YYYY-MM') AS order_month,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_revenue
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.status = 'COMPLETED'
GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
ORDER BY order_month;


-- ============================================================
-- 3. TOP CUSTOMERS
-- ============================================================

SELECT
    c.first_name || ' ' || c.last_name AS customer_name,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.status = 'COMPLETED'
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name
ORDER BY total_revenue DESC
FETCH FIRST 5 ROWS ONLY;


-- ============================================================
-- 4. AVERAGE ORDER VALUE
-- ============================================================

SELECT
    ROUND(
        SUM(oi.quantity * oi.unit_price)
        / COUNT(DISTINCT o.order_id),
        2
    ) AS average_order_value
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.status = 'COMPLETED';


-- ============================================================
-- 5. REVENUE BY CATEGORY
-- ============================================================

SELECT
    c.category_name,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS category_revenue
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
JOIN categories c
    ON p.category_id = c.category_id
WHERE o.status = 'COMPLETED'
GROUP BY c.category_name
ORDER BY category_revenue DESC;


-- ============================================================
-- 6. PRODUCT REVENUE
-- ============================================================

WITH product_revenue AS (
    SELECT
        p.product_id,
        p.product_name,
        c.category_name,
        SUM(oi.quantity * oi.unit_price) AS total_revenue
    FROM products p
    JOIN categories c
        ON p.category_id = c.category_id
    JOIN order_items oi
        ON p.product_id = oi.product_id
    JOIN orders o
        ON oi.order_id = o.order_id
    WHERE o.status = 'COMPLETED'
    GROUP BY
        p.product_id,
        p.product_name,
        c.category_name
)
SELECT
    product_name,
    category_name,
    ROUND(total_revenue, 2) AS total_revenue
FROM product_revenue
ORDER BY total_revenue DESC;


-- ============================================================
-- 7. TOP 3 PRODUCTS PER CATEGORY
-- ============================================================

WITH product_revenue AS (
    SELECT
        p.product_id,
        p.product_name,
        c.category_name,
        SUM(oi.quantity * oi.unit_price) AS total_revenue
    FROM products p
    JOIN categories c
        ON p.category_id = c.category_id
    JOIN order_items oi
        ON p.product_id = oi.product_id
    JOIN orders o
        ON oi.order_id = o.order_id
    WHERE o.status = 'COMPLETED'
    GROUP BY
        p.product_id,
        p.product_name,
        c.category_name
),
ranked_products AS (
    SELECT
        product_name,
        category_name,
        total_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_name
            ORDER BY total_revenue DESC
        ) AS product_rank
    FROM product_revenue
)
SELECT
    product_name,
    category_name,
    ROUND(total_revenue, 2) AS total_revenue,
    product_rank
FROM ranked_products
WHERE product_rank <= 3
ORDER BY category_name, product_rank;


-- ============================================================
-- 8. MONTHLY REVENUE GROWTH
-- ============================================================

WITH monthly_revenue AS (
    SELECT
        TO_CHAR(o.order_date, 'YYYY-MM') AS order_month,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.status = 'COMPLETED'
    GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
),
monthly_with_previous AS (
    SELECT
        order_month,
        monthly_revenue,
        LAG(monthly_revenue) OVER (
            ORDER BY order_month
        ) AS previous_month_revenue
    FROM monthly_revenue
)
SELECT
    order_month,
    monthly_revenue,
    previous_month_revenue,
    ROUND(
        (monthly_revenue - previous_month_revenue)
        / previous_month_revenue * 100,
        2
    ) AS revenue_growth_percent
FROM monthly_with_previous
ORDER BY order_month;


-- ============================================================
-- 9. CUSTOMER LIFETIME VALUE
-- ============================================================

WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.quantity) AS total_items,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.status = 'COMPLETED'
    GROUP BY
        c.customer_id,
        c.first_name,
        c.last_name
)
SELECT
    customer_name,
    total_orders,
    total_items,
    total_revenue,
    ROUND(total_revenue / total_orders, 2) AS average_order_value
FROM customer_metrics
ORDER BY total_revenue DESC;


-- ============================================================
-- 10. REPEAT CUSTOMERS
-- ============================================================

SELECT
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(DISTINCT o.order_id) AS completed_orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.status = 'COMPLETED'
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name
HAVING COUNT(DISTINCT o.order_id) >= 2
ORDER BY completed_orders DESC, total_revenue DESC;


-- ============================================================
-- 11. REPEAT CUSTOMER RATE
-- ============================================================

WITH customer_orders AS (
    SELECT
        c.customer_id,
        COUNT(DISTINCT o.order_id) AS completed_orders
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    WHERE o.status = 'COMPLETED'
    GROUP BY c.customer_id
),
customer_stats AS (
    SELECT
        COUNT(*) AS total_customers,
        SUM(
            CASE
                WHEN completed_orders >= 2 THEN 1
                ELSE 0
            END
        ) AS repeat_customers
    FROM customer_orders
)
SELECT
    total_customers,
    repeat_customers,
    ROUND(
        repeat_customers / total_customers * 100,
        2
    ) AS repeat_customer_rate
FROM customer_stats;


-- ============================================================
-- 12. LOW STOCK PRODUCTS
-- ============================================================

SELECT
    p.product_name,
    c.category_name,
    p.stock_quantity,
    CASE
        WHEN p.stock_quantity < 20 THEN 'LOW STOCK'
        WHEN p.stock_quantity <= 40 THEN 'MEDIUM STOCK'
        ELSE 'HEALTHY STOCK'
    END AS stock_status
FROM products p
JOIN categories c
    ON p.category_id = c.category_id
ORDER BY p.stock_quantity;


-- ============================================================
-- 13. PROFIT BY CATEGORY
-- ============================================================

SELECT
    c.category_name,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
    ROUND(SUM(oi.quantity * p.cost_price), 2) AS cost,
    ROUND(
        SUM(oi.quantity * oi.unit_price)
        - SUM(oi.quantity * p.cost_price),
        2
    ) AS profit
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
JOIN categories c
    ON p.category_id = c.category_id
WHERE o.status = 'COMPLETED'
GROUP BY c.category_name
ORDER BY profit DESC;


-- ============================================================
-- 14. PRODUCT SALES DECLINE
-- ============================================================

WITH monthly_product_sales AS (
    SELECT
        p.product_id,
        p.product_name,
        TO_CHAR(o.order_date, 'YYYY-MM') AS sales_month,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_revenue
    FROM products p
    JOIN order_items oi
        ON p.product_id = oi.product_id
    JOIN orders o
        ON oi.order_id = o.order_id
    WHERE o.status = 'COMPLETED'
    GROUP BY
        p.product_id,
        p.product_name,
        TO_CHAR(o.order_date, 'YYYY-MM')
),
sales_with_previous AS (
    SELECT
        product_id,
        product_name,
        sales_month,
        monthly_revenue,
        LAG(monthly_revenue) OVER (
            PARTITION BY product_id
            ORDER BY sales_month
        ) AS previous_month_revenue
    FROM monthly_product_sales
)
SELECT
    product_name,
    sales_month,
    monthly_revenue,
    previous_month_revenue,
    ROUND(
        monthly_revenue - previous_month_revenue,
        2
    ) AS revenue_change
FROM sales_with_previous
WHERE previous_month_revenue IS NOT NULL
  AND monthly_revenue < previous_month_revenue
ORDER BY revenue_change;


-- ============================================================
-- 15. CANCELLED ORDERS / POTENTIAL LOST REVENUE
-- ============================================================

SELECT
    COUNT(DISTINCT o.order_id) AS cancelled_orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)
        AS potential_lost_revenue
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.status = 'CANCELLED';