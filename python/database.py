import oracledb


def get_connection():
    return oracledb.connect(
        user="SQL_LEARNING",
        password="Rtuewn24!?",
        dsn="localhost:1521/freepdb1",
    )


def get_customers():
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
                ORDER BY customer_id
            """)

            return cursor.fetchall()
    finally:
        connection.close()