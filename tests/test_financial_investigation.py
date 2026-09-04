from pathlib import Path
import sys

import pytest


sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))


from financial_investigation import (  # noqa: E402
    PHASE_7_1_INVESTIGATION_ALLOWLIST,
    PHASE_7_1_INVESTIGATION_TOOL_PLAN,
    compose_financial_investigation_overview,
)


EXPECTED_TOOLS = (
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "get_reconciliation_review",
    "get_financial_anomalies",
)


def _empty_results():
    return [
        ("get_bookkeeping_summary", (1000, 250, 750, 0)),
        ("get_ai_review_queue", []),
        ("get_reconciliation_review", []),
        (
            "get_financial_anomalies",
            {"anomaly_count": 0, "anomalies": []},
        ),
    ]


def test_phase7_1_allowlist_is_exact_and_ordered():
    from ai_tools import TOOL_REGISTRY

    assert PHASE_7_1_INVESTIGATION_TOOL_PLAN == EXPECTED_TOOLS
    assert PHASE_7_1_INVESTIGATION_ALLOWLIST == set(EXPECTED_TOOLS)
    assert set(EXPECTED_TOOLS).issubset(TOOL_REGISTRY)

    unsafe = {
        "investigate_uncategorized_transaction",
        "investigate_reconciliation_issue",
        "investigate_bank_transaction",
        "get_audit_log",
        "approve_transaction_category",
        "reject_transaction_category",
        "assign_transaction_category",
        "cancel_transaction_rejection",
        "categorize_transaction_with_llm",
        "categorize_uncategorized_transactions",
        "run_reconciliation",
        "reject_bank_transaction_match",
        "confirm_bank_transaction_match",
        "log_audit_event",
    }
    assert PHASE_7_1_INVESTIGATION_ALLOWLIST.isdisjoint(unsafe)


def test_phase7_1_composer_preserves_evidence_and_review_semantics():
    results = [
        ("get_bookkeeping_summary", (1000, 250, 750, 3)),
        ("get_ai_review_queue", [{"transaction_id": 7}]),
        ("get_reconciliation_review", [{"bank_transaction_id": 10}]),
        (
            "get_financial_anomalies",
            {
                "anomaly_count": 1,
                "anomalies": [{
                    "anomaly_type": "LARGE_EXPENSE",
                    "requires_human_review": True,
                }],
            },
        ),
    ]

    result = compose_financial_investigation_overview(results)

    assert result["investigation_type"] == "financial_overview"
    assert result["source_tools"] == list(EXPECTED_TOOLS)
    assert result["evidence"]["get_ai_review_queue"] is results[1][1]
    assert result["evidence"]["get_reconciliation_review"] is results[2][1]
    assert result["evidence"]["get_financial_anomalies"] is results[3][1]
    assert result["requires_human_review"] is True
    assert [finding["finding_type"] for finding in result["findings"]] == [
        "AI_CATEGORIZATION_REVIEW",
        "RECONCILIATION_REVIEW",
        "FINANCIAL_ANOMALY_SIGNALS",
    ]
    assert all(
        finding["requires_human_review"] is True
        for finding in result["findings"]
    )
    assert "confidence" not in result
    assert "accounting_correctness" not in result


def test_phase7_1_empty_results_are_deterministic_and_summary_only_is_safe():
    result = compose_financial_investigation_overview(_empty_results())

    assert result["source_tools"] == list(EXPECTED_TOOLS)
    assert result["requires_human_review"] is False
    assert result["findings"] == [{
        "finding_type": "NO_CURRENT_SIGNALS",
        "count": 0,
        "message": "No current review or anomaly signals were found.",
        "requires_human_review": False,
    }]
    assert "no current review or anomaly signals" in result["summary"]


def test_phase7_1_summary_statistics_alone_do_not_require_review():
    results = _empty_results()
    results[0] = ("get_bookkeeping_summary", (1000, 250, 750, 99))

    result = compose_financial_investigation_overview(results)

    assert result["requires_human_review"] is False
    assert result["findings"][0]["finding_type"] == "NO_CURRENT_SIGNALS"


@pytest.mark.parametrize(
    "finding_tool",
    [
        "get_ai_review_queue",
        "get_reconciliation_review",
        "get_financial_anomalies",
    ],
)
def test_phase7_1_each_review_signal_requires_human_review(finding_tool):
    results = _empty_results()
    index = next(
        index
        for index, (tool_name, _) in enumerate(results)
        if tool_name == finding_tool
    )
    results[index] = (
        finding_tool,
        [{"id": 1}]
        if finding_tool != "get_financial_anomalies"
        else {"anomalies": [{"anomaly_type": "DUPLICATE_TRANSACTION"}]},
    )

    result = compose_financial_investigation_overview(results)

    assert result["requires_human_review"] is True
    assert len(result["findings"]) == 1


def test_phase7_1_demo_execution_uses_executor_once_per_planned_tool(monkeypatch):
    import ai_assistant

    calls = []

    def fake_execute_tool(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        return dict(_empty_results())[tool_name]

    monkeypatch.setattr(ai_assistant, "_execute_tool", fake_execute_tool)

    result = ai_assistant._run_phase_7_1_investigation_overview()

    assert [tool_name for tool_name, _ in calls] == list(EXPECTED_TOOLS)
    assert all(arguments is None for _, arguments in calls)
    assert result["source_tools"] == list(EXPECTED_TOOLS)


def test_phase7_1_runner_cannot_expand_beyond_allowlist(monkeypatch):
    import ai_assistant

    monkeypatch.setattr(
        ai_assistant,
        "PHASE_7_1_INVESTIGATION_TOOL_PLAN",
        ("approve_transaction_category",),
    )

    with pytest.raises(ValueError, match="not allowed"):
        ai_assistant._run_phase_7_1_investigation_overview()


@pytest.mark.parametrize(
    "question",
    [
        "What financial issues need attention?",
        "What should I investigate?",
        "Show me current bookkeeping risks.",
        "Give me a financial investigation overview.",
        "Show me financial anomalies.",
        "Are there anomalies or review items?",
    ],
)
def test_phase7_1_broad_demo_questions_route_to_overview(question):
    from ai_assistant import _select_tools

    assert _select_tools(question) == ["investigate_financial_overview"]


def test_phase7_1_specific_anomaly_questions_keep_existing_route():
    from ai_assistant import _select_tools

    assert _select_tools("Which transactions look unusual?") == [
        "get_financial_anomalies"
    ]
    assert _select_tools("Which accounting anomalies need attention?") == [
        "get_financial_anomalies"
    ]


def test_phase7_1_does_not_swallow_summary_or_unrelated_intents():
    from ai_assistant import _select_tools

    assert _select_tools(
        "What needs attention in the bookkeeping summary?"
    ) == ["get_bookkeeping_summary"]
    assert _select_tools("What is the weather today?") == []


def test_phase7_1_demo_route_does_not_invoke_openai(monkeypatch):
    import ai_assistant

    monkeypatch.setenv("AI_ASSISTANT_MODE", "demo")
    monkeypatch.setattr(
        ai_assistant,
        "ask_assistant_openai",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Demo overview must not call OpenAI")
        ),
    )
    monkeypatch.setattr(
        ai_assistant,
        "_run_phase_7_1_investigation_overview",
        lambda: compose_financial_investigation_overview(_empty_results()),
    )

    response = ai_assistant.ask_assistant(
        "What financial issues need attention?"
    )

    assert response.tool_name == "investigate_financial_overview"
    assert isinstance(response.tool_result, list)
    assert len(response.tool_result) == 1
    assert (
        response.tool_result[0]["tool_name"]
        == "investigate_financial_overview"
    )
    assert (
        response.tool_result[0]["result"]["investigation_type"]
        == "financial_overview"
    )
    assert "No current review or anomaly signals" in response.message


def test_phase7_1_module_has_no_database_or_analytics_execution_dependency():
    import financial_investigation

    assert "get_connection" not in financial_investigation.__dict__
    assert "analytics" not in financial_investigation.__dict__
