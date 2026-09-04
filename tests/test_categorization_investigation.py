from pathlib import Path
import inspect
import sys

import pytest


sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))


def test_phase7_2_allowlist_is_exact_and_read_only():
    from categorization_investigation import (
        PHASE_7_2_CATEGORIZATION_ALLOWLIST,
        PHASE_7_2_CATEGORIZATION_TOOL_PLAN,
    )
    from financial_investigation import PHASE_7_1_INVESTIGATION_ALLOWLIST

    assert PHASE_7_2_CATEGORIZATION_TOOL_PLAN == (
        "investigate_uncategorized_transaction",
    )
    assert PHASE_7_2_CATEGORIZATION_ALLOWLIST == {
        "investigate_uncategorized_transaction",
    }
    assert PHASE_7_2_CATEGORIZATION_ALLOWLIST.isdisjoint(
        {
            "approve_transaction_category",
            "reject_transaction_category",
            "assign_transaction_category",
            "cancel_transaction_rejection",
            "categorize_transaction_with_llm",
            "categorize_uncategorized_transactions",
            "investigate_bank_transaction",
            "run_reconciliation",
            "confirm_bank_transaction_match",
            "reject_bank_transaction_match",
            "log_audit_event",
            "get_audit_log",
            "investigate_financial_overview",
            *PHASE_7_1_INVESTIGATION_ALLOWLIST,
        }
    )


def test_phase7_2_permission_module_is_pure():
    import categorization_investigation

    source = inspect.getsource(categorization_investigation)

    assert "import analytics" not in source
    assert "import database" not in source
    assert "import ai_assistant" not in source
    assert "_execute_tool" not in source


def test_phase7_2_runner_uses_executor_once_with_demo_flag(monkeypatch):
    import ai_assistant

    calls = []

    def fake_execute_tool(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        return {"investigation_status": "RECOMMENDATION_READY"}

    monkeypatch.setattr(ai_assistant, "_execute_tool", fake_execute_tool)

    result = ai_assistant._run_phase_7_2_categorization_investigation(123)

    assert result["investigation_status"] == "RECOMMENDATION_READY"
    assert calls == [
        (
            "investigate_uncategorized_transaction",
            {
                "transaction_id": 123,
                "demo_only": True,
            },
        )
    ]


def test_phase7_2_runner_rejects_plan_expansion(monkeypatch):
    import ai_assistant

    monkeypatch.setattr(
        ai_assistant,
        "PHASE_7_2_CATEGORIZATION_TOOL_PLAN",
        (
            "investigate_uncategorized_transaction",
            "get_audit_log",
        ),
    )

    with pytest.raises(ValueError, match="not allowed"):
        ai_assistant._run_phase_7_2_categorization_investigation(123)


@pytest.mark.parametrize(
    "question",
    [
        "Investigate transaction 123.",
        "Why does transaction 123 need review?",
        "What evidence supports transaction 123?",
        "What historical examples support transaction 123?",
    ],
)
def test_phase7_2_routing_supports_narrow_transaction_intents(question):
    from ai_assistant import _select_tools

    assert _select_tools(question) == [
        "investigate_uncategorized_transaction",
    ]


def test_phase7_2_routing_does_not_swallow_other_intents():
    from ai_assistant import _select_tools

    assert _select_tools("Show transaction 123") == []
    assert _select_tools("Why investigate bank transaction 9?") == [
        "investigate_reconciliation_issue",
    ]
    assert _select_tools("What financial issues need attention?") == [
        "investigate_financial_overview",
    ]


def test_phase7_2_demo_boundary_avoids_openai(monkeypatch):
    import accounting_rag
    import analytics
    import llm_categorizer

    from accounting_rag import AccountingContext
    from llm_categorizer import CategorySuggestion

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql, binds=None):
            self.sql = sql
            self.binds = binds

        def fetchone(self):
            return (
                123,
                "2026-09-01",
                "EXPENSE",
                "Unknown expense",
                -25.0,
                None,
                "Unknown Vendor",
                None,
                None,
                "UNMATCHED",
                "POSTED",
            )

    class Connection:
        def __init__(self):
            self.commit_called = False

        def cursor(self):
            return Cursor()

        def commit(self):
            self.commit_called = True

        def close(self):
            pass

    context = AccountingContext(
        categories=[{
            "category_id": 1,
            "account_code": "6100",
            "account_name": "Software",
            "account_type": "EXPENSE",
        }],
        examples=[],
    )
    calls = []

    monkeypatch.setenv("AI_ASSISTANT_MODE", "demo")
    monkeypatch.setenv("AI_CATEGORIZATION_MODE", "openai")
    monkeypatch.setattr(analytics, "get_connection", Connection)
    monkeypatch.setattr(
        accounting_rag,
        "get_accounting_context",
        lambda description, vendor, **kwargs: context,
    )

    def fail_normal(**kwargs):
        raise AssertionError("normal/OpenAI categorizer was invoked")

    def fake_demo(**kwargs):
        calls.append(kwargs)
        return CategorySuggestion("Software", 0.90)

    monkeypatch.setattr(
        llm_categorizer,
        "suggest_transaction_category",
        fail_normal,
    )
    monkeypatch.setattr(
        llm_categorizer,
        "suggest_transaction_category_demo",
        fake_demo,
    )

    result = analytics.investigate_uncategorized_transaction(
        transaction_id=123,
        demo_only=True,
    )

    assert result["recommendation"]["category"] == "Software"
    assert calls[0]["transaction_type"] == "EXPENSE"
    assert calls[0]["context"] is context

    import ai_assistant

    response = ai_assistant.ask_assistant(
        "Investigate transaction 123."
    )

    assert response.tool_name == "investigate_uncategorized_transaction"
    assert response.tool_result[0]["result"]["recommendation"][
        "category"
    ] == "Software"


def test_phase7_2_demo_investigation_remains_read_only_and_preserves_type(
    monkeypatch,
):
    import accounting_rag
    import analytics
    import llm_categorizer

    from accounting_rag import AccountingContext
    from llm_categorizer import CategorySuggestion

    executions = []

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql, binds=None):
            executions.append((sql, binds))

        def fetchone(self):
            return (
                123,
                "2026-09-01",
                "SALE",
                "Customer order payment",
                100.0,
                None,
                "Customer",
                "Office Supplies",
                0.60,
                "UNMATCHED",
                "POSTED",
            )

    class Connection:
        def __init__(self):
            self.commit_called = False

        def cursor(self):
            return Cursor()

        def commit(self):
            self.commit_called = True

        def close(self):
            pass

    context = AccountingContext(
        categories=[{
            "category_id": 1,
            "account_code": "4000",
            "account_name": "Sales Revenue",
            "account_type": "REVENUE",
        }],
        examples=[],
    )
    captured = {}
    connection = Connection()

    monkeypatch.setattr(analytics, "get_connection", lambda: connection)
    monkeypatch.setattr(
        accounting_rag,
        "get_accounting_context",
        lambda description, vendor, **kwargs: (
            captured.update(kwargs) or context
        ),
    )
    monkeypatch.setattr(
        llm_categorizer,
        "suggest_transaction_category_demo",
        lambda **kwargs: (
            captured.update({"categorizer": kwargs})
            or CategorySuggestion("Sales Revenue", 0.95)
        ),
    )

    result = analytics.investigate_uncategorized_transaction(
        transaction_id=123,
        demo_only=True,
    )

    sql_text = " ".join(sql for sql, _ in executions).upper()
    assert result["transaction"]["transaction_type"] == "SALE"
    assert captured["exclude_transaction_id"] == 123
    assert captured["categorizer"]["transaction_type"] == "SALE"
    assert "UPDATE" not in sql_text
    assert "INSERT" not in sql_text
    assert "DELETE" not in sql_text
    assert connection.commit_called is False


def test_phase7_2_demo_keeps_chart_of_accounts_validation(monkeypatch):
    import accounting_rag
    import analytics
    import llm_categorizer

    from accounting_rag import AccountingContext
    from llm_categorizer import CategorySuggestion

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql, binds=None):
            pass

        def fetchone(self):
            return (
                123,
                "2026-09-01",
                "EXPENSE",
                "Unknown expense",
                -25.0,
                None,
                "Unknown Vendor",
                None,
                None,
                "UNMATCHED",
                "POSTED",
            )

    class Connection:
        def cursor(self):
            return Cursor()

        def close(self):
            pass

    context = AccountingContext(
        categories=[{
            "category_id": 1,
            "account_code": "6100",
            "account_name": "Software",
            "account_type": "EXPENSE",
        }],
        examples=[],
    )

    monkeypatch.setattr(analytics, "get_connection", Connection)
    monkeypatch.setattr(
        accounting_rag,
        "get_accounting_context",
        lambda description, vendor, **kwargs: context,
    )
    monkeypatch.setattr(
        llm_categorizer,
        "suggest_transaction_category_demo",
        lambda **kwargs: CategorySuggestion("Office Supplies", 0.90),
    )

    with pytest.raises(
        ValueError,
        match="Invalid accounting category returned by AI",
    ):
        analytics.investigate_uncategorized_transaction(
            transaction_id=123,
            demo_only=True,
        )


def test_phase7_2_rag_excludes_target_before_ranking(monkeypatch):
    import accounting_rag

    executions = []

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql, binds=None):
            executions.append((sql, binds or {}))

        def fetchall(self):
            normalized = " ".join(executions[-1][0].split()).upper()
            if "FROM ACCOUNTING_CATEGORIES" in normalized and "JOIN" not in normalized:
                return [(1, "6100", "Software", "EXPENSE")]
            return [(124, "Cloud subscription", "Microsoft", "Software")]

    class Connection:
        def cursor(self):
            return Cursor()

        def close(self):
            pass

    monkeypatch.setattr(accounting_rag, "get_connection", Connection)

    context = accounting_rag.get_accounting_context(
        description="Cloud subscription",
        vendor="Microsoft",
        exclude_transaction_id=123,
    )

    assert [example["transaction_id"] for example in context.examples] == [124]

    candidate_calls = [
        (sql, binds)
        for sql, binds in executions
        if "exclude_transaction_id" in binds
    ]
    assert candidate_calls
    for sql, binds in candidate_calls:
        normalized = " ".join(sql.split()).upper()
        assert "FT.TRANSACTION_ID != :EXCLUDE_TRANSACTION_ID" in normalized
        assert binds["exclude_transaction_id"] == 123
        assert normalized.index("FT.TRANSACTION_ID !=") < normalized.index("FETCH FIRST")


def test_phase7_2_formatter_separates_truth_and_recommendation():
    from ai_assistant import _format_uncategorized_investigation

    result = {
        "transaction": {
            "transaction_id": 123,
            "transaction_type": "EXPENSE",
            "description": "Cloud subscription",
            "vendor": "Microsoft",
            "amount": -50,
            "category": None,
        },
        "investigation_status": "RECOMMENDATION_READY",
        "current_ai_suggestion": {
            "category": "Software",
            "confidence": 0.70,
        },
        "evidence": {
            "historical_examples": [],
            "supporting_example_count": 0,
        },
        "recommendation": {
            "category": "Software",
            "confidence": 0.90,
            "rationale": "Description supports the recommendation.",
        },
    }

    message = _format_uncategorized_investigation(result)

    assert "transaction type EXPENSE" in message
    assert "Final accounting category: not assigned" in message
    assert "Stored AI suggestion" in message
    assert "New read-only recommendation" in message
    assert "No accounting change was made" in message
