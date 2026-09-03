from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
import calendar
import re

from ai_tools import TOOL_REGISTRY
from llm_categorizer import AI_CONFIDENCE_THRESHOLD


KNOWN_VENDORS = (
    "Amazon Web Services",
    "Microsoft",
    "Office Depot",
)

KNOWN_CATEGORIES = (
    "Sales Revenue",
    "Cost of Goods Sold",
    "Software",
    "Office Supplies",
    "Bank Fees",
    "Travel",
    "Advertising",
    "Utilities",
)

MONTH_NAMES = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)

@dataclass
class AssistantResponse:
    message: str
    tool_name: str | None = None
    tool_result: Any = None


def _extract_known_vendor(question: str) -> str | None:
    question_lower = question.lower()

    for vendor in KNOWN_VENDORS:
        if vendor.lower() in question_lower:
            return vendor

    return None


def _extract_known_category(question: str) -> str | None:
    question_lower = question.lower()

    for category in KNOWN_CATEGORIES:
        if category.lower() in question_lower:
            return category

    return None


def _extract_top_limit(question: str, default: int = 10) -> int:
    match = re.search(r"\btop\s+(\d+)\b", question.lower())

    if match is None:
        return default

    return min(max(int(match.group(1)), 1), 100)


def _extract_bank_transaction_id(question: str) -> int | None:
    match = re.search(
        r"\bbank\s+transaction(?:\s+id)?\s*#?\s*(\d+)\b",
        question,
        re.IGNORECASE,
    )

    if match is None:
        return None

    return int(match.group(1))


def _extract_transaction_id(question: str) -> int | None:
    match = re.search(
        r"\btransaction(?:\s+id)?\s*#?\s*(\d+)\b",
        question,
        re.IGNORECASE,
    )

    if match is None:
        return None

    return int(match.group(1))


def _extract_analysis_period(question: str) -> str:
    question_lower = question.lower()

    if re.search(
        r"\b(?:yearly|annual|annually|by year)\b",
        question_lower,
    ):
        return "year"

    return "month"


def _extract_transaction_type(question: str) -> str | None:
    question_lower = question.lower()

    if re.search(r"\bbank fees?\b", question_lower):
        return "BANK_FEE"

    if re.search(r"\bexpenses?\b", question_lower):
        return "EXPENSE"

    if (
        re.search(r"\bsales?\b", question_lower)
        and "sales revenue" not in question_lower
    ):
        return "SALE"

    return None


def _extract_reconciliation_status(question: str) -> str | None:
    question_lower = question.lower()

    if re.search(r"\bunmatched\b", question_lower):
        return "UNMATCHED"

    if re.search(r"\bmatched\b", question_lower):
        return "MATCHED"

    return None


def _extract_categorization_state(question: str) -> str | None:
    question_lower = question.lower()

    if re.search(r"\buncategorized\b", question_lower):
        return "UNCATEGORIZED"

    if re.search(r"\bcategorized\b", question_lower):
        return "CATEGORIZED"

    return None


def _extract_ai_confidence_filters(
    question: str,
) -> tuple[float | None, float | None]:
    question_lower = question.lower()

    below_match = re.search(
        r"(?:below|under|less than)\s*(\d+(?:\.\d+)?)\s*%\s*confidence",
        question_lower,
    )

    if below_match:
        return None, float(below_match.group(1)) / 100

    minimum_match = re.search(
        r"at least\s*(\d+(?:\.\d+)?)\s*%\s*confidence",
        question_lower,
    )

    if minimum_match:
        return float(minimum_match.group(1)) / 100, None

    if re.search(r"\bhigh[- ]confidence\b", question_lower):
        return AI_CONFIDENCE_THRESHOLD, None

    return None, None


def _extract_amount_filters(
    question: str,
) -> tuple[float | None, float | None]:
    question_lower = question.lower()
    amount_pattern = (
        r"€?\s*(\d+(?:\.\d+)?)(?!\d|\s*%)\s*(?:euros?)?"
    )

    range_match = re.search(
        rf"\bbetween\s+{amount_pattern}\s+and\s+{amount_pattern}",
        question_lower,
    )

    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    minimum_match = re.search(
        rf"\b(?:over|above|more than|at least)\s+{amount_pattern}",
        question_lower,
    )
    maximum_match = re.search(
        rf"\b(?:under|below|less than|at most)\s+{amount_pattern}",
        question_lower,
    )

    minimum = float(minimum_match.group(1)) if minimum_match else None
    maximum = float(maximum_match.group(1)) if maximum_match else None
    return minimum, maximum


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


def _select_tools(question: str) -> list[str]:
    question_lower = question.lower()
    category = _extract_known_category(question)
    vendor = _extract_known_vendor(question)
    transaction_type = _extract_transaction_type(question)
    reconciliation_status = _extract_reconciliation_status(question)
    categorization_state = _extract_categorization_state(question)
    min_ai_confidence, max_ai_confidence = _extract_ai_confidence_filters(
        question
    )
    min_amount, max_amount = _extract_amount_filters(question)
    transaction_id = _extract_transaction_id(question)
    bank_transaction_id = _extract_bank_transaction_id(question)

    has_spending_language = bool(
        re.search(r"\b(?:spend|spent|spending)\b", question_lower)
    )

    has_trend_language = bool(
        re.search(
            r"\b(?:trend|trends|monthly|yearly|annual|annually|"
            r"month-over-month|by month|by year)\b",
            question_lower,
        )
    )

    wants_category_spending = (
        not has_trend_language
        and (
            "spending by category" in question_lower
            or (
                "expense category" in question_lower
                and "most" in question_lower
            )
            or (category is not None and has_spending_language)
        )
    )

    wants_vendor_spending = (
        not has_trend_language
        and (
            "vendor spending" in question_lower
            or (
                "vendors" in question_lower
                and "cost" in question_lower
            )
            or (vendor is not None and has_spending_language)
        )
    )

    wants_revenue_analysis = (
        "revenue" in question_lower
        and "transaction" not in question_lower
        and "bookkeeping summary" not in question_lower
        and "financial summary" not in question_lower
    )

    wants_expense_trends = (
        bool(re.search(r"\b(?:expenses?|spending)\b", question_lower))
        and has_trend_language
    )

    has_investigation_language = bool(
        re.search(
            r"\b(?:why|investigate|investigation|recommend|"
            r"recommendation|context|evidence)\b",
            question_lower,
        )
    )

    wants_uncategorized_investigation = (
        transaction_id is not None
        and (
            (
                "uncategorized" in question_lower
                and has_investigation_language
            )
            or (
                "category" in question_lower
                and bool(
                    re.search(
                        r"\b(?:recommend|recommendation)\b",
                        question_lower,
                    )
                )
            )
            or (
                bool(
                    re.search(
                        r"\b(?:context|evidence)\b",
                        question_lower,
                    )
                )
                and bool(
                    re.search(
                        r"\b(?:recommend|recommendation)\b",
                        question_lower,
                    )
                )
            )
        )
    )

    wants_financial_statistics = (
        "financial statistics" in question_lower
        or "financial stats" in question_lower
        or "transaction count" in question_lower
        or bool(
            re.search(
                r"\b(?:average|largest)\s+expense\b",
                question_lower,
            )
        )
        or (
            "posted" in question_lower
            and "pending" in question_lower
            and bool(
                re.search(
                    r"\b(?:count|counts|how many|versus|vs\.?)\b",
                    question_lower,
                )
            )
        )
        or (
            "categorized" in question_lower
            and "uncategorized" in question_lower
            and bool(
                re.search(
                    r"\b(?:count|counts|how many|versus|vs\.?)\b",
                    question_lower,
                )
            )
        )
    )

    wants_financial_anomalies = bool(
        re.search(
            r"\b(?:anomal(?:y|ies)|unusual(?:ly)?|suspicious|"
            r"duplicate(?:s|d)?|repeated\s+bank\s+fees?)\b",
            question_lower,
        )
    )

    has_reconciliation_investigation_language = bool(
        re.search(
            r"\b(?:why|investigate|investigation|explain|"
            r"evidence|possible match|match confidence)\b",
            question_lower,
        )
    )

    wants_reconciliation_investigation = (
        bank_transaction_id is not None
        and (
            has_reconciliation_investigation_language
            or "unmatched" in question_lower
        )
    )

    has_financial_analytics_request = (
        wants_category_spending
        or wants_vendor_spending
        or wants_revenue_analysis
        or wants_expense_trends
        or wants_financial_statistics
        or wants_financial_anomalies
    )
    has_reconciliation_transaction_context = (
        reconciliation_status is not None
        and (
            "transaction" in question_lower
            or vendor is not None
            or transaction_type is not None
        )
    )

    tools: list[str] = []

    if (
        "bookkeeping summary" in question_lower
        or "financial summary" in question_lower
        or "bookkeeping overview" in question_lower
    ):
        tools.append("get_bookkeeping_summary")

    if wants_uncategorized_investigation:
        tools.append("investigate_uncategorized_transaction")

    if (
        "ai review" in question_lower
        or "ai categorization" in question_lower
        or "categorization review" in question_lower
    ):
        tools.append("get_ai_review_queue")

    if (
        not wants_reconciliation_investigation
        and (
            "reconciliation" in question_lower
            or "bank match" in question_lower
            or "bank matches" in question_lower
            or (
                "unmatched" in question_lower
                and not has_reconciliation_transaction_context
            )
        )
    ):
        tools.append("get_reconciliation_review")

    if wants_reconciliation_investigation:
        tools.append("investigate_reconciliation_issue")

    if (
        "audit log" in question_lower
        or "audit activity" in question_lower
        or "recent activity" in question_lower
    ):
        tools.append("get_audit_log")

    if wants_financial_anomalies:
        tools.append("get_financial_anomalies")

    if wants_category_spending:
        tools.append("get_spending_by_category")

    if wants_vendor_spending:
        tools.append("get_vendor_totals")

    if wants_revenue_analysis:
        tools.append("get_revenue_analysis")

    if wants_expense_trends:
        tools.append("get_expense_trends")

    if wants_financial_statistics:
        tools.append("get_financial_statistics")

    has_transaction_filters = (
        "expenses over" in question_lower
        or "expenses above" in question_lower
        or "expenses under" in question_lower
        or "transactions over" in question_lower
        or "transactions above" in question_lower
        or "transactions under" in question_lower
        or "pending transactions" in question_lower
        or "posted transactions" in question_lower
        or vendor is not None
        or transaction_type is not None
        or has_reconciliation_transaction_context
        or categorization_state is not None
        or min_ai_confidence is not None
        or max_ai_confidence is not None
        or min_amount is not None
        or max_amount is not None
    )

    has_explicit_date_range_request = (
        "transactions from" in question_lower
        or "transactions between" in question_lower
        or "transactions during" in question_lower
    )
    has_relative_date_request = bool(
        re.search(
            r"\b(?:this month|last month|this year|last 30 days)\b",
            question_lower,
        )
    )

    if not (
        has_financial_analytics_request
        or wants_uncategorized_investigation
        or wants_reconciliation_investigation
    ):
        if has_transaction_filters or has_relative_date_request:
            tools.append("get_transactions")

        elif has_explicit_date_range_request:
            tools.append("get_transactions_by_date")

    return list(dict.fromkeys(tools))




def ask_assistant(question: str) -> AssistantResponse:
    mode = os.getenv(
        "AI_ASSISTANT_MODE",
        "demo",
    ).lower()

    if mode == "demo":
        return _ask_assistant_demo(question)

    if mode == "openai":
        return ask_assistant_openai(question)

    raise ValueError(
        "AI_ASSISTANT_MODE must be 'demo' or 'openai'"
    )


def _current_local_date() -> date:
    return datetime.now().astimezone().date()


def _extract_date_range(
    question: str,
    reference_date: date | None = None,
) -> tuple[str, str] | None:
    matches = re.findall(
        r"\b(20\d{2}-\d{2}-\d{2})\b",
        question,
    )

    if len(matches) >= 2:
        return matches[0], matches[1]

    question_lower = question.lower()
    today = reference_date or _current_local_date()

    month_match = re.search(
        rf"\b({'|'.join(MONTH_NAMES)})(?:\s+(20\d{{2}}))?\b",
        question_lower,
    )

    if month_match:
        month_number = MONTH_NAMES.index(month_match.group(1)) + 1
        year = int(month_match.group(2)) if month_match.group(2) else today.year

        if month_match.group(2) is None and month_number > today.month:
            year -= 1

        start_date = date(year, month_number, 1)
        end_date = date(
            year,
            month_number,
            calendar.monthrange(year, month_number)[1],
        )
        return start_date.isoformat(), end_date.isoformat()

    if re.search(r"\blast 30 days\b", question_lower):
        start_date = today - timedelta(days=29)
        return start_date.isoformat(), today.isoformat()

    if re.search(r"\blast month\b", question_lower):
        current_month_start = today.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)
        return previous_month_start.isoformat(), previous_month_end.isoformat()

    if re.search(r"\bthis month\b", question_lower):
        return today.replace(day=1).isoformat(), today.isoformat()

    if re.search(r"\bthis year\b", question_lower):
        return today.replace(month=1, day=1).isoformat(), today.isoformat()

    return None


def _extract_transaction_filters(
    question: str,
) -> dict[str, Any]:
    question_lower = question.lower()

    filters: dict[str, Any] = {
    "category": None,
    "vendor": None,
    "transaction_type": None,
    "reconciliation_status": None,
    "categorization_state": None,
    "min_ai_confidence": None,
    "max_ai_confidence": None,
    "min_amount": None,
    "max_amount": None,
    "status": None,
    "start_date": None,
    "end_date": None,
    }

    filters["category"] = _extract_known_category(question)

    filters["vendor"] = _extract_known_vendor(question)
    filters["transaction_type"] = _extract_transaction_type(question)
    filters["reconciliation_status"] = _extract_reconciliation_status(question)
    filters["categorization_state"] = _extract_categorization_state(question)
    (
        filters["min_ai_confidence"],
        filters["max_ai_confidence"],
    ) = _extract_ai_confidence_filters(question)

    filters["min_amount"], filters["max_amount"] = (
        _extract_amount_filters(question)
    )

    if "pending" in question_lower:
        filters["status"] = "PENDING"

    elif "posted" in question_lower:
        filters["status"] = "POSTED"

    date_range = _extract_date_range(question)

    if date_range is not None:
        filters["start_date"] = date_range[0]
        filters["end_date"] = date_range[1]
    else:
        filters["start_date"] = None
        filters["end_date"] = None

    return filters


def _ask_assistant_demo(
    question: str,
) -> AssistantResponse:
    tool_names = _select_tools(question)

    if not tool_names:
        return AssistantResponse(
            message=(
                "I can help with bookkeeping summary, "
                "AI categorization review, reconciliation, "
                "and audit activity."
            )
        )

    results = []
    messages = []

    for tool_name in tool_names:
        arguments = _get_demo_tool_arguments(
            tool_name,
            question,
        )

        result = _execute_tool(
            tool_name,
            arguments,
        )

        results.append(
            {
                "tool_name": tool_name,
                "result": result,
            }
        )

        messages.append(
            _format_tool_result(
                tool_name,
                result,
            )
        )

    return AssistantResponse(
        message="\n\n".join(messages),
        tool_name=", ".join(tool_names),
        tool_result=results,
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


def _format_uncategorized_investigation(result: Any) -> str:
    if not result:
        return "No financial transaction was found for that transaction ID."

    transaction = result["transaction"]

    if result["investigation_status"] == "ALREADY_CATEGORIZED":
        return (
            f"Transaction {transaction['transaction_id']} is already "
            f"categorized as {transaction['category']}. "
            f"No uncategorized-transaction recommendation was generated."
        )

    recommendation = result["recommendation"]
    current_ai_suggestion = result.get("current_ai_suggestion")
    evidence = result["evidence"]

    stored_suggestion_text = (
        (
            f"Stored AI suggestion: "
            f"{current_ai_suggestion['category']} at "
            f"{float(current_ai_suggestion['confidence']) * 100:.0f}% "
            f"confidence. This stored suggestion is not approved "
            f"accounting truth. "
        )
        if (
            current_ai_suggestion is not None
            and current_ai_suggestion.get("confidence") is not None
        )
        else (
            f"Stored AI suggestion: "
            f"{current_ai_suggestion['category']} with no confidence "
            f"score. This stored suggestion is not approved accounting "
            f"truth. "
            if current_ai_suggestion is not None
            else "There is no stored AI category suggestion. "
        )
    )

    return (
        f"Transaction {transaction['transaction_id']} remains "
        f"uncategorized: {transaction['description'] or 'No description'}, "
        f"vendor {transaction['vendor'] or 'No vendor'}, "
        f"amount €{abs(float(transaction['amount'])):.2f}. "
        f"{stored_suggestion_text}"
        f"Read-only recommendation: {recommendation['category']} at "
        f"{float(recommendation['confidence']) * 100:.0f}% confidence. "
        f"Supporting confirmed examples: "
        f"{evidence['supporting_example_count']}. "
        f"{recommendation['rationale']} "
        f"Final categorization requires human review and approval."
    )


def _format_reconciliation_investigation(result: Any) -> str:
    if not result:
        return "No bank transaction was found for that ID."

    bank = result["bank_transaction"]
    candidate = result.get("candidate_match")
    match = result["match"]
    evidence = result["evidence"]
    assessment = result["assessment"]

    amount = float(bank["amount"])

    lines = [
        (
            f"Reconciliation investigation for bank transaction "
            f"{bank['bank_transaction_id']}: "
            f"{bank['description'] or 'No description'}, "
            f"amount €{amount:.2f}, "
            f"status {bank['status']}."
        ),
        (
            f"Stored match type: "
            f"{match['match_type'] or 'None'}; "
            f"confidence: "
            + (
                f"{float(match['match_confidence']) * 100:.0f}%."
                if match["match_confidence"] is not None
                else "N/A."
            )
        ),
    ]

    if candidate is not None:
        candidate_amount = float(candidate["amount"])

        lines.append(
            f"Linked candidate transaction "
            f"{candidate['transaction_id']}: "
            f"{candidate['description'] or 'No description'}, "
            f"amount €{candidate_amount:.2f}, "
            f"vendor {candidate['vendor'] or 'No vendor'}."
        )

        amount_difference = evidence["amount_difference"]
        date_difference = evidence["date_difference_days"]
        overlap = evidence["description_token_overlap"]

        lines.append(
            "Evidence: "
            + (
                f"amount difference €"
                f"{float(amount_difference):.2f}, "
                if amount_difference is not None
                else "amount difference unavailable, "
            )
            + (
                f"date difference {date_difference} day(s), "
                if date_difference is not None
                else "date difference unavailable, "
            )
            + (
                f"description token overlap "
                f"{float(overlap) * 100:.0f}%."
                if overlap is not None
                else "description token overlap unavailable."
            )
        )
    else:
        lines.append(
            "No linked financial transaction candidate is stored."
        )

    lines.append(
        f"Assessment: {assessment['explanation']}"
    )

    if result["requires_human_review"]:
        lines.append(
            "No reconciliation state was changed. "
            "Human review is required before any final "
            "reconciliation decision."
        )
    else:
        lines.append(
            "No reconciliation state was changed. "
            "This item does not currently require unresolved-match review."
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


import json
import os
from typing import Any

from openai import OpenAI

from ai_tools import TOOL_DEFINITIONS, TOOL_REGISTRY


def ask_assistant_openai(
    question: str,
    client: Any | None = None,
) -> AssistantResponse:
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured"
            )

        client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "user",
                "content": question,
            }
        ],
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
    )

    tool_calls = [
        item
        for item in response.output
        if item.type == "function_call"
    ]

    if not tool_calls:
        return AssistantResponse(
            message=response.output_text,
            tool_name=None,
            tool_result=None,
        )

    tool_outputs = []
    first_tool_name = None
    first_tool_result = None

    for tool_call in tool_calls:
        tool_name = tool_call.name

        if tool_name not in TOOL_REGISTRY:
            raise ValueError(
                f"Unknown AI tool requested: {tool_name}"
            )

        arguments = json.loads(
            tool_call.arguments or "{}"
        )

        result = _execute_tool(
            tool_name,
            arguments,
        )

        if first_tool_name is None:
            first_tool_name = tool_name
            first_tool_result = result

        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": json.dumps(
                    result,
                    default=str,
                ),
            }
        )

    final_response = client.responses.create(
        model="gpt-5.6-luna",
        previous_response_id=response.id,
        input=tool_outputs,
        tools=TOOL_DEFINITIONS,
    )

    return AssistantResponse(
        message=final_response.output_text,
        tool_name=first_tool_name,
        tool_result=first_tool_result,
    )


def _format_tool_result(
    tool_name: str,
    result: Any,
) -> str:
    if tool_name == "get_bookkeeping_summary":
        return _format_bookkeeping_summary(result)

    if tool_name == "get_ai_review_queue":
        return _format_ai_review_queue(result)

    if tool_name == "investigate_uncategorized_transaction":
        return _format_uncategorized_investigation(result)

    if tool_name == "investigate_reconciliation_issue":
        return _format_reconciliation_investigation(result)

    if tool_name == "get_reconciliation_review":
        return _format_reconciliation_review(result)

    if tool_name == "get_audit_log":
        return _format_audit_log(result)

    if tool_name == "get_transactions_by_date":
        return _format_transactions_by_date(result)

    if tool_name == "get_transactions":
        return _format_transactions(result)

    if tool_name == "get_spending_by_category":
        return _format_spending_by_category(result)

    if tool_name == "get_vendor_totals":
        return _format_vendor_totals(result)

    if tool_name == "get_financial_anomalies":
        return _format_financial_anomalies(result)

    if tool_name == "get_financial_statistics":
        return _format_financial_statistics(result)

    if tool_name == "get_revenue_analysis":
        return _format_revenue_analysis(result)

    if tool_name == "get_expense_trends":
        return _format_expense_trends(result)

    return f"Executed tool: {tool_name}"

def _format_transactions_by_date(result: Any) -> str:
    if not result:
        return "No financial transactions were found for that date range."

    lines = [
        f"{len(result)} transaction(s) found:"
    ]

    for transaction in result:
        transaction_id = transaction["transaction_id"]
        description = transaction["description"]
        amount = float(transaction["amount"])
        category = transaction["category"] or "Uncategorized"
        vendor = transaction["vendor"] or "No vendor"
        status = transaction["status"]

        lines.append(
            f"- Transaction {transaction_id}: "
            f"{description}, "
            f"amount €{amount:.2f}, "
            f"vendor: {vendor}, "
            f"category: {category}, "
            f"status: {status}."
        )

    return "\n".join(lines)


def _execute_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(
            f"Unknown AI tool requested: {tool_name}"
        )

    tool = TOOL_REGISTRY[tool_name]
    arguments = arguments or {}

    return tool(**arguments)


def _get_demo_tool_arguments(
    tool_name: str,
    question: str,
) -> dict[str, Any]:
    if tool_name == "investigate_reconciliation_issue":
        bank_transaction_id = _extract_bank_transaction_id(
            question
        )

        if bank_transaction_id is None:
            raise ValueError(
                "Please provide a bank transaction ID."
            )

        return {
            "bank_transaction_id": bank_transaction_id,
        }

    if tool_name == "investigate_uncategorized_transaction":
        transaction_id = _extract_transaction_id(question)

        if transaction_id is None:
            raise ValueError(
                "Please provide a financial transaction ID."
            )

        return {
            "transaction_id": transaction_id,
        }

    if tool_name == "get_transactions_by_date":
        date_range = _extract_date_range(question)

        if date_range is None:
            raise ValueError(
                "Please provide a start and end date "
                "in YYYY-MM-DD format."
            )

        return {
            "start_date": date_range[0],
            "end_date": date_range[1],
        }

    if tool_name == "get_transactions":
        return _extract_transaction_filters(
            question
        )

    if tool_name == "get_spending_by_category":
        date_range = _extract_date_range(question)
        return {
            "category": _extract_known_category(question),
            "start_date": date_range[0] if date_range else None,
            "end_date": date_range[1] if date_range else None,
        }

    if tool_name == "get_vendor_totals":
        date_range = _extract_date_range(question)
        return {
            "vendor": _extract_known_vendor(question),
            "start_date": date_range[0] if date_range else None,
            "end_date": date_range[1] if date_range else None,
            "limit": _extract_top_limit(question),
        }

    if tool_name == "get_financial_anomalies":
        date_range = _extract_date_range(question)
        return {
            "start_date": date_range[0] if date_range else None,
            "end_date": date_range[1] if date_range else None,
        }

    if tool_name == "get_financial_statistics":
        date_range = _extract_date_range(question)
        return {
            "start_date": date_range[0] if date_range else None,
            "end_date": date_range[1] if date_range else None,
        }

    if tool_name == "get_revenue_analysis":
        date_range = _extract_date_range(question)
        return {
            "start_date": date_range[0] if date_range else None,
            "end_date": date_range[1] if date_range else None,
            "period": _extract_analysis_period(question),
        }

    if tool_name == "get_expense_trends":
        date_range = _extract_date_range(question)
        return {
            "category": _extract_known_category(question),
            "vendor": _extract_known_vendor(question),
            "start_date": date_range[0] if date_range else None,
            "end_date": date_range[1] if date_range else None,
            "period": _extract_analysis_period(question),
        }

    return {}



def _format_financial_anomalies(result: Any) -> str:
    if not result:
        return "No deterministic financial anomaly result is available."

    anomalies = result.get("anomalies", [])
    baseline = result.get("baseline", {})

    if not anomalies:
        return (
            "No deterministic financial anomaly signals were detected in the "
            "selected posted expense data. This does not prove that the "
            "accounting data is error-free."
        )

    lines = [
        f"Deterministic financial anomaly scan: {len(anomalies)} anomaly signal(s)."
    ]

    average_expense = baseline.get("average_expense")
    threshold = baseline.get("large_expense_threshold")
    if average_expense is not None:
        lines.append(
            f"Posted expense baseline: average €{float(average_expense):.2f}"
            + (
                f", large-expense threshold €{float(threshold):.2f}."
                if threshold is not None
                else "."
            )
        )

    for anomaly in anomalies:
        transaction_ids = ", ".join(
            str(transaction_id)
            for transaction_id in anomaly["transaction_ids"]
        )
        lines.append(
            f"- [{anomaly['severity']}] {anomaly['anomaly_type']}: "
            f"transaction(s) {transaction_ids}. {anomaly['reason']}"
        )

    lines.append(
        "These are deterministic investigation signals, not confirmed "
        "accounting errors. No accounting state was changed; human review "
        "is required before taking action."
    )
    return "\n".join(lines)


def _format_transactions(result: Any) -> str:
    if not result:
        return "No financial transactions matched those filters."

    lines = [
        f"{len(result)} transaction(s) matched:"
    ]

    for transaction in result:
        transaction_id = transaction["transaction_id"]
        description = transaction["description"]
        amount = float(transaction["amount"])
        category = transaction["category"] or "Uncategorized"
        vendor = transaction["vendor"] or "No vendor"
        status = transaction["status"]

        lines.append(
            f"- Transaction {transaction_id}: "
            f"{description}, "
            f"amount €{amount:.2f}, "
            f"vendor: {vendor}, "
            f"category: {category}, "
            f"status: {status}."
        )

    return "\n".join(lines)


def _format_spending_by_category(result: Any) -> str:
    if not result:
        return "No posted expense spending was found by category."

    lines = ["Posted spending by category:"]

    for item in result:
        lines.append(
            f"- {item['category']}: "
            f"€{float(item['total_spending']):.2f} across "
            f"{item['transaction_count']} transaction(s)."
        )

    return "\n".join(lines)


def _format_vendor_totals(result: Any) -> str:
    if not result:
        return "No posted expense spending was found by vendor."

    lines = ["Posted spending by vendor:"]

    for item in result:
        lines.append(
            f"- {item['vendor']}: "
            f"€{float(item['total_spending']):.2f} across "
            f"{item['transaction_count']} transaction(s)."
        )

    return "\n".join(lines)


def _format_financial_statistics(result: Any) -> str:
    if not result:
        return "No financial statistics are available."

    average_expense = result.get("average_expense")
    largest_expense = result.get("largest_expense")

    average_text = (
        f"€{float(average_expense):.2f}"
        if average_expense is not None
        else "N/A"
    )
    largest_text = (
        f"€{float(largest_expense):.2f}"
        if largest_expense is not None
        else "N/A"
    )

    return (
        f"Financial statistics: "
        f"{result.get('transaction_count', 0)} transaction(s). "
        f"Average posted expense: {average_text}. "
        f"Largest posted expense: {largest_text}. "
        f"Status counts: {result.get('posted_count', 0)} posted, "
        f"{result.get('pending_count', 0)} pending. "
        f"Categorization counts: "
        f"{result.get('categorized_count', 0)} categorized, "
        f"{result.get('uncategorized_count', 0)} uncategorized."
    )


def _format_revenue_analysis(result: Any) -> str:
    if not result or not result.get("periods"):
        return "No posted sale revenue was found for that period."

    lines = [
        "Posted sale revenue: "
        f"€{float(result['total_revenue']):.2f} across "
        f"{result['transaction_count']} transaction(s)."
    ]

    for item in result["periods"]:
        lines.append(
            f"- {item['period']}: "
            f"€{float(item['total_revenue']):.2f} across "
            f"{item['transaction_count']} transaction(s)."
        )

    return "\n".join(lines)


def _format_expense_trends(result: Any) -> str:
    if not result or not result.get("periods"):
        return "No posted expense spending was found for that period."

    lines = [
        "Posted expense trend: "
        f"€{float(result['total_expenses']):.2f} across "
        f"{result['transaction_count']} transaction(s)."
    ]
    comparison_label = (
        "month over month"
        if result["period"] == "month"
        else "year over year"
    )

    for item in result["periods"]:
        change_percentage = item["change_percentage"]
        change_text = (
            "no previous period"
            if item["change_amount"] is None
            else (
                f"{float(change_percentage):+.2f}% {comparison_label}"
                if change_percentage is not None
                else f"{comparison_label} change unavailable"
            )
        )
        lines.append(
            f"- {item['period']}: "
            f"€{float(item['total_expenses']):.2f} across "
            f"{item['transaction_count']} transaction(s); {change_text}."
        )

    return "\n".join(lines)
