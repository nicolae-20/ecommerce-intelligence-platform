from dataclasses import dataclass
from typing import Any

from ai_tools import TOOL_REGISTRY


@dataclass
class AssistantResponse:
    message: str
    tool_name: str | None = None
    tool_result: Any = None


def _select_tool(question: str) -> str | None:
    question_lower = question.lower()

    if (
        "bookkeeping summary" in question_lower
        or "financial summary" in question_lower
        or "bookkeeping status" in question_lower
    ):
        return "get_bookkeeping_summary"

    if (
        "ai review" in question_lower
        or "categorization review" in question_lower
        or "categorization" in question_lower
    ):
        return "get_ai_review_queue"

    if (
        "reconciliation" in question_lower
        or "unmatched" in question_lower
        or "bank matches" in question_lower
    ):
        return "get_reconciliation_review"

    if (
        "audit log" in question_lower
        or "audit activity" in question_lower
        or "recent audit" in question_lower
    ):
        return "get_audit_log"

    return None




def ask_assistant(question: str) -> AssistantResponse:
    tool_name = _select_tool(question)

    if tool_name is None:
        return AssistantResponse(
            message=(
                "I can help with bookkeeping summary, "
                "AI categorization review, reconciliation, "
                "and audit activity."
            )
        )

    tool = TOOL_REGISTRY[tool_name]
    result = tool()

    if tool_name == "get_bookkeeping_summary":
        message = _format_bookkeeping_summary(result)

    elif tool_name == "get_ai_review_queue":
        message = _format_ai_review_queue(result)

    elif tool_name == "get_reconciliation_review":
        message = _format_reconciliation_review(result)

    elif tool_name == "get_audit_log":
        message = _format_audit_log(result)

    else:
        message = f"Executed tool: {tool_name}"

    return AssistantResponse(
        message=message,
        tool_name=tool_name,
        tool_result=result,
    )

def _format_bookkeeping_summary(result: Any) -> str:
    if not result:
        return "No bookkeeping summary is available."

    total_revenue = result[0] or 0
    total_expenses = result[1] or 0
    net_movement = result[2] or 0
    transactions_requiring_review = result[3] or 0

    return (
        f"Your current bookkeeping summary is: "
        f"revenue €{total_revenue:.2f}, "
        f"expenses €{total_expenses:.2f}, "
        f"net movement €{net_movement:.2f}, "
        f"and {transactions_requiring_review} "
        f"transactions requiring review."
    )

def _format_ai_review_queue(result: Any) -> str:
    if not result:
        return "There are no transactions requiring AI categorization review."

    lines = [
        f"{len(result)} transaction(s) require AI categorization review:"
    ]

    for item in result:
        transaction_id = item[0]
        description = item[3]
        amount = item[4]
        suggestion = item[7]
        confidence = item[8]

        confidence_text = (
            f"{float(confidence) * 100:.0f}%"
            if confidence is not None
            else "N/A"
        )

        lines.append(
            f"- Transaction {transaction_id}: "
            f"{description}, "
            f"amount €{float(amount):.2f}, "
            f"AI suggestion: {suggestion or 'None'}, "
            f"confidence: {confidence_text}."
        )

    return "\n".join(lines)


def _format_reconciliation_review(result: Any) -> str:
    if not result:
        return "There are no reconciliation items requiring review."

    lines = [
        f"{len(result)} reconciliation item(s) require review:"
    ]

    for item in result:
        bank_transaction_id = item[0]
        bank_description = item[2] or "No description"
        bank_amount = float(item[3])
        status = item[4]
        match_type = item[6]
        confidence = item[7]

        confidence_text = (
            f"{float(confidence) * 100:.0f}%"
            if confidence is not None
            else "N/A"
        )

        lines.append(
            f"- Bank transaction {bank_transaction_id}: "
            f"{bank_description}, "
            f"amount €{bank_amount:.2f}, "
            f"status: {status}, "
            f"match type: {match_type}, "
            f"confidence: {confidence_text}."
        )

    return "\n".join(lines)


def _format_audit_log(result: Any) -> str:
    if not result:
        return "There are no audit log entries."

    lines = [
        f"{len(result)} recent audit log entr{'y' if len(result) == 1 else 'ies'}:"
    ]

    for item in result:
        audit_id = item[0]
        action = item[3]
        details = item[4] or "No details"
        created_at = item[5]

        lines.append(
            f"- Audit {audit_id}: "
            f"{action} at {created_at}. "
            f"{details}"
        )

    return "\n".join(lines)