import os

import oracledb
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN"),
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