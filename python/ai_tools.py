from analytics import (
    get_ai_categorization_review_queue,
    get_audit_log,
    get_bookkeeping_summary,
    get_expense_trends,
    get_financial_statistics,
    get_reconciliation_review_queue,
    get_revenue_analysis,
    get_spending_by_category,
    get_vendor_totals,
)
from database import get_connection


def tool_get_bookkeeping_summary():
    return get_bookkeeping_summary()


def tool_get_ai_review_queue():
    return get_ai_categorization_review_queue()


def tool_get_reconciliation_review():
    return get_reconciliation_review_queue()


def tool_get_audit_log():
    return get_audit_log()


def tool_get_spending_by_category(
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    return get_spending_by_category(
        category=category,
        start_date=start_date,
        end_date=end_date,
    )


def tool_get_vendor_totals(
    vendor: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
):
    return get_vendor_totals(
        vendor=vendor,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


def tool_get_financial_statistics(
    start_date: str | None = None,
    end_date: str | None = None,
):
    return get_financial_statistics(
        start_date=start_date,
        end_date=end_date,
    )


def tool_get_revenue_analysis(
    start_date: str | None = None,
    end_date: str | None = None,
    period: str = "month",
):
    return get_revenue_analysis(
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


def tool_get_expense_trends(
    category: str | None = None,
    vendor: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    period: str = "month",
):
    return get_expense_trends(
        category=category,
        vendor=vendor,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


def tool_get_transactions_by_date(
    start_date: str,
    end_date: str,
):
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
                WHERE transaction_date >= TO_TIMESTAMP(
                    :start_date,
                    'YYYY-MM-DD'
                )
                AND transaction_date < TO_TIMESTAMP(
                    :end_date,
                    'YYYY-MM-DD'
                ) + INTERVAL '1' DAY
                ORDER BY transaction_date, transaction_id
            """, {
                "start_date": start_date,
                "end_date": end_date,
            })

            return [
                {
                    "transaction_id": row[0],
                    "transaction_date": row[1],
                    "transaction_type": row[2],
                    "description": row[3],
                    "amount": row[4],
                    "category": row[5],
                    "vendor": row[6],
                    "ai_suggested_category": row[7],
                    "ai_confidence": row[8],
                    "reconciliation_status": row[9],
                    "status": row[10],
                }
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()

def tool_get_transactions(
    category: str | None = None,
    vendor: str | None = None,
    transaction_type: str | None = None,
    reconciliation_status: str | None = None,
    categorization_state: str | None = None,
    min_ai_confidence: float | None = None,
    max_ai_confidence: float | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
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
                WHERE
                    (:category IS NULL OR category = :category)
                AND (
                    :vendor IS NULL
                    OR LOWER(vendor) LIKE '%' || LOWER(:vendor) || '%'
                )
                AND (
                    :transaction_type IS NULL
                    OR transaction_type = :transaction_type
                )
                AND (
                    :reconciliation_status IS NULL
                    OR reconciliation_status = :reconciliation_status
                )
                AND (
                    :categorization_state IS NULL
                    OR :categorization_state = CASE
                        WHEN category IS NULL THEN 'UNCATEGORIZED'
                        ELSE 'CATEGORIZED'
                    END
                )
                AND (
                    :min_ai_confidence IS NULL
                    OR ai_confidence >= :min_ai_confidence
                )
                AND (
                    :max_ai_confidence IS NULL
                    OR ai_confidence < :max_ai_confidence
                )
                AND (
                    :min_amount IS NULL
                    OR ABS(amount) >= :min_amount
                )
                AND (
                    :max_amount IS NULL
                    OR ABS(amount) <= :max_amount
                )
                AND (
                    :status IS NULL
                    OR status = :status
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
                ORDER BY transaction_date, transaction_id
            """, {
                "category": category,
                "vendor": vendor,
                "transaction_type": transaction_type,
                "reconciliation_status": reconciliation_status,
                "categorization_state": categorization_state,
                "min_ai_confidence": min_ai_confidence,
                "max_ai_confidence": max_ai_confidence,
                "min_amount": min_amount,
                "max_amount": max_amount,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
            })

            return [
                {
                    "transaction_id": row[0],
                    "transaction_date": row[1],
                    "transaction_type": row[2],
                    "description": row[3],
                    "amount": row[4],
                    "category": row[5],
                    "vendor": row[6],
                    "ai_suggested_category": row[7],
                    "ai_confidence": row[8],
                    "reconciliation_status": row[9],
                    "status": row[10],
                }
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()

TOOL_REGISTRY = {
    "get_bookkeeping_summary": tool_get_bookkeeping_summary,
    "get_ai_review_queue": tool_get_ai_review_queue,
    "get_reconciliation_review": tool_get_reconciliation_review,
    "get_audit_log": tool_get_audit_log,
    "get_spending_by_category": tool_get_spending_by_category,
    "get_vendor_totals": tool_get_vendor_totals,
    "get_revenue_analysis": tool_get_revenue_analysis,
    "get_expense_trends": tool_get_expense_trends,
    "get_financial_statistics": tool_get_financial_statistics,
    "get_transactions_by_date": tool_get_transactions_by_date,
    "get_transactions": tool_get_transactions,
}


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "get_bookkeeping_summary",
        "description": (
            "Get the current bookkeeping financial summary, "
            "including revenue, expenses, net movement, "
            "and the number of transactions requiring review."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_ai_review_queue",
        "description": (
            "Get financial transactions that currently need "
            "AI categorization review."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_reconciliation_review",
        "description": (
            "Get bank transactions that currently require "
            "reconciliation review."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_audit_log",
        "description": (
            "Get the most recent bookkeeping and reconciliation "
            "audit log entries."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_spending_by_category",
        "description": (
            "Aggregate posted expense and bank-fee spending by accounting "
            "category using absolute transaction amounts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": ["string", "null"],
                    "description": (
                        "Optional accounting category, such as Software."
                    ),
                },
                "start_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive end date in YYYY-MM-DD format.",
                },
            },
            "required": ["category", "start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_vendor_totals",
        "description": (
            "Aggregate posted expense and bank-fee spending by vendor using "
            "absolute transaction amounts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "vendor": {
                    "type": ["string", "null"],
                    "description": "Optional full or partial vendor name.",
                },
                "start_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive end date in YYYY-MM-DD format.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Maximum number of vendor groups to return.",
                },
            },
            "required": ["vendor", "start_date", "end_date", "limit"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_financial_statistics",
        "description": (
            "Get deterministic bookkeeping statistics from financial "
            "transactions, including transaction counts, posted expense "
            "average and maximum, status counts, and categorization counts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive end date in YYYY-MM-DD format.",
                },
            },
            "required": ["start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_revenue_analysis",
        "description": (
            "Analyze posted SALE revenue from financial transactions, "
            "including totals and monthly or yearly periods."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive end date in YYYY-MM-DD format.",
                },
                "period": {
                    "type": "string",
                    "enum": ["month", "year"],
                    "description": "Calendar period used to group revenue.",
                },
            },
            "required": ["start_date", "end_date", "period"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_expense_trends",
        "description": (
            "Analyze posted EXPENSE and BANK_FEE spending over monthly or "
            "yearly periods, with period-over-period changes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": ["string", "null"],
                    "description": "Optional accounting category filter.",
                },
                "vendor": {
                    "type": ["string", "null"],
                    "description": "Optional full or partial vendor filter.",
                },
                "start_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": ["string", "null"],
                    "description": "Optional inclusive end date in YYYY-MM-DD format.",
                },
                "period": {
                    "type": "string",
                    "enum": ["month", "year"],
                    "description": "Calendar period used to group expenses.",
                },
            },
            "required": [
                "category",
                "vendor",
                "start_date",
                "end_date",
                "period",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_transactions_by_date",
        "description": (
            "Get financial transactions within an inclusive date range. "
            "Use ISO dates in YYYY-MM-DD format."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format.",
                },
            },
            "required": [
                "start_date",
                "end_date",
            ],
            "additionalProperties": False,
        },
    },
    {
    "type": "function",
    "name": "get_transactions",
    "description": (
        "Get financial transactions using optional filters "
        "for accounting category, vendor, transaction type, "
        "reconciliation status, categorization state, AI suggestion "
        "confidence, absolute transaction amount, and transaction status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": ["string", "null"],
                "description": (
                    "Accounting category, such as Software "
                    "or Office Supplies."
                ),
            },
            "vendor": {
                "type": ["string", "null"],
                "description": (
                    "Vendor name or partial vendor name, such as "
                    "Microsoft or Amazon Web Services."
                ),
            },
            "transaction_type": {
                "type": ["string", "null"],
                "enum": ["SALE", "EXPENSE", "BANK_FEE", None],
                "description": (
                    "Transaction type: SALE, EXPENSE, or BANK_FEE."
                ),
            },
            "reconciliation_status": {
                "type": ["string", "null"],
                "enum": ["MATCHED", "UNMATCHED", None],
                "description": (
                    "Transaction reconciliation status: "
                    "MATCHED or UNMATCHED."
                ),
            },
            "categorization_state": {
                "type": ["string", "null"],
                "enum": ["CATEGORIZED", "UNCATEGORIZED", None],
                "description": (
                    "Whether a transaction has an assigned category: "
                    "CATEGORIZED or UNCATEGORIZED."
                ),
            },
            "min_ai_confidence": {
                "type": ["number", "null"],
                "minimum": 0,
                "maximum": 1,
                "description": (
                    "Inclusive minimum stored AI suggestion confidence "
                    "on the 0.0 to 1.0 scale."
                ),
            },
            "max_ai_confidence": {
                "type": ["number", "null"],
                "minimum": 0,
                "maximum": 1,
                "description": (
                    "Exclusive maximum stored AI suggestion confidence "
                    "on the 0.0 to 1.0 scale."
                ),
            },
            "min_amount": {
                "type": ["number", "null"],
                "description": (
                    "Minimum absolute transaction amount in EUR."
                ),
            },
            "max_amount": {
                "type": ["number", "null"],
                "description": (
                    "Maximum absolute transaction amount in EUR."
                ),
            },
            "status": {
                "type": ["string", "null"],
                "description": (
                    "Transaction status, such as POSTED or PENDING."
                ),
            },
            "start_date": {
    "type": ["string", "null"],
    "description": "Optional start date in YYYY-MM-DD format.",
},
"end_date": {
    "type": ["string", "null"],
    "description": "Optional end date in YYYY-MM-DD format.",
},
        },
        "required": [
            "category",
            "vendor",
            "transaction_type",
            "reconciliation_status",
            "categorization_state",
            "min_ai_confidence",
            "max_ai_confidence",
            "min_amount",
            "max_amount",
            "status",
            "start_date",
            "end_date",
        ],
        "additionalProperties": False,
    },
},
]
