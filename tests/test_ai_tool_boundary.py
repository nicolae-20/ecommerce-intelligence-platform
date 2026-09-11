import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


EXPECTED_READ_ONLY_TOOLS = {
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "investigate_uncategorized_transaction",
    "get_reconciliation_review",
    "investigate_reconciliation_issue",
    "get_audit_log",
    "get_spending_by_category",
    "get_vendor_totals",
    "get_revenue_analysis",
    "get_expense_trends",
    "get_financial_statistics",
    "get_financial_anomalies",
    "get_transactions_by_date",
    "get_transactions",
}

WRITE_TOOLS_THAT_MUST_NOT_BE_EXPOSED = {
    "approve_transaction_category",
    "assign_transaction_category",
    "reject_transaction_category",
    "confirm_bank_transaction_match",
    "reject_bank_transaction_match",
    "investigate_bank_transaction",
    "run_reconciliation",
    "log_audit_event",
}


def test_tool_registry_preserves_exact_read_only_surface():
    from ai_tools import TOOL_REGISTRY

    assert set(TOOL_REGISTRY) == EXPECTED_READ_ONLY_TOOLS
    assert not (set(TOOL_REGISTRY) & WRITE_TOOLS_THAT_MUST_NOT_BE_EXPOSED)


def test_execute_tool_rejects_unknown_tool():
    from ai_assistant import _execute_tool

    with pytest.raises(ValueError, match="Unknown AI tool requested"):
        _execute_tool("does_not_exist")


def test_execute_tool_rejects_non_object_arguments():
    from ai_assistant import _execute_tool

    with pytest.raises(ValueError, match="arguments must be an object"):
        _execute_tool("get_bookkeeping_summary", [])


def test_execute_tool_rejects_missing_required_arguments(monkeypatch):
    import ai_assistant

    called = False

    def fake_vendor_totals(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_vendor_totals",
        fake_vendor_totals,
    )

    with pytest.raises(ValueError, match="Missing required AI tool argument"):
        ai_assistant._execute_tool(
            "get_vendor_totals",
            {
                "vendor": None,
                "start_date": None,
                "end_date": None,
            },
        )

    assert called is False


def test_execute_tool_rejects_extra_arguments(monkeypatch):
    import ai_assistant

    called = False

    def fake_summary(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_bookkeeping_summary",
        fake_summary,
    )

    with pytest.raises(ValueError, match="Unexpected AI tool argument"):
        ai_assistant._execute_tool(
            "get_bookkeeping_summary",
            {"unexpected": "value"},
        )

    assert called is False


def test_execute_tool_rejects_wrong_type_before_invocation(monkeypatch):
    import ai_assistant

    called = False

    def fake_vendor_totals(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_vendor_totals",
        fake_vendor_totals,
    )

    with pytest.raises(ValueError, match="Invalid AI tool argument type"):
        ai_assistant._execute_tool(
            "get_vendor_totals",
            {
                "vendor": None,
                "start_date": None,
                "end_date": None,
                "limit": "10",
            },
        )

    assert called is False


@pytest.mark.parametrize("limit", [0, 101])
def test_execute_tool_enforces_numeric_ranges(monkeypatch, limit):
    import ai_assistant

    called = False

    def fake_vendor_totals(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_vendor_totals",
        fake_vendor_totals,
    )

    with pytest.raises(ValueError, match="outside the allowed range"):
        ai_assistant._execute_tool(
            "get_vendor_totals",
            {
                "vendor": None,
                "start_date": None,
                "end_date": None,
                "limit": limit,
            },
        )

    assert called is False


def test_execute_tool_rejects_boolean_for_integer(monkeypatch):
    import ai_assistant

    called = False

    def fake_vendor_totals(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_vendor_totals",
        fake_vendor_totals,
    )

    with pytest.raises(ValueError, match="Invalid AI tool argument type"):
        ai_assistant._execute_tool(
            "get_vendor_totals",
            {
                "vendor": None,
                "start_date": None,
                "end_date": None,
                "limit": True,
            },
        )

    assert called is False


def test_execute_tool_rejects_boolean_for_number(monkeypatch):
    import ai_assistant

    called = False

    def fake_transactions(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_transactions",
        fake_transactions,
    )

    arguments = {
        "category": None,
        "vendor": None,
        "transaction_type": None,
        "reconciliation_status": None,
        "categorization_state": None,
        "min_ai_confidence": None,
        "max_ai_confidence": None,
        "min_amount": True,
        "max_amount": None,
        "status": None,
        "start_date": None,
        "end_date": None,
    }

    with pytest.raises(ValueError, match="Invalid AI tool argument type"):
        ai_assistant._execute_tool("get_transactions", arguments)

    assert called is False


def test_execute_tool_rejects_invalid_enum(monkeypatch):
    import ai_assistant

    called = False

    def fake_revenue(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_revenue_analysis",
        fake_revenue,
    )

    with pytest.raises(ValueError, match="not an allowed value"):
        ai_assistant._execute_tool(
            "get_revenue_analysis",
            {
                "start_date": None,
                "end_date": None,
                "period": "quarter",
            },
        )

    assert called is False


def test_execute_tool_rejects_public_internal_only_argument(monkeypatch):
    import ai_assistant

    called = False

    def fake_investigation(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "investigate_uncategorized_transaction",
        fake_investigation,
    )

    with pytest.raises(ValueError, match="Unexpected AI tool argument"):
        ai_assistant._execute_tool(
            "investigate_uncategorized_transaction",
            {
                "transaction_id": 7,
                "demo_only": True,
            },
        )

    assert called is False


def test_execute_tool_allows_bounded_trusted_internal_argument(monkeypatch):
    import ai_assistant

    captured = {}

    def fake_investigation(**kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "investigate_uncategorized_transaction",
        fake_investigation,
    )

    result = ai_assistant._execute_tool(
        "investigate_uncategorized_transaction",
        {"transaction_id": 7},
        internal_arguments={"demo_only": True},
    )

    assert result == {
        "transaction_id": 7,
        "demo_only": True,
    }
    assert captured == result


def test_execute_tool_rejects_unapproved_internal_argument(monkeypatch):
    import ai_assistant

    called = False

    def fake_summary(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_bookkeeping_summary",
        fake_summary,
    )

    with pytest.raises(ValueError, match="Internal AI tool argument is not allowed"):
        ai_assistant._execute_tool(
            "get_bookkeeping_summary",
            {},
            internal_arguments={"demo_only": True},
        )

    assert called is False


def test_valid_arguments_execute_after_validation(monkeypatch):
    import ai_assistant

    captured = {}

    def fake_vendor_totals(**kwargs):
        captured.update(kwargs)
        return [kwargs]

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_vendor_totals",
        fake_vendor_totals,
    )

    arguments = {
        "vendor": "Microsoft",
        "start_date": None,
        "end_date": None,
        "limit": 5,
    }

    assert ai_assistant._execute_tool(
        "get_vendor_totals",
        arguments,
    ) == [arguments]
    assert captured == arguments


def test_openai_tool_call_rejects_extra_argument_before_tool_execution(
    monkeypatch,
):
    import ai_assistant

    called = False

    def fake_summary(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_bookkeeping_summary",
        fake_summary,
    )

    class ToolCall:
        type = "function_call"
        name = "get_bookkeeping_summary"
        arguments = json.dumps({"unexpected": True})
        call_id = "call_boundary"

    class FirstResponse:
        id = "resp_boundary"
        output = [ToolCall()]
        output_text = ""

    class Responses:
        def create(self, **kwargs):
            return FirstResponse()

    class Client:
        def __init__(self):
            self.responses = Responses()

    with pytest.raises(ValueError, match="Unexpected AI tool argument"):
        ai_assistant.ask_assistant_openai(
            "Show the bookkeeping summary.",
            client=Client(),
        )

    assert called is False


def test_openai_tool_call_rejects_malformed_json_before_execution(
    monkeypatch,
):
    import ai_assistant

    called = False

    def fake_summary(**kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_bookkeeping_summary",
        fake_summary,
    )

    class ToolCall:
        type = "function_call"
        name = "get_bookkeeping_summary"
        arguments = "{not-json"
        call_id = "call_bad_json"

    class FirstResponse:
        id = "resp_bad_json"
        output = [ToolCall()]
        output_text = ""

    class Responses:
        def create(self, **kwargs):
            return FirstResponse()

    class Client:
        def __init__(self):
            self.responses = Responses()

    with pytest.raises(json.JSONDecodeError):
        ai_assistant.ask_assistant_openai(
            "Show the bookkeeping summary.",
            client=Client(),
        )

    assert called is False


def test_demo_module_import_does_not_require_openai_sdk():
    project_root = Path(__file__).resolve().parents[1]
    python_dir = project_root / "python"

    code = r'''
import builtins

real_import = builtins.__import__

def blocked_import(name, *args, **kwargs):
    if name == "openai" or name.startswith("openai."):
        raise ModuleNotFoundError("openai intentionally unavailable")
    return real_import(name, *args, **kwargs)

builtins.__import__ = blocked_import
import ai_assistant
assert callable(ai_assistant.ask_assistant)
'''

    env = os.environ.copy()
    env["PYTHONPATH"] = str(python_dir)
    env["AI_ASSISTANT_MODE"] = "demo"

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
