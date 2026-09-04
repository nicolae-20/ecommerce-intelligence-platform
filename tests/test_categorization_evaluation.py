import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))

from accounting_rag import AccountingContext
from categorization_evaluation import (
    evaluate_demo_categorization,
    load_trusted_categorization_records,
)
from llm_categorizer import CategorySuggestion


def _categories(*names):
    return [
        {
            "category_id": index,
            "account_code": str(4000 + index),
            "account_name": name,
            "account_type": "REVENUE" if name == "Sales Revenue" else "EXPENSE",
        }
        for index, name in enumerate(names, start=1)
    ]


def _record(category="Software", **overrides):
    record = {
        "transaction_id": 1,
        "description": "Microsoft 365 subscription",
        "vendor": "Microsoft",
        "amount": -20,
        "transaction_type": "EXPENSE",
        "trusted_category": category,
    }
    record.update(overrides)
    return record


def test_trusted_loader_uses_final_active_category_join_and_is_read_only(monkeypatch):
    captured = {}

    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, sql): captured["sql"] = sql
        def fetchall(self):
            return [(1, "Microsoft", "Microsoft", -20, "EXPENSE", "Software")]

    class Connection:
        def cursor(self): return Cursor()
        def commit(self): raise AssertionError("loader must not commit")
        def close(self): captured["closed"] = True

    import categorization_evaluation
    monkeypatch.setattr(categorization_evaluation, "get_connection", lambda: Connection())
    records = load_trusted_categorization_records()
    sql = " ".join(captured["sql"].split()).upper()
    assert "FT.ACCOUNTING_CATEGORY_ID" in sql
    assert "AC.IS_ACTIVE = 'Y'" in sql
    assert "AI_SUGGESTED_CATEGORY" not in sql
    assert "AI_CONFIDENCE" not in sql
    assert all(keyword not in sql for keyword in ("UPDATE", "INSERT", "DELETE"))
    assert records[0]["trusted_category"] == "Software"
    assert captured["closed"] is True


def test_correct_prediction_and_category_aggregation():
    result = evaluate_demo_categorization(
        [_record()],
        _categories("Software"),
    )
    assert result["demo_accuracy_on_trusted_labels"] == 1.0
    assert result["by_trusted_category"]["Software"]["correct"] == 1


def test_incorrect_and_confidence_breakdowns():
    result = evaluate_demo_categorization(
        [
            _record(transaction_id=1),
            _record(
                transaction_id=3,
                description="AWS monthly service",
                vendor="Amazon Web Services",
                trusted_category="Office Supplies",
            ),
            _record(
                transaction_id=2,
                description="Unknown transaction",
                vendor=None,
                trusted_category="Office Supplies",
            ),
        ],
        _categories("Software", "Office Supplies"),
    )
    assert result["correct_prediction_count"] == 2
    assert result["incorrect_prediction_count"] == 1
    assert result["high_confidence_count"] == 2
    assert result["high_confidence_correct_count"] == 1
    assert result["high_confidence_incorrect_count"] == 1
    assert result["below_threshold_count"] == 1
    assert result["below_threshold_suggestion_rate"] == 1 / 3


@pytest.mark.parametrize(
    ("transaction_type", "description", "amount", "category"),
    [
        ("SALE", "Customer order payment", -100, "Sales Revenue"),
        ("EXPENSE", "Microsoft 365 subscription", 100, "Software"),
        ("BANK_FEE", "Bank fee refund", 5, "Bank Fees"),
    ],
)
def test_transaction_type_and_amount_sign_cases(
    transaction_type,
    description,
    amount,
    category,
):
    result = evaluate_demo_categorization(
        [_record(
            transaction_type=transaction_type,
            description=description,
            amount=amount,
            trusted_category=category,
        )],
        _categories("Sales Revenue", "Software", "Bank Fees"),
    )
    assert result["by_transaction_type"][transaction_type]["support"] == 1
    assert result["correct_prediction_count"] == 1


def test_unsupported_type_is_excluded_without_normalization():
    result = evaluate_demo_categorization(
        [_record(transaction_type=" sale ")],
        _categories("Software"),
    )
    assert result["trusted_labeled_count"] == 1
    assert result["evaluable_count"] == 0
    assert result["excluded_count"] == 1
    assert result["successful_prediction_count"] == 0
    assert result["validation_failure_count"] == 0
    assert result["exclusion_reasons"] == {"unsupported_transaction_type": 1}


def test_unsupported_trusted_category_is_excluded():
    result = evaluate_demo_categorization(
        [_record(trusted_category="Inactive Category")],
        _categories("Software"),
    )
    assert result["evaluable_count"] == 0
    assert result["exclusion_reasons"] == {
        "unsupported_trusted_category": 1,
    }


def test_validation_failure_reduces_coverage_and_primary_accuracy(monkeypatch):
    import categorization_evaluation

    monkeypatch.setattr(
        categorization_evaluation,
        "suggest_transaction_category_demo",
        lambda **kwargs: (_ for _ in ()).throw(
            ValueError("Invalid accounting category returned by AI")
        ),
    )
    result = evaluate_demo_categorization(
        [_record()],
        _categories("Software"),
    )
    assert result["validation_failure_count"] == 1
    assert result["successful_prediction_count"] == 0
    assert result["prediction_coverage"] == 0.0
    assert result["demo_accuracy_on_trusted_labels"] == 0.0


def test_phase6_4_validation_failures_are_sorted_by_transaction_id():
    result = evaluate_demo_categorization(
        [
            _record(
                transaction_id=9,
                description="Unknown one",
                vendor=None,
            ),
            _record(
                transaction_id=2,
                description="Unknown two",
                vendor=None,
            ),
        ],
        _categories("Software"),
    )
    assert [
        failure["transaction_id"]
        for failure in result["validation_failures"]
    ] == [2, 9]


def test_phase6_4_trusted_evaluable_excluded_invariant():
    result = evaluate_demo_categorization(
        [
            _record(transaction_id=1),
            _record(transaction_id=2, transaction_type="TRANSFER"),
        ],
        _categories("Software"),
    )
    assert result["trusted_labeled_count"] == (
        result["evaluable_count"] + result["excluded_count"]
    )
    assert result["excluded_count"] == 1
    assert result["exclusion_reasons"] == {
        "unsupported_transaction_type": 1,
    }


def test_phase6_4_success_validation_and_primary_denominators():
    result = evaluate_demo_categorization(
        [
            _record(transaction_id=1),
            _record(
                transaction_id=2,
                description="Unknown transaction",
                vendor=None,
            ),
        ],
        _categories("Software"),
    )
    assert result["successful_prediction_count"] == 1
    assert result["validation_failure_count"] == 1
    assert result["successful_prediction_count"] + result["validation_failure_count"] == result["evaluable_count"]
    assert result["prediction_coverage"] == 1 / 2
    assert result["demo_accuracy_on_trusted_labels"] == 1 / 2
    assert result["accuracy_among_successful_predictions"] == 1.0


def test_phase6_4_prediction_and_high_confidence_counts_reconcile():
    result = evaluate_demo_categorization(
        [
            _record(transaction_id=1),
            _record(
                transaction_id=2,
                description="AWS monthly service",
                vendor="Amazon Web Services",
                trusted_category="Office Supplies",
            ),
        ],
        _categories("Software", "Office Supplies"),
    )
    assert result["correct_prediction_count"] + result["incorrect_prediction_count"] == result["successful_prediction_count"]
    assert result["high_confidence_correct_count"] + result["high_confidence_incorrect_count"] == result["high_confidence_count"]
    assert result["high_confidence_accuracy"] == result["high_confidence_correct_count"] / result["high_confidence_count"]
    assert result["high_confidence_error_rate"] == result["high_confidence_incorrect_count"] / result["high_confidence_count"]


def test_ambiguous_transaction_is_successful_but_below_threshold():
    result = evaluate_demo_categorization(
        [_record(
            description="Microsoft 365 subscription",
            transaction_type="SALE",
            trusted_category="Sales Revenue",
        )],
        _categories("Sales Revenue", "Software"),
    )
    assert result["successful_prediction_count"] == 1
    assert result["below_threshold_count"] == 1
    assert result["confusion_pairs"][0]["predicted_category"] == "Sales Revenue"


def test_pure_evaluator_does_not_open_a_database_connection(monkeypatch):
    import categorization_evaluation

    monkeypatch.setattr(
        categorization_evaluation,
        "get_connection",
        lambda: (_ for _ in ()).throw(
            AssertionError("pure evaluation must not connect to the database")
        ),
    )
    result = evaluate_demo_categorization(
        [_record()],
        _categories("Software"),
    )
    assert result["correct_prediction_count"] == 1


def test_zero_rows_have_deterministic_empty_metrics():
    result = evaluate_demo_categorization([], _categories("Software"))
    assert result["trusted_labeled_count"] == 0
    assert result["evaluable_count"] == 0
    assert result["prediction_coverage"] == 0.0
    assert result["demo_accuracy_on_trusted_labels"] == 0.0
    assert result["by_transaction_type"] == {}
    assert result["by_trusted_category"] == {}
    assert result["confusion_pairs"] == []


def test_evaluation_does_not_use_rag_examples_or_environment_mode(monkeypatch):
    import accounting_rag
    import categorization_evaluation

    monkeypatch.setenv("AI_CATEGORIZATION_MODE", "openai")
    captured = {}
    monkeypatch.setattr(
        accounting_rag,
        "get_accounting_context",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("evaluation must not call historical RAG")
        ),
    )
    real_context = categorization_evaluation.AccountingContext

    def capture_context(**kwargs):
        captured["examples"] = kwargs["examples"]
        return real_context(**kwargs)

    monkeypatch.setattr(
        categorization_evaluation,
        "AccountingContext",
        capture_context,
    )
    result = evaluate_demo_categorization(
        [_record()],
        _categories("Software"),
    )
    assert result["correct_prediction_count"] == 1
    assert captured["examples"] == []


def test_evaluation_bypasses_environment_selected_openai_mode(monkeypatch):
    import categorization_evaluation
    import llm_categorizer

    monkeypatch.setenv("AI_CATEGORIZATION_MODE", "openai")
    monkeypatch.setattr(
        llm_categorizer,
        "suggest_transaction_category",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("evaluation must not use environment-selected mode")
        ),
    )
    result = categorization_evaluation.evaluate_demo_categorization(
        [_record()],
        _categories("Software"),
    )
    assert result["successful_prediction_count"] == 1
    assert result["correct_prediction_count"] == 1


def test_breakdowns_and_confusion_pairs_are_sorted():
    result = evaluate_demo_categorization(
        [
            _record(transaction_id=2, trusted_category="Zed"),
            _record(transaction_id=1, trusted_category="Alpha"),
        ],
        _categories("Software", "Alpha", "Zed"),
    )
    assert list(result["by_trusted_category"]) == ["Alpha", "Zed"]
    assert result["confusion_pairs"] == [
        {
            "trusted_category": "Alpha",
            "predicted_category": "Software",
            "count": 1,
        },
        {
            "trusted_category": "Zed",
            "predicted_category": "Software",
            "count": 1,
        },
    ]
