"""Pure contracts for the deterministic Phase 7.1 investigation overview."""

from collections.abc import Iterable, Mapping
from typing import Any


# This is intentionally independent from TOOL_REGISTRY.  Adding a future tool
# to the global registry must not silently expand the investigation surface.
PHASE_7_1_INVESTIGATION_ALLOWLIST = frozenset({
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "get_reconciliation_review",
    "get_financial_anomalies",
})

PHASE_7_1_INVESTIGATION_TOOL_PLAN = (
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "get_reconciliation_review",
    "get_financial_anomalies",
)


def _result_count(result: Any) -> int:
    if result is None:
        return 0
    if isinstance(result, Mapping):
        anomalies = result.get("anomalies")
        if isinstance(anomalies, list):
            return len(anomalies)
        value = result.get("anomaly_count")
        return int(value or 0)
    if isinstance(result, (str, bytes)):
        return 0
    try:
        return len(result)
    except TypeError:
        return 0


def compose_financial_investigation_overview(
    executed_results: Iterable[tuple[str, Any]],
) -> dict[str, Any]:
    """Compose an immutable, deterministic overview from tool results.

    Tool execution is deliberately outside this module.  The composer only
    receives already-collected results and preserves them under their actual
    tool names.
    """
    ordered_results = list(executed_results)
    evidence = {
        tool_name: result
        for tool_name, result in ordered_results
    }

    ai_review_count = _result_count(
        evidence.get("get_ai_review_queue")
    )
    reconciliation_count = _result_count(
        evidence.get("get_reconciliation_review")
    )
    anomaly_result = evidence.get("get_financial_anomalies")
    anomaly_count = _result_count(anomaly_result)

    findings: list[dict[str, Any]] = []

    if ai_review_count:
        findings.append({
            "finding_type": "AI_CATEGORIZATION_REVIEW",
            "count": ai_review_count,
            "message": (
                f"{ai_review_count} categorization item(s) require review."
            ),
            "requires_human_review": True,
        })

    if reconciliation_count:
        findings.append({
            "finding_type": "RECONCILIATION_REVIEW",
            "count": reconciliation_count,
            "message": (
                f"{reconciliation_count} reconciliation item(s) require review."
            ),
            "requires_human_review": True,
        })

    if anomaly_count:
        findings.append({
            "finding_type": "FINANCIAL_ANOMALY_SIGNALS",
            "count": anomaly_count,
            "message": (
                f"{anomaly_count} financial anomaly signal(s) were detected."
            ),
            "requires_human_review": True,
        })

    requires_human_review = bool(findings)

    if not findings:
        findings.append({
            "finding_type": "NO_CURRENT_SIGNALS",
            "count": 0,
            "message": (
                "No current review or anomaly signals were found."
            ),
            "requires_human_review": False,
        })

    if requires_human_review:
        summary = (
            "Financial investigation overview: "
            f"{len(findings)} issue group(s) require attention."
        )
        next_action = (
            "Review the listed categorization, reconciliation, and anomaly "
            "signals before taking any accounting action."
        )
    else:
        summary = (
            "Financial investigation overview: no current review or anomaly "
            "signals were found."
        )
        next_action = (
            "No immediate investigation action is indicated; continue normal "
            "human review workflows."
        )

    return {
        "investigation_type": "financial_overview",
        "summary": summary,
        "findings": findings,
        "evidence": evidence,
        "source_tools": [
            tool_name
            for tool_name, _ in ordered_results
        ],
        "requires_human_review": requires_human_review,
        "suggested_next_human_action": next_action,
    }
