from analytics import (
    get_ai_categorization_review_queue,
    get_audit_log,
    get_bookkeeping_summary,
    get_reconciliation_review_queue,
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
        "absolute transaction amount, and transaction status."
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
