from database import get_connection


def get_top_customers(limit=5):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
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
                FETCH FIRST :limit ROWS ONLY
            """, {"limit": limit})

            return cursor.fetchall()
    finally:
        connection.close()


def get_monthly_revenue():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    TO_CHAR(o.order_date, 'YYYY-MM') AS order_month,
                    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_revenue
                FROM orders o
                JOIN order_items oi
                    ON o.order_id = oi.order_id
                WHERE o.status = 'COMPLETED'
                GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
                ORDER BY order_month
            """)

            return cursor.fetchall()
    finally:
        connection.close()


def get_customer_metrics():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
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
                ORDER BY total_revenue DESC
            """)

            return cursor.fetchall()
    finally:
        connection.close()

def get_customer(customer_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    customer_id,
                    first_name,
                    last_name,
                    country
                FROM customers
                WHERE customer_id = :customer_id
            """, {"customer_id": customer_id})

            return cursor.fetchone()
    finally:
        connection.close()


def get_profit_by_category():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
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
                ORDER BY profit DESC
            """)

            return cursor.fetchall()
    finally:
        connection.close()


def get_overview():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
                    COUNT(DISTINCT o.order_id) AS total_orders,
                    COUNT(DISTINCT o.customer_id) AS total_customers,
                    ROUND(
                        SUM(oi.quantity * oi.unit_price)
                        / COUNT(DISTINCT o.order_id),
                        2
                    ) AS average_order_value
                FROM orders o
                JOIN order_items oi
                    ON o.order_id = oi.order_id
                WHERE o.status = 'COMPLETED'
            """)

            return cursor.fetchone()
    finally:
        connection.close()


def get_financial_summary():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
                    ROUND(SUM(oi.quantity * p.cost_price), 2) AS total_cogs,
                    ROUND(
                        SUM(oi.quantity * oi.unit_price)
                        - SUM(oi.quantity * p.cost_price),
                        2
                    ) AS gross_profit,
                    ROUND(
                        (
                            SUM(oi.quantity * oi.unit_price)
                            - SUM(oi.quantity * p.cost_price)
                        )
                        / NULLIF(SUM(oi.quantity * oi.unit_price), 0) * 100,
                        2
                    ) AS gross_margin
                FROM orders o
                JOIN order_items oi
                    ON o.order_id = oi.order_id
                JOIN products p
                    ON oi.product_id = p.product_id
                WHERE o.status = 'COMPLETED'
            """)

            return cursor.fetchone()
    finally:
        connection.close()