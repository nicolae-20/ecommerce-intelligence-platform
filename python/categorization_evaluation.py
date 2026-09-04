"""Deterministic, read-only evaluation of Demo Mode categorization."""

import math
from collections.abc import Iterable, Mapping

from accounting_rag import AccountingContext
from database import get_connection
from llm_categorizer import (
    AI_CONFIDENCE_THRESHOLD,
    CategorySuggestion,
    SUPPORTED_TRANSACTION_TYPES,
    suggest_transaction_category_demo,
)


def load_active_accounting_categories() -> list[dict]:
    """Load the active Chart of Accounts without changing database state."""
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
                ORDER BY account_code
            """)

            return [
                {
                    "category_id": row[0],
                    "account_code": row[1],
                    "account_name": row[2],
                    "account_type": row[3],
                }
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()


def load_trusted_categorization_records() -> list[dict]:
    """Load transactions whose final active category is a trusted label."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ft.transaction_id,
                    ft.description,
                    ft.vendor,
                    ft.amount,
                    ft.transaction_type,
                    ac.account_name
                FROM financial_transactions ft
                JOIN accounting_categories ac
                  ON ac.accounting_category_id =
                     ft.accounting_category_id
                 AND ac.is_active = 'Y'
                WHERE ft.accounting_category_id IS NOT NULL
                ORDER BY ft.transaction_id
            """)

            return [
                {
                    "transaction_id": row[0],
                    "description": row[1],
                    "vendor": row[2],
                    "amount": row[3],
                    "transaction_type": row[4],
                    "trusted_category": row[5],
                }
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()


def _record_value(record: Mapping, key: str):
    return record.get(key)


def _exclusion_reason(
    record: Mapping,
    valid_categories: set[str],
) -> str | None:
    trusted_category = _record_value(record, "trusted_category")
    if not isinstance(trusted_category, str) or not trusted_category.strip():
        return "missing_trusted_category"
    if trusted_category not in valid_categories:
        return "unsupported_trusted_category"

    amount = _record_value(record, "amount")
    try:
        numeric_amount = float(amount)
    except (TypeError, ValueError):
        return "invalid_amount"

    if not math.isfinite(numeric_amount):
        return "invalid_amount"

    transaction_type = _record_value(record, "transaction_type")
    if (
        transaction_type is not None
        and (
            not isinstance(transaction_type, str)
            or transaction_type not in SUPPORTED_TRANSACTION_TYPES
        )
    ):
        return "unsupported_transaction_type"

    for field in ("description", "vendor"):
        value = _record_value(record, field)
        if value is not None and not isinstance(value, str):
            return f"invalid_{field}"

    return None


def _empty_breakdown() -> dict:
    return {
        "support": 0,
        "correct": 0,
        "accuracy": 0.0,
    }


def _accuracy(correct: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return correct / denominator


def evaluate_demo_categorization(
    records: Iterable[Mapping],
    categories: Iterable[Mapping],
) -> dict:
    """Evaluate Demo Mode against trusted final accounting labels.

    Historical examples are deliberately omitted from the AccountingContext;
    this evaluates deterministic categorization rather than RAG-assisted
    behavior. The function itself never opens a database connection.
    """
    trusted_records = list(records)
    active_categories = [dict(category) for category in categories]
    valid_categories = {
        category["account_name"]
        for category in active_categories
    }
    context = AccountingContext(
        categories=active_categories,
        examples=[],
    )

    exclusions: dict[str, int] = {}
    evaluable_records: list[Mapping] = []

    for record in trusted_records:
        reason = _exclusion_reason(record, valid_categories)
        if reason is None:
            evaluable_records.append(record)
        else:
            exclusions[reason] = exclusions.get(reason, 0) + 1

    correct_prediction_count = 0
    incorrect_prediction_count = 0
    successful_prediction_count = 0
    validation_failure_count = 0
    high_confidence_count = 0
    high_confidence_correct_count = 0
    high_confidence_incorrect_count = 0
    below_threshold_count = 0
    by_transaction_type: dict[str, dict] = {}
    by_trusted_category: dict[str, dict] = {}
    confusion_counts: dict[tuple[str, str], int] = {}
    validation_failures: list[dict] = []

    for record in evaluable_records:
        transaction_type = _record_value(record, "transaction_type")
        type_key = transaction_type or "UNSPECIFIED"
        trusted_category = _record_value(record, "trusted_category")
        by_transaction_type.setdefault(type_key, _empty_breakdown())
        by_trusted_category.setdefault(
            trusted_category,
            _empty_breakdown(),
        )
        by_transaction_type[type_key]["support"] += 1
        by_trusted_category[trusted_category]["support"] += 1

        try:
            suggestion: CategorySuggestion = suggest_transaction_category_demo(
                description=_record_value(record, "description"),
                vendor=_record_value(record, "vendor"),
                amount=float(_record_value(record, "amount")),
                transaction_type=transaction_type,
                context=context,
            )
        except ValueError as exc:
            validation_failure_count += 1
            validation_failures.append({
                "transaction_id": _record_value(record, "transaction_id"),
                "trusted_category": trusted_category,
                "error": str(exc),
            })
            continue

        successful_prediction_count += 1
        is_correct = suggestion.category == trusted_category

        if is_correct:
            correct_prediction_count += 1
            by_transaction_type[type_key]["correct"] += 1
            by_trusted_category[trusted_category]["correct"] += 1
        else:
            incorrect_prediction_count += 1

        confusion_key = (trusted_category, suggestion.category)
        confusion_counts[confusion_key] = (
            confusion_counts.get(confusion_key, 0) + 1
        )

        if suggestion.high_confidence:
            high_confidence_count += 1
            if is_correct:
                high_confidence_correct_count += 1
            else:
                high_confidence_incorrect_count += 1
        else:
            below_threshold_count += 1

    for breakdown in by_transaction_type.values():
        breakdown["accuracy"] = _accuracy(
            breakdown["correct"],
            breakdown["support"],
        )

    for breakdown in by_trusted_category.values():
        breakdown["accuracy"] = _accuracy(
            breakdown["correct"],
            breakdown["support"],
        )

    def validation_failure_key(failure: dict):
        transaction_id = failure["transaction_id"]
        try:
            return (0, float(transaction_id), str(transaction_id))
        except (TypeError, ValueError):
            return (1, str(transaction_id), "")

    evaluable_count = len(evaluable_records)
    return {
        "trusted_labeled_count": len(trusted_records),
        "evaluable_count": evaluable_count,
        "excluded_count": len(trusted_records) - evaluable_count,
        "exclusion_reasons": dict(sorted(exclusions.items())),
        "successful_prediction_count": successful_prediction_count,
        "validation_failure_count": validation_failure_count,
        "correct_prediction_count": correct_prediction_count,
        "incorrect_prediction_count": incorrect_prediction_count,
        "prediction_coverage": _accuracy(
            successful_prediction_count,
            evaluable_count,
        ),
        "demo_accuracy_on_trusted_labels": _accuracy(
            correct_prediction_count,
            evaluable_count,
        ),
        "accuracy_among_successful_predictions": _accuracy(
            correct_prediction_count,
            successful_prediction_count,
        ),
        "high_confidence_count": high_confidence_count,
        "high_confidence_correct_count": high_confidence_correct_count,
        "high_confidence_incorrect_count": high_confidence_incorrect_count,
        "high_confidence_accuracy": _accuracy(
            high_confidence_correct_count,
            high_confidence_count,
        ),
        "high_confidence_error_rate": _accuracy(
            high_confidence_incorrect_count,
            high_confidence_count,
        ),
        "below_threshold_count": below_threshold_count,
        "below_threshold_suggestion_rate": _accuracy(
            below_threshold_count,
            successful_prediction_count,
        ),
        "by_transaction_type": {
            key: by_transaction_type[key]
            for key in sorted(by_transaction_type)
        },
        "by_trusted_category": {
            key: by_trusted_category[key]
            for key in sorted(by_trusted_category)
        },
        "confusion_pairs": [
            {
                "trusted_category": trusted,
                "predicted_category": predicted,
                "count": confusion_counts[(trusted, predicted)],
            }
            for trusted, predicted in sorted(confusion_counts)
        ],
        "validation_failures": sorted(
            validation_failures,
            key=validation_failure_key,
        ),
    }


def evaluate_trusted_categorization() -> dict:
    """Load trusted records and evaluate Demo Mode without writes or RAG."""
    categories = load_active_accounting_categories()
    records = load_trusted_categorization_records()
    return evaluate_demo_categorization(records, categories)
