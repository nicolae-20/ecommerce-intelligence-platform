"""Pure permission contract for Phase 7.2 categorization drill-down."""


# Keep this contract independent from TOOL_REGISTRY. Future registry additions
# must not silently become available to the categorization investigation.
PHASE_7_2_CATEGORIZATION_ALLOWLIST = frozenset({
    "investigate_uncategorized_transaction",
})

PHASE_7_2_CATEGORIZATION_TOOL_PLAN = (
    "investigate_uncategorized_transaction",
)
