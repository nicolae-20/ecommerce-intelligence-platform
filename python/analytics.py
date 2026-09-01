from database import get_connection
from llm_categorizer import (
    is_high_confidence_suggestion,
    suggest_transaction_category,
)

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


def get_accounting_insights():
    financial = get_financial_summary()
    categories = get_profit_by_category()

    total_revenue = float(financial[0] or 0)
    total_cogs = float(financial[1] or 0)
    gross_profit = float(financial[2] or 0)
    gross_margin = float(financial[3] or 0)

    insights = []

    insights.append({
        "type": "financial_summary",
        "title": "Gross profit overview",
        "message": (
            f"Revenue is €{total_revenue:.2f}, "
            f"COGS is €{total_cogs:.2f}, "
            f"and gross profit is €{gross_profit:.2f}."
        )
    })

    insights.append({
        "type": "margin",
        "title": "Gross margin",
        "message": f"Gross margin is {gross_margin:.2f}%."
    })

    if categories:
        top_category = categories[0]
        bottom_category = categories[-1]

        insights.append({
            "type": "top_category",
            "title": "Most profitable category",
            "message": (
                f"{top_category[0]} generated "
                f"€{float(top_category[3]):.2f} in profit."
            )
        })

        insights.append({
            "type": "bottom_category",
            "title": "Lowest profitable category",
            "message": (
                f"{bottom_category[0]} generated "
                f"€{float(bottom_category[3]):.2f} in profit."
            )
        })

    return insights


def get_bookkeeping_summary():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ROUND(
                        SUM(
                            CASE
                                WHEN transaction_type = 'SALE'
                                     AND status = 'POSTED'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        2
                    ) AS total_revenue,

                    ROUND(
                        SUM(
                            CASE
                                WHEN transaction_type IN ('EXPENSE', 'BANK_FEE')
                                     AND status = 'POSTED'
                                THEN ABS(amount)
                                ELSE 0
                            END
                        ),
                        2
                    ) AS total_expenses,

                    ROUND(
                        SUM(
                            CASE
                                WHEN status = 'POSTED'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        2
                    ) AS net_movement,

                    COUNT(
    CASE
        WHEN category IS NULL
             OR reconciliation_status = 'UNMATCHED'
        THEN 1
    END
) AS transactions_requiring_review

                FROM financial_transactions
            """)

            return cursor.fetchone()
    finally:
        connection.close()


def get_transactions_requiring_review():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    transaction_id,
                    transaction_date,
                    transaction_type,
                    description,
                    amount,
                    category,
                    vendor,
                    ai_suggested_category,
                    ai_confidence,
                    reconciliation_status,
                    status,
                    CASE
    WHEN ai_suggested_category IS NULL THEN 'NO_SUGGESTION'
    WHEN ai_confidence >= 0.80 THEN 'HIGH_CONFIDENCE'
    ELSE 'NEEDS_REVIEW'
END AS ai_review_status
                FROM financial_transactions
                WHERE
    category IS NULL
    OR reconciliation_status = 'UNMATCHED'
                ORDER BY transaction_date
            """)

            return cursor.fetchall()
    finally:
        connection.close()

def get_ai_categorization_review_queue():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    transaction_id,
                    transaction_date,
                    transaction_type,
                    description,
                    amount,
                    category,
                    vendor,
                    ai_suggested_category,
                    ai_confidence,
                    reconciliation_status,
                    status,
                    CASE
                        WHEN ai_suggested_category IS NULL
                            THEN 'NO_SUGGESTION'
                        WHEN ai_confidence >= 0.80
                            THEN 'HIGH_CONFIDENCE'
                        ELSE 'NEEDS_REVIEW'
                    END AS ai_review_status
                FROM financial_transactions
                WHERE category IS NULL
                ORDER BY transaction_date
            """)

            return cursor.fetchall()
    finally:
        connection.close()

def approve_transaction_category(transaction_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE financial_transactions ft
                SET
                    accounting_category_id = (
                        SELECT ac.accounting_category_id
                        FROM accounting_categories ac
                        WHERE ac.account_name = ft.ai_suggested_category
                    ),
                    reconciliation_status = 'MATCHED'
                WHERE ft.transaction_id = :transaction_id
                  AND ft.ai_suggested_category IS NOT NULL
                  AND EXISTS (
                      SELECT 1
                      FROM accounting_categories ac
                      WHERE ac.account_name = ft.ai_suggested_category
                        AND ac.is_active = 'Y'
                  )
            """, {"transaction_id": transaction_id})

            if cursor.rowcount == 0:
                return False

            cursor.execute("""
                INSERT INTO audit_log (
                    financial_transaction_id,
                    action,
                    details
                )
                VALUES (
                    :financial_transaction_id,
                    'CATEGORY_APPROVED',
                    'User approved AI-suggested accounting category.'
                )
            """, {
                "financial_transaction_id": transaction_id,
            })

            connection.commit()
            return True
    finally:
        connection.close()


def reject_transaction_category(transaction_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE financial_transactions
                SET
                    ai_suggested_category = NULL,
                    ai_confidence = NULL
                WHERE transaction_id = :transaction_id
            """, {"transaction_id": transaction_id})

            if cursor.rowcount == 0:
                return False

            cursor.execute("""
                INSERT INTO audit_log (
                    financial_transaction_id,
                    action,
                    details
                )
                VALUES (
                    :financial_transaction_id,
                    'CATEGORY_REJECTED',
                    'User rejected AI-suggested accounting category.'
                )
            """, {
                "financial_transaction_id": transaction_id,
            })

            connection.commit()
            return True
    finally:
        connection.close()


def get_bookkeeping_categories():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    accounting_category_id,
                    account_code,
                    account_name,
                    account_type
                FROM accounting_categories
                WHERE is_active = 'Y'
                ORDER BY accounting_category_id
            """)

            return cursor.fetchall()
    finally:
        connection.close()


def assign_transaction_category(transaction_id, category_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE financial_transactions ft
                SET
                    accounting_category_id = :category_id,
                    reconciliation_status = 'MATCHED'
                WHERE ft.transaction_id = :transaction_id
                  AND EXISTS (
                      SELECT 1
                      FROM accounting_categories ac
                      WHERE ac.accounting_category_id = :category_id
                        AND ac.is_active = 'Y'
                  )
            """, {
                "transaction_id": transaction_id,
                "category_id": category_id,
            })

            if cursor.rowcount == 0:
                return False

            connection.commit()
            return True
    finally:
        connection.close()


def cancel_transaction_rejection(transaction_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE financial_transactions
                SET
                    ai_suggested_category = original_ai_category,
                    ai_confidence = original_ai_confidence
                WHERE transaction_id = :transaction_id
                  AND original_ai_category IS NOT NULL
            """, {"transaction_id": transaction_id})

            if cursor.rowcount == 0:
                return False

            cursor.execute("""
                INSERT INTO audit_log (
                    financial_transaction_id,
                    action,
                    details
                )
                VALUES (
                    :financial_transaction_id,
                    'REJECTION_CANCELLED',
                    'User cancelled category rejection and restored AI suggestion.'
                )
            """, {
                "financial_transaction_id": transaction_id,
            })

            connection.commit()
            return True
    finally:
        connection.close()


def run_reconciliation():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                BEGIN
                    reconcile_bank_transactions;
                END;
            """)

            connection.commit()
            return True
    finally:
        connection.close()

def get_reconciliation_review_queue():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    bt.bank_transaction_id,
                    bt.transaction_date,
                    bt.description,
                    bt.amount,
                    bt.status,
                    bt.financial_transaction_id,
                    bt.match_type,
                    bt.match_confidence,
                    ft.transaction_date,
                    ft.description,
                    ft.amount
                FROM bank_transactions bt
                LEFT JOIN financial_transactions ft
                    ON ft.transaction_id = bt.financial_transaction_id
                WHERE bt.status = 'UNMATCHED'
  AND bt.match_type IN (
      'POSSIBLE_MATCH',
      'NO_MATCH'
  )
  AND (
      bt.match_type = 'POSSIBLE_MATCH'
      OR bt.investigation_status IS NULL
  )
                ORDER BY bt.bank_transaction_id
            """)

            return cursor.fetchall()
    finally:
        connection.close()


def reject_bank_transaction_match(bank_transaction_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE bank_transactions
                SET
                    financial_transaction_id = NULL,
                    status = 'UNMATCHED',
                    match_type = 'NO_MATCH',
                    match_confidence = 0
                WHERE bank_transaction_id = :bank_transaction_id
                  AND match_type = 'POSSIBLE_MATCH'
            """, {"bank_transaction_id": bank_transaction_id})

            if cursor.rowcount == 0:
                return False

            cursor.execute("""
                INSERT INTO audit_log (
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                )
                VALUES (
                    :bank_transaction_id,
                    NULL,
                    'RECONCILIATION_REJECTED',
                    'User rejected possible reconciliation match.'
                )
            """, {
                "bank_transaction_id": bank_transaction_id,
            })

            connection.commit()
            return True
    finally:
        connection.close()


def investigate_bank_transaction(bank_transaction_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE bank_transactions
                SET
                    investigation_status = 'INVESTIGATED'
                WHERE bank_transaction_id = :bank_transaction_id
                  AND match_type = 'NO_MATCH'
                  AND status = 'UNMATCHED'
            """, {"bank_transaction_id": bank_transaction_id})

            if cursor.rowcount == 0:
                return False

            cursor.execute("""
                INSERT INTO audit_log (
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                )
                VALUES (
                    :bank_transaction_id,
                    NULL,
                    'TRANSACTION_INVESTIGATED',
                    'User marked unmatched bank transaction as investigated.'
                )
            """, {
                "bank_transaction_id": bank_transaction_id,
            })

            connection.commit()
            return True
    finally:
        connection.close()

def confirm_bank_transaction_match(bank_transaction_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'MATCHED'
                WHERE bank_transaction_id = :bank_transaction_id
                  AND match_type = 'POSSIBLE_MATCH'
                  AND financial_transaction_id IS NOT NULL
            """, {"bank_transaction_id": bank_transaction_id})

            if cursor.rowcount == 0:
                return False

            cursor.execute("""
                SELECT
                    financial_transaction_id
                FROM bank_transactions
                WHERE bank_transaction_id = :bank_transaction_id
            """, {"bank_transaction_id": bank_transaction_id})

            row = cursor.fetchone()

            financial_transaction_id = row[0]

            cursor.execute("""
                INSERT INTO audit_log (
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                )
                VALUES (
                    :bank_transaction_id,
                    :financial_transaction_id,
                    'RECONCILIATION_CONFIRMED',
                    'User confirmed possible reconciliation match.'
                )
            """, {
                "bank_transaction_id": bank_transaction_id,
                "financial_transaction_id": financial_transaction_id,
            })

            connection.commit()
            return True
    finally:
        connection.close()

def log_audit_event(
    action,
    bank_transaction_id=None,
    financial_transaction_id=None,
    details=None,
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_log (
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                )
                VALUES (
                    :bank_transaction_id,
                    :financial_transaction_id,
                    :action,
                    :details
                )
            """, {
                "bank_transaction_id": bank_transaction_id,
                "financial_transaction_id": financial_transaction_id,
                "action": action,
                "details": details,
            })

            connection.commit()
            return True
    finally:
        connection.close()

def get_audit_log():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    audit_id,
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details,
                    created_at
                FROM audit_log
                ORDER BY audit_id DESC
            """)

            return cursor.fetchall()
    finally:
        connection.close()

def categorize_transaction_with_llm(transaction_id, client=None):
    from llm_categorizer import suggest_transaction_category
    from accounting_rag import get_accounting_context

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    description,
                    vendor,
                    amount
                FROM financial_transactions
                WHERE transaction_id = :transaction_id
            """, {"transaction_id": transaction_id})

            row = cursor.fetchone()

            if row is None:
                return False

            description, vendor, amount = row

            context = get_accounting_context(
    description=description,
    vendor=vendor,
)

            suggestion = suggest_transaction_category(
    description=description,
    vendor=vendor,
    amount=float(amount),
    client=client,
    context=context,
)

            cursor.execute("""
                UPDATE financial_transactions
                SET
                    ai_suggested_category = :category,
                    ai_confidence = :confidence
                WHERE transaction_id = :transaction_id
            """, {
                "category": suggestion.category,
                "confidence": suggestion.confidence,
                "transaction_id": transaction_id,
            })

            connection.commit()

            return suggestion
    finally:
        connection.close()


def categorize_uncategorized_transactions(client=None):
    from llm_categorizer import is_high_confidence_suggestion

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    transaction_id
                FROM financial_transactions
                WHERE
                    category IS NULL
                    AND ai_suggested_category IS NULL
                ORDER BY transaction_id
            """)

            transaction_ids = [
                row[0]
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()

    results = []

    for transaction_id in transaction_ids:
        suggestion = categorize_transaction_with_llm(
            transaction_id=transaction_id,
            client=client,
        )

        if suggestion:
            results.append({
        "transaction_id": transaction_id,
        "category": suggestion.category,
        "confidence": suggestion.confidence,
        "high_confidence": suggestion.high_confidence,
    })

    return results