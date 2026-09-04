"""Pure permission contract for the Phase 7.3 reconciliation drill-down."""


# Keep this contract independent from TOOL_REGISTRY so registry additions do
# not silently expand the reconciliation investigation surface.
PHASE_7_3_RECONCILIATION_ALLOWLIST = frozenset({
    "investigate_reconciliation_issue",
})

PHASE_7_3_RECONCILIATION_TOOL_PLAN = (
    "investigate_reconciliation_issue",
)
