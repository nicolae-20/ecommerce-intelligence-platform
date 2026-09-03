from datetime import datetime

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


def get_financial_statistics(
    start_date=None,
    end_date=None,
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) AS transaction_count,

                    ROUND(
                        AVG(
                            CASE
                                WHEN transaction_type IN ('EXPENSE', 'BANK_FEE')
                                     AND status = 'POSTED'
                                THEN ABS(amount)
                            END
                        ),
                        2
                    ) AS average_expense,

                    ROUND(
                        MAX(
                            CASE
                                WHEN transaction_type IN ('EXPENSE', 'BANK_FEE')
                                     AND status = 'POSTED'
                                THEN ABS(amount)
                            END
                        ),
                        2
                    ) AS largest_expense,

                    SUM(
                        CASE
                            WHEN status = 'POSTED' THEN 1
                            ELSE 0
                        END
                    ) AS posted_count,

                    SUM(
                        CASE
                            WHEN status = 'PENDING' THEN 1
                            ELSE 0
                        END
                    ) AS pending_count,

                    SUM(
                        CASE
                            WHEN category IS NOT NULL THEN 1
                            ELSE 0
                        END
                    ) AS categorized_count,

                    SUM(
                        CASE
                            WHEN category IS NULL THEN 1
                            ELSE 0
                        END
                    ) AS uncategorized_count

                FROM financial_transactions
                WHERE (
                    :start_date IS NULL
                    OR transaction_date >= TO_TIMESTAMP(
                        :start_date,
                        'YYYY-MM-DD'
                    )
                )
                AND (
                    :end_date IS NULL
                    OR transaction_date < TO_TIMESTAMP(
                        :end_date,
                        'YYYY-MM-DD'
                    ) + INTERVAL '1' DAY
                )
            """, {
                "start_date": start_date,
                "end_date": end_date,
            })

            row = cursor.fetchone()

            return {
                "transaction_count": row[0] or 0,
                "average_expense": row[1],
                "largest_expense": row[2],
                "posted_count": row[3] or 0,
                "pending_count": row[4] or 0,
                "categorized_count": row[5] or 0,
                "uncategorized_count": row[6] or 0,
            }
    finally:
        connection.close()


def get_spending_by_category(
    category=None,
    start_date=None,
    end_date=None,
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    NVL(category, 'Uncategorized') AS spending_category,
                    ROUND(SUM(ABS(amount)), 2) AS total_spending,
                    COUNT(*) AS transaction_count
                FROM financial_transactions
                WHERE transaction_type IN ('EXPENSE', 'BANK_FEE')
                AND status = 'POSTED'
                AND (
                    :category IS NULL
                    OR category = :category
                )
                AND (
                    :start_date IS NULL
                    OR transaction_date >= TO_TIMESTAMP(
                        :start_date,
                        'YYYY-MM-DD'
                    )
                )
                AND (
                    :end_date IS NULL
                    OR transaction_date < TO_TIMESTAMP(
                        :end_date,
                        'YYYY-MM-DD'
                    ) + INTERVAL '1' DAY
                )
                GROUP BY NVL(category, 'Uncategorized')
                ORDER BY total_spending DESC, spending_category
            """, {
                "category": category,
                "start_date": start_date,
                "end_date": end_date,
            })

            return [
                {
                    "category": row[0],
                    "total_spending": row[1],
                    "transaction_count": row[2],
                }
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()


def get_vendor_totals(
    vendor=None,
    start_date=None,
    end_date=None,
    limit=10,
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    NVL(vendor, 'No vendor') AS spending_vendor,
                    ROUND(SUM(ABS(amount)), 2) AS total_spending,
                    COUNT(*) AS transaction_count
                FROM financial_transactions
                WHERE transaction_type IN ('EXPENSE', 'BANK_FEE')
                AND status = 'POSTED'
                AND (
                    :vendor IS NULL
                    OR LOWER(vendor) LIKE '%' || LOWER(:vendor) || '%'
                )
                AND (
                    :start_date IS NULL
                    OR transaction_date >= TO_TIMESTAMP(
                        :start_date,
                        'YYYY-MM-DD'
                    )
                )
                AND (
                    :end_date IS NULL
                    OR transaction_date < TO_TIMESTAMP(
                        :end_date,
                        'YYYY-MM-DD'
                    ) + INTERVAL '1' DAY
                )
                GROUP BY NVL(vendor, 'No vendor')
                ORDER BY total_spending DESC, spending_vendor
                FETCH FIRST :limit ROWS ONLY
            """, {
                "vendor": vendor,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
            })

            return [
                {
                    "vendor": row[0],
                    "total_spending": row[1],
                    "transaction_count": row[2],
                }
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()


_FINANCIAL_PERIOD_SQL = {
    "month": (
        "TRUNC(transaction_date, 'MM')",
        "YYYY-MM",
    ),
    "year": (
        "TRUNC(transaction_date, 'YYYY')",
        "YYYY",
    ),
}


def _get_financial_period_sql(period):
    normalized_period = period.lower()

    if normalized_period not in _FINANCIAL_PERIOD_SQL:
        raise ValueError("period must be 'month' or 'year'")

    period_expression, period_format = _FINANCIAL_PERIOD_SQL[normalized_period]
    return normalized_period, period_expression, period_format


def _fill_financial_period_gaps(rows, period):
    if not rows:
        return []

    rows_by_period = {row[0]: row for row in rows}
    current_period = rows[0][0]
    final_period = rows[-1][0]
    complete_rows = []

    while current_period <= final_period:
        complete_rows.append(
            rows_by_period.get(current_period, (current_period, 0, 0))
        )

        if period == "month":
            current_date = datetime.strptime(current_period, "%Y-%m")
            next_year = current_date.year + (current_date.month == 12)
            next_month = 1 if current_date.month == 12 else current_date.month + 1
            current_period = f"{next_year:04d}-{next_month:02d}"
        else:
            current_period = str(int(current_period) + 1)

    return complete_rows


def get_revenue_analysis(
    start_date=None,
    end_date=None,
    period="month",
):
    normalized_period, period_expression, period_format = (
        _get_financial_period_sql(period)
    )
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    TO_CHAR({period_expression}, '{period_format}') AS period,
                    ROUND(SUM(amount), 2) AS total_revenue,
                    COUNT(*) AS transaction_count
                FROM financial_transactions
                WHERE transaction_type = 'SALE'
                AND status = 'POSTED'
                AND (
                    :start_date IS NULL
                    OR transaction_date >= TO_TIMESTAMP(
                        :start_date,
                        'YYYY-MM-DD'
                    )
                )
                AND (
                    :end_date IS NULL
                    OR transaction_date < TO_TIMESTAMP(
                        :end_date,
                        'YYYY-MM-DD'
                    ) + INTERVAL '1' DAY
                )
                GROUP BY {period_expression}
                ORDER BY {period_expression}
            """, {
                "start_date": start_date,
                "end_date": end_date,
            })

            rows = _fill_financial_period_gaps(
                cursor.fetchall(),
                normalized_period,
            )
            periods = [
                {
                    "period": row[0],
                    "total_revenue": row[1],
                    "transaction_count": row[2],
                }
                for row in rows
            ]

            return {
                "period": normalized_period,
                "total_revenue": round(
                    sum((item["total_revenue"] or 0) for item in periods),
                    2,
                ),
                "transaction_count": sum(
                    item["transaction_count"] for item in periods
                ),
                "periods": periods,
            }
    finally:
        connection.close()


def get_expense_trends(
    category=None,
    vendor=None,
    start_date=None,
    end_date=None,
    period="month",
):
    normalized_period, period_expression, period_format = (
        _get_financial_period_sql(period)
    )
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    TO_CHAR({period_expression}, '{period_format}') AS period,
                    ROUND(SUM(ABS(amount)), 2) AS total_expenses,
                    COUNT(*) AS transaction_count
                FROM financial_transactions
                WHERE transaction_type IN ('EXPENSE', 'BANK_FEE')
                AND status = 'POSTED'
                AND (
                    :category IS NULL
                    OR category = :category
                )
                AND (
                    :vendor IS NULL
                    OR LOWER(vendor) LIKE '%' || LOWER(:vendor) || '%'
                )
                AND (
                    :start_date IS NULL
                    OR transaction_date >= TO_TIMESTAMP(
                        :start_date,
                        'YYYY-MM-DD'
                    )
                )
                AND (
                    :end_date IS NULL
                    OR transaction_date < TO_TIMESTAMP(
                        :end_date,
                        'YYYY-MM-DD'
                    ) + INTERVAL '1' DAY
                )
                GROUP BY {period_expression}
                ORDER BY {period_expression}
            """, {
                "category": category,
                "vendor": vendor,
                "start_date": start_date,
                "end_date": end_date,
            })

            periods = []
            previous_total = None

            rows = _fill_financial_period_gaps(
                cursor.fetchall(),
                normalized_period,
            )

            for row in rows:
                total_expenses = row[1]
                change_amount = None
                change_percentage = None

                if previous_total is not None:
                    change_amount = round(
                        total_expenses - previous_total,
                        2,
                    )

                    if previous_total != 0:
                        change_percentage = round(
                            (change_amount / previous_total) * 100,
                            2,
                        )

                periods.append({
                    "period": row[0],
                    "total_expenses": total_expenses,
                    "transaction_count": row[2],
                    "change_amount": change_amount,
                    "change_percentage": change_percentage,
                })
                previous_total = total_expenses

            return {
                "period": normalized_period,
                "category": category,
                "vendor": vendor,
                "total_expenses": round(
                    sum((item["total_expenses"] or 0) for item in periods),
                    2,
                ),
                "transaction_count": sum(
                    item["transaction_count"] for item in periods
                ),
                "periods": periods,
            }
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

def investigate_uncategorized_transaction(
    transaction_id,
    client=None,
):
    from accounting_rag import get_accounting_context
    from llm_categorizer import (
        suggest_transaction_category,
        validate_category_suggestion,
    )

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
                    status
                FROM financial_transactions
                WHERE transaction_id = :transaction_id
            """, {
                "transaction_id": transaction_id,
            })

            row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    transaction = {
        "transaction_id": row[0],
        "transaction_date": row[1],
        "transaction_type": row[2],
        "description": row[3],
        "amount": row[4],
        "category": row[5],
        "vendor": row[6],
        "reconciliation_status": row[9],
        "status": row[10],
    }

    current_ai_suggestion = (
        {
            "category": row[7],
            "confidence": row[8],
        }
        if row[7] is not None
        else None
    )

    if row[5] is not None:
        return {
            "transaction": transaction,
            "investigation_status": "ALREADY_CATEGORIZED",
            "current_ai_suggestion": current_ai_suggestion,
            "evidence": {
                "available_categories": [],
                "historical_examples": [],
                "supporting_example_count": 0,
            },
            "recommendation": None,
            "requires_human_review": False,
        }

    context = get_accounting_context(
        description=row[3],
        vendor=row[6],
    )

    suggestion = suggest_transaction_category(
        description=row[3],
        vendor=row[6],
        amount=float(row[4]),
        client=client,
        context=context,
    )

    # Validate even in deterministic Demo Mode. The existing categorizer
    # validates model responses, but Demo Mode should obey the same trust
    # boundary for investigation results.
    suggestion = validate_category_suggestion(
        suggestion,
        context,
    )

    supporting_examples = [
        example
        for example in context.examples
        if example["category"] == suggestion.category
    ]

    if supporting_examples:
        rationale = (
            f"{len(supporting_examples)} confirmed historical "
            f"example(s) support the recommended category "
            f"{suggestion.category}. Vendor and description context "
            f"were used as supporting evidence."
        )
    elif context.examples:
        rationale = (
            f"Relevant confirmed historical examples were retrieved, "
            f"but none directly support {suggestion.category}. "
            f"The recommendation is based on the transaction description, "
            f"vendor, and available Chart of Accounts."
        )
    else:
        rationale = (
            f"No relevant confirmed historical examples were found. "
            f"The recommendation is based on the transaction description, "
            f"vendor, and available Chart of Accounts."
        )

    return {
        "transaction": transaction,
        "investigation_status": "RECOMMENDATION_READY",
        "current_ai_suggestion": current_ai_suggestion,
        "evidence": {
            "available_categories": [
                category["account_name"]
                for category in context.categories
            ],
            "historical_examples": context.examples,
            "supporting_example_count": len(supporting_examples),
        },
        "recommendation": {
            "category": suggestion.category,
            "confidence": suggestion.confidence,
            "high_confidence": suggestion.high_confidence,
            "rationale": rationale,
        },
        "requires_human_review": True,
    }


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
