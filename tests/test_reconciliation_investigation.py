from pathlib import Path
import sys

import pytest


sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))


EXPECTED_PHASE_7_1_TOOLS = {
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "get_reconciliation_review",
    "get_financial_anomalies",
}
EXPECTED_PHASE_7_2_TOOLS = {"investigate_uncategorized_transaction"}


def test_phase7_3_permission_contract_is_exact_and_read_only():
    from reconciliation_investigation import (
        PHASE_7_3_RECONCILIATION_ALLOWLIST,
        PHASE_7_3_RECONCILIATION_TOOL_PLAN,
    )

    assert PHASE_7_3_RECONCILIATION_ALLOWLIST == {
        "investigate_reconciliation_issue",
    }
    assert PHASE_7_3_RECONCILIATION_TOOL_PLAN == (
        "investigate_reconciliation_issue",
    )
    assert isinstance(PHASE_7_3_RECONCILIATION_ALLOWLIST, frozenset)
    assert not PHASE_7_3_RECONCILIATION_ALLOWLIST.intersection({
        "investigate_bank_transaction",
        "run_reconciliation",
        "confirm_bank_transaction_match",
        "reject_bank_transaction_match",
        "log_audit_event",
        "get_audit_log",
    })


def test_phase7_3_contract_module_has_no_runtime_architecture_imports():
    source = (
        Path(__file__).resolve().parents[1]
        / "python"
        / "reconciliation_investigation.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "import analytics",
        "import database",
        "import ai_assistant",
        "import ai_tools",
        "import openai",
    ):
        assert forbidden not in source.lower()


def test_phase7_1_and_phase7_2_allowlists_remain_isolated():
    from categorization_investigation import (
        PHASE_7_2_CATEGORIZATION_ALLOWLIST,
    )
    from financial_investigation import PHASE_7_1_INVESTIGATION_ALLOWLIST

    assert PHASE_7_1_INVESTIGATION_ALLOWLIST == EXPECTED_PHASE_7_1_TOOLS
    assert PHASE_7_2_CATEGORIZATION_ALLOWLIST == EXPECTED_PHASE_7_2_TOOLS
    assert "investigate_reconciliation_issue" not in (
        PHASE_7_1_INVESTIGATION_ALLOWLIST
    )
    assert "investigate_reconciliation_issue" not in (
        PHASE_7_2_CATEGORIZATION_ALLOWLIST
    )


def test_phase7_3_runner_uses_executor_once_with_bank_id(monkeypatch):
    import ai_assistant

    calls = []

    def fake_execute_tool(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        return {"bank_transaction_id": 123}

    monkeypatch.setattr(ai_assistant, "_execute_tool", fake_execute_tool)

    result = ai_assistant._run_phase_7_3_reconciliation_investigation(123)

    assert result == {"bank_transaction_id": 123}
    assert calls == [
        (
            "investigate_reconciliation_issue",
            {"bank_transaction_id": 123},
        )
    ]


@pytest.mark.parametrize(
    "question",
    [
        "Investigate bank transaction 123.",
        "Investigate reconciliation issue 123.",
        "Why does bank transaction 123 need review?",
        "Why is bank transaction 123 unmatched?",
        "What evidence supports bank transaction 123?",
        "Compare bank transaction 123 with its financial transaction.",
    ],
)
def test_phase7_3_questions_route_to_read_only_investigation(question):
    from ai_assistant import _select_tools

    assert _select_tools(question) == [
        "investigate_reconciliation_issue",
    ]


def test_phase7_3_reconciliation_id_extraction_is_narrow():
    from ai_assistant import (
        _extract_bank_transaction_id,
        _extract_transaction_id,
    )

    assert _extract_bank_transaction_id(
        "Investigate reconciliation issue #123"
    ) == 123
    assert _extract_bank_transaction_id(
        "Investigate reconciliation item id 456"
    ) == 456
    assert _extract_bank_transaction_id("Investigate transaction 789") is None
    assert _extract_transaction_id("Investigate transaction 789") == 789


def test_phase7_3_routing_protects_queue_display_and_write_intent():
    from ai_assistant import _select_tools

    assert _select_tools("Show bank transaction 123") != [
        "investigate_reconciliation_issue",
    ]
    assert _select_tools("Show reconciliation review queue") == [
        "get_reconciliation_review",
    ]
    for question in (
        "Confirm bank transaction 123",
        "Reject bank transaction 123",
        "Confirm reconciliation 123",
        "Reject reconciliation 123",
    ):
        assert "investigate_reconciliation_issue" not in _select_tools(
            question
        )


def test_phase7_3_bank_context_precedes_categorization_investigation():
    from ai_assistant import _select_tools

    assert _select_tools(
        "Why is bank transaction 123 uncategorized?"
    ) == ["investigate_reconciliation_issue"]
    assert _select_tools(
        "Why is transaction 123 uncategorized?"
    ) == ["investigate_uncategorized_transaction"]


def test_phase7_3_missing_id_does_not_route_specific_investigation():
    from ai_assistant import _select_tools

    assert "investigate_reconciliation_issue" not in _select_tools(
        "Why is this possible match not confirmed?"
    )


def test_phase7_3_demo_route_is_model_free_and_uses_runner(monkeypatch):
    import ai_assistant

    calls = []

    monkeypatch.delenv("AI_ASSISTANT_MODE", raising=False)
    monkeypatch.setattr(
        ai_assistant,
        "ask_assistant_openai",
        lambda question: pytest.fail("Demo routing must not call OpenAI"),
    )

    def fake_execute_tool(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        return {
            "bank_transaction": {
                "bank_transaction_id": 123,
                "description": "Bank payment",
                "amount": -10,
                "status": "UNMATCHED",
            },
            "candidate_match": None,
            "match": {"match_type": "NO_MATCH", "match_confidence": None},
            "evidence": {},
            "assessment": {
                "code": "NO_MATCH_FOUND",
                "explanation": "No linked candidate exists.",
            },
            "requires_human_review": True,
        }

    monkeypatch.setattr(ai_assistant, "_execute_tool", fake_execute_tool)

    response = ai_assistant.ask_assistant(
        "Investigate reconciliation issue 123."
    )

    assert response.tool_name == "investigate_reconciliation_issue"
    assert calls == [
        (
            "investigate_reconciliation_issue",
            {"bank_transaction_id": 123},
        )
    ]
    assert "Human review is required" in response.message


def test_phase7_3_formatter_labels_stored_metadata_and_evidence():
    from ai_assistant import _format_reconciliation_investigation

    result = {
        "bank_transaction": {
            "bank_transaction_id": 123,
            "description": "Bank payment",
            "amount": -10,
            "status": "UNMATCHED",
        },
        "candidate_match": {
            "transaction_id": 9,
            "description": "Vendor payment",
            "amount": -10,
            "vendor": "Vendor",
        },
        "match": {"match_type": "POSSIBLE_MATCH", "match_confidence": 0.8},
        "evidence": {
            "amount_difference": 0.0,
            "amount_matches": True,
            "date_difference_days": 1,
            "description_token_overlap": 0.5,
        },
        "assessment": {
            "code": "POSSIBLE_MATCH_REVIEW",
            "explanation": "Possible match requires review.",
        },
        "requires_human_review": True,
    }

    message = _format_reconciliation_investigation(result)

    assert "stored reconciliation match metadata" in message
    assert "Amount match: yes." in message
    assert "No reconciliation state was changed" in message
    assert "Human review is required" in message
    assert "AI confidence" not in message


def test_phase7_3_formatter_distinguishes_matched_state_from_stale_metadata():
    from ai_assistant import _format_reconciliation_investigation

    result = {
        "bank_transaction": {
            "bank_transaction_id": 123,
            "description": "Settled payment",
            "amount": -10,
            "status": "MATCHED",
        },
        "candidate_match": None,
        "match": {"match_type": "POSSIBLE_MATCH", "match_confidence": 0.8},
        "evidence": {},
        "assessment": {
            "code": "ALREADY_MATCHED",
            "explanation": "The bank transaction is already matched.",
        },
        "requires_human_review": False,
    }

    message = _format_reconciliation_investigation(result)

    assert "Stored reconciliation state: MATCHED." in message
    assert "no new confirmation is required" in message
    assert "possible match" not in message.lower()
    assert "No reconciliation state was changed" in message
