import json
import math
import os
from dataclasses import dataclass
from typing import Any
from accounting_rag import AccountingContext

AI_CONFIDENCE_THRESHOLD = 0.80


@dataclass
class CategorySuggestion:
    category: str
    confidence: float

    @property
    def high_confidence(self) -> bool:
        return self.confidence >= AI_CONFIDENCE_THRESHOLD


SYSTEM_PROMPT = (
    "You are an accounting categorization assistant. "
    "Use only the accounting categories provided in the user context. "
    "Use confirmed historical examples as supporting evidence when available. "
    "Never invent an accounting category. "
    "Choose exactly one category from the provided Chart of Accounts. "
    "If the evidence is weak or ambiguous, still choose the best "
    "available category but return a lower confidence score. "
    "Treat explicit transaction type as a structural accounting signal; "
    "amount sign is supporting evidence only and must not redefine it. "
    "Conflicting evidence should reduce confidence. "
    "Return only JSON with keys: category and confidence. "
    "Confidence must be a number between 0 and 1."
)



def is_high_confidence_suggestion(
    suggestion: CategorySuggestion,
) -> bool:
    return suggestion.confidence >= AI_CONFIDENCE_THRESHOLD

def _parse_category_response(response: Any) -> CategorySuggestion:
    result = response.output_text.strip()
    data = json.loads(result)

    return CategorySuggestion(
        category=data["category"],
        confidence=float(data["confidence"]),
    )

def validate_suggestion_confidence(
    suggestion: CategorySuggestion,
) -> CategorySuggestion:
    try:
        confidence = float(suggestion.confidence)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Invalid AI confidence: expected a finite number "
            "between 0 and 1."
        ) from exc

    if (
        not math.isfinite(confidence)
        or confidence < 0.0
        or confidence > 1.0
    ):
        raise ValueError(
            "Invalid AI confidence: expected a finite number "
            "between 0 and 1."
        )

    suggestion.confidence = confidence
    return suggestion


def validate_category_suggestion(
    suggestion: CategorySuggestion,
    context: AccountingContext,
) -> CategorySuggestion:
    validate_suggestion_confidence(suggestion)

    valid_categories = {
        category["account_name"]
        for category in context.categories
    }

    if suggestion.category not in valid_categories:
        raise ValueError(
            f"Invalid accounting category returned by AI: "
            f"{suggestion.category}"
        )

    return suggestion


def _validate_suggestion_for_context(
    suggestion: CategorySuggestion,
    context: AccountingContext | None,
) -> CategorySuggestion:
    if context is None:
        return validate_suggestion_confidence(
            suggestion
        )

    return validate_category_suggestion(
        suggestion,
        context,
    )

DEMO_AMBIGUOUS_CONFIDENCE = 0.60
SUPPORTED_TRANSACTION_TYPES = {"SALE", "EXPENSE", "BANK_FEE"}


def _normalize_transaction_type(transaction_type: str | None) -> str | None:
    if transaction_type is None:
        return None
    normalized = str(transaction_type).strip().upper()
    if normalized not in SUPPORTED_TRANSACTION_TYPES:
        raise ValueError(
            "transaction_type must be one of SALE, EXPENSE, or BANK_FEE"
        )
    return normalized


def _demo_category_suggestion(
    description: str | None,
    vendor: str | None,
    amount: float,
    transaction_type: str | None = None,
) -> CategorySuggestion:
    transaction_type = _normalize_transaction_type(transaction_type)
    text = " ".join(
        value.strip().lower()
        for value in [description, vendor]
        if value
    )

    matches: dict[str, float] = {}

    def add_match(
        category: str,
        confidence: float,
    ) -> None:
        matches[category] = max(
            confidence,
            matches.get(category, 0.0),
        )

    if (
        "aws" in text
        or "amazon web services" in text
    ):
        add_match(
            "Software",
            0.97,
        )

    if "microsoft" in text:
        add_match(
            "Software",
            0.95,
        )

    if "bank fee" in text:
        add_match(
            "Bank Fees",
            0.99,
        )

    if any(
        marker in text
        for marker in (
            "google ads",
            "facebook ads",
            "meta ads",
            "advertising",
            "ad campaign",
            "marketing campaign",
        )
    ):
        add_match(
            "Advertising",
            0.92,
        )

    if any(
        marker in text
        for marker in (
            "electricity bill",
            "electric bill",
            "utility bill",
            "utilities",
            "water bill",
            "gas bill",
        )
    ):
        add_match(
            "Utilities",
            0.90,
        )

    if any(
        marker in text
        for marker in (
            "hotel",
            "accommodation",
            "airfare",
            "flight",
            "travel expense",
        )
    ):
        add_match(
            "Travel",
            0.90,
        )

    if any(
        marker in text
        for marker in (
            "software subscription",
            "software license",
            "software licence",
            "saas",
        )
    ):
        add_match(
            "Software",
            0.86,
        )

    if (
        "office" in text
        or "supplies" in text
        or "printer paper" in text
        or "stationery" in text
    ):
        add_match(
            "Office Supplies",
            0.88,
        )

    if transaction_type == "SALE":
        return CategorySuggestion(
            category="Sales Revenue",
            confidence=(
                DEMO_AMBIGUOUS_CONFIDENCE
                if matches
                else 0.95
            ),
        )

    if transaction_type == "BANK_FEE":
        return CategorySuggestion(
            category="Bank Fees",
            confidence=(
                DEMO_AMBIGUOUS_CONFIDENCE
                if any(category != "Bank Fees" for category in matches)
                else 0.99
            ),
        )

    if matches:
        ranked_matches = sorted(
            matches.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )

        category, confidence = ranked_matches[0]

        if len(matches) > 1:
            confidence = min(
                confidence,
                DEMO_AMBIGUOUS_CONFIDENCE,
            )

        return CategorySuggestion(
            category=category,
            confidence=confidence,
        )

    return CategorySuggestion(
        category="Office Supplies",
        confidence=0.10,
    )


def suggest_transaction_category(
    description: str | None,
    vendor: str | None,
    amount: float,
    client: Any | None = None,
    context: AccountingContext | None = None,
    transaction_type: str | None = None,
) -> CategorySuggestion:

    transaction_type = _normalize_transaction_type(transaction_type)

    context_text = ""

    if context is not None:
        category_lines = "\n".join(
            f"- {category['account_code']} "
            f"{category['account_name']} "
            f"({category['account_type']})"
            for category in context.categories
        )

        example_lines = "\n".join(
            f"- {example['description']} "
            f"({example['vendor'] or 'No vendor'}) "
            f"-> {example['category']}"
            for example in context.examples
        )

        context_text = f"""
Available accounting categories:
{category_lines}

Confirmed historical examples:
{example_lines or "No relevant confirmed examples found."}
"""

    transaction_text = f"""
Transaction:
Description: {description or "N/A"}
Vendor: {vendor or "N/A"}
Amount: {amount}
Transaction type: {transaction_type or "N/A"}

{context_text}

Choose exactly one category from the available accounting categories above.
Do not invent categories.
The explicit transaction type is a structural accounting signal. The amount
sign is supporting evidence only and must not redefine the transaction type.
If evidence conflicts, keep the explicit type and reduce confidence.
"""

    if client is not None:
        response = client.responses.create(
            model="gpt-5.6-luna",
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": transaction_text,
                },
            ],
        )

        suggestion = _parse_category_response(response)

        return _validate_suggestion_for_context(
            suggestion=suggestion,
            context=context,
        )

    mode = os.getenv(
        "AI_CATEGORIZATION_MODE",
        "demo",
    ).lower()

    if mode == "demo":
        suggestion = _demo_category_suggestion(
            description=description,
            vendor=vendor,
            amount=amount,
            transaction_type=transaction_type,
        )

        return _validate_suggestion_for_context(
            suggestion=suggestion,
            context=context,
        )

    if mode == "openai":
        from openai import OpenAI

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
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": transaction_text,
                },
            ],
        )

        suggestion = _parse_category_response(response)

        return _validate_suggestion_for_context(
            suggestion=suggestion,
            context=context,
        )

    raise ValueError(
        "AI_CATEGORIZATION_MODE must be 'demo' or 'openai'"
    )
