from pathlib import Path
import inspect
import sys

import pytest


sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))


OVERVIEW_TOOLS = (
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "get_reconciliation_review",
    "get_financial_anomalies",
)
DRILL_DOWN_TOOLS = (
    "investigate_uncategorized_transaction",
    "investigate_reconciliation_issue",
)


def _category_row(transaction_id, transaction_date):
    # The queue's first two columns are the only columns used for selection.
    return (
        transaction_id,
        transaction_date,
        "EXPENSE",
        "Unknown expense",
        -25.0,
        None,
        "Vendor",
        "Office Supplies",
        0.60,
        "UNMATCHED",
        "POSTED",
    )


def _reconciliation_row(bank_transaction_id):
    return (
        bank_transaction_id,
        "2026-09-01",
        "Bank payment",
        -25.0,
        "UNMATCHED",
        None,
        None,
        "Vendor",
        None,
        None,
        "PENDING",
    )


def _overview_results(category_queue=None, reconciliation_queue=None):
    return {
        "get_bookkeeping_summary": (1000, 250, 750, 2),
        "get_ai_review_queue": (
            [] if category_queue is None else category_queue
        ),
        "get_reconciliation_review": (
            [] if reconciliation_queue is None else reconciliation_queue
        ),
        "get_financial_anomalies": {
            "anomaly_count": 0,
            "anomalies": [],
        },
    }


def test_phase7_4_permission_contract_is_exact_and_read_only():
    import cross_issue_investigation as contract
    from categorization_investigation import PHASE_7_2_CATEGORIZATION_ALLOWLIST
    from financial_investigation import PHASE_7_1_INVESTIGATION_ALLOWLIST
    from reconciliation_investigation import PHASE_7_3_RECONCILIATION_ALLOWLIST

    assert contract.PHASE_7_4_OVERVIEW_TOOL_PLAN == OVERVIEW_TOOLS
    assert contract.PHASE_7_4_DRILL_DOWN_TOOL_PLAN == DRILL_DOWN_TOOLS
    assert contract.PHASE_7_4_CROSS_ISSUE_ALLOWLIST == frozenset(
        (*OVERVIEW_TOOLS, *DRILL_DOWN_TOOLS)
    )
    assert contract.PHASE_7_4_CROSS_ISSUE_ALLOWLIST.isdisjoint({
        "approve_transaction_category",
        "reject_transaction_category",
        "assign_transaction_category",
        "cancel_transaction_rejection",
        "confirm_bank_transaction_match",
        "reject_bank_transaction_match",
        "run_reconciliation",
        "log_audit_event",
        "get_audit_log",
    })
    assert PHASE_7_1_INVESTIGATION_ALLOWLIST == frozenset(OVERVIEW_TOOLS)
    assert PHASE_7_2_CATEGORIZATION_ALLOWLIST == frozenset({
        "investigate_uncategorized_transaction",
    })
    assert PHASE_7_3_RECONCILIATION_ALLOWLIST == frozenset({
        "investigate_reconciliation_issue",
    })


def test_phase7_4_contract_module_has_no_runtime_dependencies():
    import cross_issue_investigation

    source = inspect.getsource(cross_issue_investigation).lower()
    for forbidden in (
        "import analytics",
        "import database",
        "import ai_assistant",
        "import ai_tools",
        "import openai",
        "get_connection",
    ):
        assert forbidden not in source


def test_phase7_4_selectors_are_stable_null_safe_and_non_mutating():
    from cross_issue_investigation import (
        select_categorization_item,
        select_reconciliation_item,
    )

    category_queue = [
        _category_row(22, "2026-09-02"),
        _category_row(11, "2026-09-01"),
        _category_row(7, None),
    ]
    original = list(category_queue)
    assert select_categorization_item(category_queue)[0] == 7
    assert category_queue == original

    tied = [_category_row(22, "2026-09-01"), _category_row(11, "2026-09-01")]
    assert select_categorization_item(tied)[0] == 11

    reconciliation_queue = [_reconciliation_row(91), _reconciliation_row(9)]
    assert select_reconciliation_item(reconciliation_queue)[0] == 9


def test_phase7_4_runner_is_bounded_and_uses_stable_drill_down_args(monkeypatch):
    import ai_assistant

    overview = _overview_results(
        category_queue=[
            _category_row(22, "2026-09-02"),
            _category_row(11, "2026-09-01"),
        ],
        reconciliation_queue=[_reconciliation_row(91), _reconciliation_row(9)],
    )
    calls = []

    def fake_execute_tool(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        if tool_name in overview:
            return overview[tool_name]
        if tool_name == "investigate_uncategorized_transaction":
            return {
                "transaction": {"transaction_id": arguments["transaction_id"]},
                "investigation_status": "RECOMMENDATION_READY",
                "requires_human_review": True,
            }
        return {
            "bank_transaction": {
                "bank_transaction_id": arguments["bank_transaction_id"],
                "status": "UNMATCHED",
            },
            "assessment": {"explanation": "Review the possible match."},
            "requires_human_review": True,
        }

    monkeypatch.setattr(ai_assistant, "_execute_tool", fake_execute_tool)
    result = ai_assistant._run_phase_7_4_cross_issue_investigation()

    assert [name for name, _ in calls] == [
        *OVERVIEW_TOOLS,
        *DRILL_DOWN_TOOLS,
    ]
    assert calls[4] == (
        "investigate_uncategorized_transaction",
        {"transaction_id": 11, "demo_only": True},
    )
    assert calls[5] == (
        "investigate_reconciliation_issue",
        {"bank_transaction_id": 9},
    )
    assert len(calls) <= 6
    assert result["source_tools"] == [name for name, _ in calls]


def test_phase7_4_empty_queues_make_only_four_overview_calls(monkeypatch):
    import ai_assistant

    overview = _overview_results()
    calls = []

    def fake_execute_tool(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        return overview[tool_name]

    monkeypatch.setattr(ai_assistant, "_execute_tool", fake_execute_tool)
    result = ai_assistant._run_phase_7_4_cross_issue_investigation()

    assert calls == [(name, None) for name in OVERVIEW_TOOLS]
    assert result["findings"] == []
    assert result["requires_human_review"] is False
    assert result["suggested_next_human_action"].startswith("No immediate")


def test_phase7_4_composer_preserves_evidence_provenance_and_separates_confidence():
    from cross_issue_investigation import compose_cross_issue_investigation

    category_detail = {
        "transaction": {"transaction_id": 11},
        "investigation_status": "RECOMMENDATION_READY",
        "recommendation": {"category": "Software", "confidence": 0.99},
        "evidence": {"top_retrieval_score": 0.97},
        "requires_human_review": True,
    }
    recon_detail = {
        "bank_transaction": {
            "bank_transaction_id": 9,
            "status": "UNMATCHED",
        },
        "assessment": {"explanation": "No exact match was found."},
        "requires_human_review": True,
    }
    anomaly_result = {
        "anomaly_count": 1,
        "anomalies": [{
            "anomaly_type": "LARGE_EXPENSE",
            "transaction_ids": [44],
            "reason": "Large posted expense.",
            "requires_human_review": True,
        }],
    }
    results = [
        ("get_bookkeeping_summary", (1000, 250, 750, 2)),
        ("get_ai_review_queue", [_category_row(11, "2026-09-01")]),
        ("get_reconciliation_review", [_reconciliation_row(9)]),
        ("get_financial_anomalies", anomaly_result),
        ("investigate_uncategorized_transaction", category_detail),
        ("investigate_reconciliation_issue", recon_detail),
    ]

    result = compose_cross_issue_investigation(results)

    assert result["investigation_type"] == "cross_issue"
    assert result["source_tools"] == [name for name, _ in results]
    assert result["evidence"]["get_financial_anomalies"] is anomaly_result
    assert result["evidence"][
        "investigate_uncategorized_transaction"
    ] is category_detail
    assert result["requires_human_review"] is True
    assert "confidence" not in result
    assert "risk" not in result
    assert {(item["issue_type"], item["detail_level"]) for item in result["findings"]} == {
        ("categorization", "overview"),
        ("categorization", "drill_down"),
        ("reconciliation", "overview"),
        ("reconciliation", "drill_down"),
        ("anomaly", "overview"),
    }
    assert all("source_tool" in finding for finding in result["findings"])
    assert "uncategorized transaction 11" in result["suggested_next_human_action"]


def test_phase7_4_matched_detail_does_not_create_review_requirement():
    from cross_issue_investigation import compose_cross_issue_investigation

    result = compose_cross_issue_investigation([
        ("get_bookkeeping_summary", (1000, 250, 750, 0)),
        ("get_ai_review_queue", []),
        ("get_reconciliation_review", []),
        ("get_financial_anomalies", {"anomalies": []}),
        (
            "investigate_reconciliation_issue",
            {
                "bank_transaction": {
                    "bank_transaction_id": 9,
                    "status": "MATCHED",
                },
                "assessment": {"explanation": "An exact match exists."},
                "requires_human_review": False,
            },
        ),
    ])

    assert result["requires_human_review"] is False
    assert "no new human review is required" in result["summary"]
    assert result["suggested_next_human_action"].startswith("No immediate")


@pytest.mark.parametrize(
    "question",
    [
        "Investigate all current financial issues.",
        "Show the categorization and reconciliation problems together.",
        "Show unresolved bookkeeping issues.",
        "Run a cross-issue investigation.",
        "Explain the most important bookkeeping issues and why.",
        "What should I review first across bookkeeping?",
        "Investigate unresolved issues across bookkeeping.",
        "Summarize the categorization and reconciliation problems across bookkeeping.",
    ],
)
def test_phase7_4_explicit_questions_route_to_cross_issue(question):
    from ai_assistant import _select_tools

    assert _select_tools(question) == ["investigate_cross_issue"]


def test_phase7_4_existing_investigation_routes_remain_narrow():
    from ai_assistant import _select_tools

    assert _select_tools("What financial issues need attention?") == [
        "investigate_financial_overview"
    ]
    assert _select_tools("Investigate transaction 123.") == [
        "investigate_uncategorized_transaction"
    ]
    assert _select_tools("Investigate bank transaction 123.") == [
        "investigate_reconciliation_issue"
    ]
    assert _select_tools("Show reconciliation review queue") == [
        "get_reconciliation_review"
    ]
    assert _select_tools("Confirm bank transaction 123") == []


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "Show the bookkeeping summary across bookkeeping systems.",
            ["get_bookkeeping_summary"],
        ),
        (
            "Show pending transactions across bookkeeping accounts.",
            ["get_transactions"],
        ),
        (
            "Investigate transaction 123 across bookkeeping records.",
            ["investigate_uncategorized_transaction"],
        ),
        (
            "Investigate bank transaction 123 across bookkeeping records.",
            ["investigate_reconciliation_issue"],
        ),
        (
            "Show anomalies across bookkeeping records.",
            ["get_financial_anomalies"],
        ),
        (
            "Confirm bank transaction 123 across bookkeeping systems.",
            [],
        ),
        (
            "Reject bank transaction 123 across bookkeeping systems.",
            [],
        ),
        (
            "Show transactions across bookkeeping accounts.",
            [],
        ),
    ],
)
def test_phase7_4_across_bookkeeping_does_not_swallow_existing_routes(
    question,
    expected,
):
    from ai_assistant import _select_tools

    assert _select_tools(question) == expected


def test_phase7_4_demo_route_is_model_free_and_uses_executor(monkeypatch):
    import ai_assistant

    calls = []
    overview = _overview_results(
        category_queue=[_category_row(11, "2026-09-01")],
        reconciliation_queue=[_reconciliation_row(9)],
    )

    monkeypatch.setenv("AI_ASSISTANT_MODE", "demo")
    monkeypatch.setenv("AI_CATEGORIZATION_MODE", "openai")
    monkeypatch.setattr(
        ai_assistant,
        "ask_assistant_openai",
        lambda *args, **kwargs: pytest.fail("Demo route called OpenAI"),
    )

    def fake_execute_tool(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        if tool_name in overview:
            return overview[tool_name]
        if tool_name == "investigate_uncategorized_transaction":
            return {
                "transaction": {"transaction_id": arguments["transaction_id"]},
                "investigation_status": "RECOMMENDATION_READY",
                "requires_human_review": True,
            }
        return {
            "bank_transaction": {
                "bank_transaction_id": arguments["bank_transaction_id"],
                "status": "UNMATCHED",
            },
            "assessment": {"explanation": "Review required."},
            "requires_human_review": True,
        }

    monkeypatch.setattr(ai_assistant, "_execute_tool", fake_execute_tool)
    response = ai_assistant.ask_assistant(
        "Investigate all current financial issues."
    )

    assert response.tool_name == "investigate_cross_issue"
    assert [name for name, _ in calls] == [*OVERVIEW_TOOLS, *DRILL_DOWN_TOOLS]
    assert calls[4][1] == {"transaction_id": 11, "demo_only": True}
    assert "No accounting or reconciliation state was changed" in response.message


@pytest.mark.parametrize(
    ("category_queue", "reconciliation_queue", "anomalies", "expected_type"),
    [
        ([_category_row(11, "2026-09-01")], [], [], "categorization"),
        ([], [_reconciliation_row(9)], [], "reconciliation"),
        ([], [], [{"anomaly_type": "DUPLICATE_TRANSACTION", "transaction_ids": [3]}], "anomaly"),
    ],
)
def test_phase7_4_mixed_single_signal_composition_is_deterministic(
    category_queue,
    reconciliation_queue,
    anomalies,
    expected_type,
):
    from cross_issue_investigation import compose_cross_issue_investigation

    anomaly_result = {
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }
    result = compose_cross_issue_investigation([
        ("get_bookkeeping_summary", (1000, 250, 750, 1)),
        ("get_ai_review_queue", category_queue),
        ("get_reconciliation_review", reconciliation_queue),
        ("get_financial_anomalies", anomaly_result),
    ])

    assert [finding["issue_type"] for finding in result["findings"]] == [
        expected_type
    ]
    assert result["requires_human_review"] is True
    assert result["source_tools"] == list(OVERVIEW_TOOLS)


def test_phase7_4_formatter_is_grouped_and_preserves_human_boundary():
    from ai_assistant import _format_cross_issue_investigation

    message = _format_cross_issue_investigation({
        "summary": "Cross-issue investigation summary: 2 findings require attention.",
        "findings": [
            {
                "issue_type": "categorization",
                "subject_ids": [11],
                "summary": "Uncategorized transaction requires review.",
                "source_tool": "get_ai_review_queue",
                "detail_level": "overview",
            },
            {
                "issue_type": "reconciliation",
                "subject_id": 9,
                "summary": "Possible match requires review.",
                "source_tool": "investigate_reconciliation_issue",
                "detail_level": "drill_down",
            },
        ],
        "suggested_next_human_action": "Review transaction 11.",
    })

    assert "[categorization]" in message
    assert "[reconciliation]" in message
    assert "Categorization findings:" in message
    assert "Reconciliation findings:" in message
    assert "Source: get_ai_review_queue" in message
    assert "detail: drill_down" in message
    assert "No accounting or reconciliation state was changed" in message
    assert "Final decisions remain human-controlled" in message
    assert "not final accounting assignments or matches" in message
    assert "deterministic review order" in message
    assert "materiality or risk ranking" in message
    for forbidden in (
        "overall confidence",
        "combined confidence",
        "investigation confidence",
        "risk probability",
        "accounting correctness score",
        "weighted confidence",
    ):
        assert forbidden not in message.lower()


def test_phase7_4_formatter_preserves_labelled_source_evidence():
    from ai_assistant import _format_cross_issue_investigation

    message = _format_cross_issue_investigation({
        "summary": "Cross-issue investigation summary: 3 findings require attention.",
        "findings": [
            {
                "issue_type": "categorization",
                "subject_id": 11,
                "summary": "Read-only categorization investigation for transaction 11.",
                "source_tool": "investigate_uncategorized_transaction",
                "detail_level": "drill_down",
                "evidence": {
                    "transaction": {
                        "transaction_id": 11,
                        "category": None,
                    },
                    "current_ai_suggestion": {
                        "category": "Office Supplies",
                        "confidence": 0.62,
                    },
                    "recommendation": {
                        "category": "Software",
                        "confidence": 0.91,
                    },
                    "evidence": {
                        "supporting_example_count": 2,
                        "retrieved_category_conflict": True,
                    },
                    "requires_human_review": True,
                },
            },
            {
                "issue_type": "reconciliation",
                "subject_id": 9,
                "summary": "Possible match requires review.",
                "source_tool": "investigate_reconciliation_issue",
                "detail_level": "drill_down",
                "evidence": {
                    "bank_transaction": {
                        "bank_transaction_id": 9,
                        "status": "UNMATCHED",
                    },
                    "match": {
                        "match_type": "POSSIBLE_MATCH",
                        "match_confidence": 0.84,
                    },
                    "candidate_match": {"transaction_id": 44},
                    "evidence": {
                        "amount_difference": 1.25,
                        "amount_matches": False,
                        "date_difference_days": 2,
                        "description_token_overlap": 0.50,
                    },
                    "assessment": {
                        "explanation": "Review the possible match.",
                    },
                    "requires_human_review": True,
                },
            },
            {
                "issue_type": "anomaly",
                "subject_ids": [44],
                "summary": "Large posted expense.",
                "source_tool": "get_financial_anomalies",
                "detail_level": "overview",
                "status": "LARGE_EXPENSE",
                "evidence": {
                    "anomaly_type": "LARGE_EXPENSE",
                    "severity": "HIGH",
                    "transaction_ids": [44],
                    "reason": "Posted expense exceeds the threshold.",
                },
            },
        ],
        "suggested_next_human_action": "Review transaction 11.",
    })

    assert "Final accounting category: not assigned" in message
    assert "Stored AI suggestion: Office Supplies" in message
    assert "Stored AI confidence: 62%" in message
    assert "not approved accounting truth" in message
    assert "New read-only recommendation: Software" in message
    assert "Recommendation confidence: 91%" in message
    assert "not persisted or final" in message
    assert "Supporting trusted historical evidence: 2" in message
    assert "human judgment is required" in message
    assert "Authoritative stored reconciliation state: UNMATCHED" in message
    assert "Stored match type: POSSIBLE_MATCH" in message
    assert "Stored reconciliation match confidence: 84%" in message
    assert "not a probability" in message
    assert "Linked candidate financial transaction ID: 44" in message
    assert "Amount comparison: not an exact match; difference 1.25" in message
    assert "Date comparison: 2 day(s) apart" in message
    assert "Description-token overlap: 50%" in message
    assert "POSSIBLE_MATCH remains unconfirmed" in message
    assert "Deterministic anomaly signal: LARGE_EXPENSE" in message
    assert "source severity: HIGH" in message
    assert "not a confirmed accounting error" in message
    assert "deterministic review order" in message
    assert "No accounting or reconciliation state was changed" in message
    assert "Final decisions remain human-controlled" in message

    for forbidden in (
        "overall confidence",
        "combined confidence",
        "investigation confidence",
        "risk probability",
        "accounting correctness score",
        "weighted confidence",
    ):
        assert forbidden not in message.lower()


def test_phase7_4_runner_source_does_not_bypass_executor_or_call_prior_runners():
    import ai_assistant

    source = inspect.getsource(
        ai_assistant._run_phase_7_4_cross_issue_investigation
    )
    assert "_execute_tool" in source
    assert "_run_phase_7_1" not in source
    assert "_run_phase_7_2" not in source
    assert "_run_phase_7_3" not in source
    assert "TOOL_REGISTRY" not in source
    for forbidden in (
        "categorize_transaction_with_llm",
        "categorize_uncategorized_transactions",
        "approve_transaction_category",
        "reject_transaction_category",
        "assign_transaction_category",
        "confirm_bank_transaction_match",
        "reject_bank_transaction_match",
        "run_reconciliation",
        "log_audit_event",
        "commit(",
        "UPDATE",
        "INSERT",
        "DELETE",
    ):
        assert forbidden not in source


def test_phase7_4_is_not_exposed_as_an_openai_function_tool():
    from ai_tools import TOOL_DEFINITIONS

    assert "investigate_cross_issue" not in {
        definition["name"] for definition in TOOL_DEFINITIONS
    }
