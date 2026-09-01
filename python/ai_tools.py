from analytics import (
    get_ai_categorization_review_queue,
    get_audit_log,
    get_bookkeeping_summary,
    get_reconciliation_review_queue,
)


def tool_get_bookkeeping_summary():
    return get_bookkeeping_summary()


def tool_get_ai_review_queue():
    return get_ai_categorization_review_queue()


def tool_get_reconciliation_review():
    return get_reconciliation_review_queue()


def tool_get_audit_log():
    return get_audit_log()


TOOL_REGISTRY = {
    "get_bookkeeping_summary": tool_get_bookkeeping_summary,
    "get_ai_review_queue": tool_get_ai_review_queue,
    "get_reconciliation_review": tool_get_reconciliation_review,
    "get_audit_log": tool_get_audit_log,
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
]