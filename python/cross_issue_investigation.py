"""Pure permission and composition contract for Phase 7.4."""


PHASE_7_4_CROSS_ISSUE_ALLOWLIST = frozenset({
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "get_reconciliation_review",
    "get_financial_anomalies",
    "investigate_uncategorized_transaction",
    "investigate_reconciliation_issue",
})

PHASE_7_4_OVERVIEW_TOOL_PLAN = (
    "get_bookkeeping_summary",
    "get_ai_review_queue",
    "get_reconciliation_review",
    "get_financial_anomalies",
)

PHASE_7_4_DRILL_DOWN_TOOL_PLAN = (
    "investigate_uncategorized_transaction",
    "investigate_reconciliation_issue",
)


def _queue_date_key(value):
    """Return a stable, null-safe ordering key without mutating source data."""
    if value is None:
        return (0, "")
    return (1, str(value))


def _transaction_id(row):
    if not isinstance(row, (tuple, list)) or not row:
        return None
    try:
        return int(row[0])
    except (TypeError, ValueError):
        return None


def select_categorization_item(queue):
    """Select one stable financial transaction from the review queue."""
    candidates = [
        row
        for row in (queue or [])
        if _transaction_id(row) is not None
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda row: (
            _queue_date_key(row[1] if len(row) > 1 else None),
            _transaction_id(row),
        ),
    )


def select_reconciliation_item(queue):
    """Select one stable bank transaction from the review queue."""
    candidates = [
        row
        for row in (queue or [])
        if _transaction_id(row) is not None
    ]
    if not candidates:
        return None
    return min(candidates, key=_transaction_id)


def _sorted_queue_ids(queue, *, by_date=False):
    """Return stable IDs without mutating the source review queue."""
    candidates = [
        row
        for row in (queue or [])
        if _transaction_id(row) is not None
    ]
    if by_date:
        candidates.sort(
            key=lambda row: (
                _queue_date_key(row[1] if len(row) > 1 else None),
                _transaction_id(row),
            )
        )
    else:
        candidates.sort(key=_transaction_id)
    return [_transaction_id(row) for row in candidates]


def _anomaly_findings(anomaly_result):
    findings = []
    for anomaly in (anomaly_result or {}).get("anomalies", []):
        subject_ids = list(anomaly.get("transaction_ids", []))
        findings.append({
            "issue_type": "anomaly",
            "subject_ids": subject_ids,
            "status": anomaly.get("anomaly_type"),
            "summary": anomaly.get(
                "reason",
                "A deterministic anomaly signal requires review.",
            ),
            "evidence": anomaly,
            "source_tool": "get_financial_anomalies",
            "detail_level": "overview",
            "requires_human_review": bool(
                anomaly.get("requires_human_review", True)
            ),
        })
    return findings


def compose_cross_issue_investigation(executed_results):
    """Compose bounded source results without changing their raw structures."""
    ordered_results = list(executed_results)
    evidence = {
        tool_name: result
        for tool_name, result in ordered_results
    }

    categorization_queue = evidence.get("get_ai_review_queue") or []
    reconciliation_queue = evidence.get("get_reconciliation_review") or []
    anomaly_result = evidence.get("get_financial_anomalies") or {}

    findings = []

    categorization_ids = _sorted_queue_ids(categorization_queue, by_date=True)
    if categorization_ids:
        findings.append({
            "issue_type": "categorization",
            "subject_ids": categorization_ids,
            "status": "REVIEW_QUEUE",
            "summary": (
                f"{len(categorization_ids)} uncategorized transaction(s) "
                "require review."
            ),
            "evidence": {"queue_count": len(categorization_ids)},
            "source_tool": "get_ai_review_queue",
            "detail_level": "overview",
            "requires_human_review": True,
        })

    categorization_detail = evidence.get(
        "investigate_uncategorized_transaction"
    )
    if categorization_detail is not None:
        transaction = categorization_detail.get("transaction", {})
        findings.append({
            "issue_type": "categorization",
            "subject_id": transaction.get("transaction_id"),
            "status": categorization_detail.get("investigation_status"),
            "summary": (
                "Read-only categorization investigation for transaction "
                f"{transaction.get('transaction_id')}."
            ),
            "evidence": categorization_detail,
            "source_tool": "investigate_uncategorized_transaction",
            "detail_level": "drill_down",
            "requires_human_review": bool(
                categorization_detail.get("requires_human_review", True)
            ),
        })

    reconciliation_ids = _sorted_queue_ids(reconciliation_queue)
    if reconciliation_ids:
        findings.append({
            "issue_type": "reconciliation",
            "subject_ids": reconciliation_ids,
            "status": "REVIEW_QUEUE",
            "summary": (
                f"{len(reconciliation_ids)} reconciliation item(s) "
                "require review."
            ),
            "evidence": {"queue_count": len(reconciliation_ids)},
            "source_tool": "get_reconciliation_review",
            "detail_level": "overview",
            "requires_human_review": True,
        })

    reconciliation_detail = evidence.get("investigate_reconciliation_issue")
    if reconciliation_detail is not None:
        bank_transaction = reconciliation_detail.get("bank_transaction", {})
        findings.append({
            "issue_type": "reconciliation",
            "subject_id": bank_transaction.get("bank_transaction_id"),
            "status": bank_transaction.get("status"),
            "summary": reconciliation_detail.get(
                "assessment", {}
            ).get(
                "explanation",
                "Read-only reconciliation investigation returned.",
            ),
            "evidence": reconciliation_detail,
            "source_tool": "investigate_reconciliation_issue",
            "detail_level": "drill_down",
            "requires_human_review": bool(
                reconciliation_detail.get("requires_human_review", True)
            ),
        })

    findings.extend(_anomaly_findings(anomaly_result))

    requires_human_review = any(
        finding["requires_human_review"]
        for finding in findings
    )

    review_finding_count = sum(
        finding["requires_human_review"] for finding in findings
    )
    if review_finding_count:
        summary = (
            "Cross-issue investigation summary: "
            f"{review_finding_count} finding(s) require attention."
        )
    elif findings:
        summary = (
            "Cross-issue investigation summary: findings were recorded, "
            "but no new human review is required."
        )
    else:
        summary = (
            "Cross-issue investigation summary: no current review or "
            "anomaly signals were found."
        )

    suggested_next_human_action = _suggested_next_action(
        categorization_ids,
        reconciliation_ids,
        anomaly_result,
    )

    return {
        "investigation_type": "cross_issue",
        "summary": summary,
        "findings": findings,
        "evidence": evidence,
        "source_tools": [
            tool_name
            for tool_name, _ in ordered_results
        ],
        "requires_human_review": requires_human_review,
        "suggested_next_human_action": suggested_next_human_action,
    }


def _suggested_next_action(
    categorization_ids,
    reconciliation_ids,
    anomaly_result,
):
    if categorization_ids:
        return (
            "Review the uncategorized transaction "
            f"{categorization_ids[0]}."
        )
    if reconciliation_ids:
        return (
            "Inspect the reconciliation item for bank transaction "
            f"{reconciliation_ids[0]}."
        )

    anomalies = (anomaly_result or {}).get("anomalies", [])
    if anomalies:
        subject_ids = anomalies[0].get("transaction_ids", [])
        if subject_ids:
            return (
                "Review the anomaly signal for transaction "
                f"{subject_ids[0]}."
            )

    return "No immediate cross-issue review action is indicated."
