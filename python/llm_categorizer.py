import json
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

def validate_category_suggestion(
    suggestion: CategorySuggestion,
    context: AccountingContext,
) -> CategorySuggestion:
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

def _demo_category_suggestion(
    description: str | None,
    vendor: str | None,
    amount: float,
) -> CategorySuggestion:
    text = " ".join(
        value.strip().lower()
        for value in [description, vendor]
        if value
    )

    if "aws" in text or "amazon web services" in text:
        return CategorySuggestion(
            category="Software",
            confidence=0.97,
        )

    if "microsoft" in text:
        return CategorySuggestion(
            category="Software",
            confidence=0.95,
        )

    if "bank fee" in text:
        return CategorySuggestion(
            category="Bank Fees",
            confidence=0.99,
        )

    if "office" in text or "supplies" in text:
        return CategorySuggestion(
            category="Office Supplies",
            confidence=0.88,
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
) -> CategorySuggestion:

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

{context_text}

Choose exactly one category from the available accounting categories above.
Do not invent categories.
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

        if context is not None:
            validate_category_suggestion(
        suggestion,
        context,
    )

        return suggestion

    mode = os.getenv(
        "AI_CATEGORIZATION_MODE",
        "demo",
    ).lower()

    if mode == "demo":
        return _demo_category_suggestion(
            description=description,
            vendor=vendor,
            amount=amount,
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

        if context is not None:
            validate_category_suggestion(
        suggestion,
        context,
    )

        return suggestion

    raise ValueError(
        "AI_CATEGORIZATION_MODE must be 'demo' or 'openai'"
    )