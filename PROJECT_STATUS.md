# PROJECT_STATUS.md

# E-commerce Intelligence Platform — Current Implementation Status

## Status Snapshot

This document describes the current known implementation state.

Snapshot baseline:

```text
92 passed
0 failed
0 errors
```

This test count is a checkpoint, not a permanent target.

Future milestones are expected to add tests.

---

# 1. Project Summary

The repository is a portfolio-grade E-commerce Intelligence and AI Bookkeeping application.

The project currently combines:

* Oracle AI Database 26ai Free
* SQL / PL/SQL
* Python
* FastAPI
* Pydantic
* React
* TypeScript
* Vite
* pytest
* bookkeeping
* bank reconciliation
* audit trail
* AI categorization
* accounting RAG
* AI tools
* AI Assistant
* optional OpenAI Responses API integration

The application is deliberately designed so that normal development can continue without paid OpenAI API calls.

---

# 2. Local Environment

Project root:

```text
C:\Users\WINDOWS 10\ecommerce-intelligence-platform
```

Python virtual environment:

```text
python\.venv
```

Activation:

```cmd
python\.venv\Scripts\activate
```

Backend:

```cmd
uvicorn api.main:app --reload
```

Frontend:

```cmd
cd frontend
npm run dev
```

Frontend production build:

```cmd
cd frontend
npm run build
```

Tests:

```cmd
pytest
```

---

# 3. Database Status

Oracle AI Database 26ai Free is installed and working locally.

SQL Developer connectivity is working.

## Core business tables known to exist

* customers
* categories
* suppliers
* products
* orders
* order_items
* payments
* reviews
* discounts
* departments
* employees

## Accounting-related tables

* financial_transactions
* accounting_categories
* bank_transactions
* audit_log

---

# 4. Accounting Categories

Known accounting categories include:

| Code | Category           | Type    |
| ---- | ------------------ | ------- |
| 4000 | Sales Revenue      | REVENUE |
| 5000 | Cost of Goods Sold | COGS    |
| 6100 | Software           | EXPENSE |
| 6200 | Office Supplies    | EXPENSE |
| 6300 | Bank Fees          | EXPENSE |
| 6400 | Travel             | EXPENSE |
| 6500 | Advertising        | EXPENSE |
| 6600 | Utilities          | EXPENSE |

Verify current database contents before assuming these are the only categories.

---

# 5. Bookkeeping Module

Implemented bookkeeping capabilities include:

* revenue calculation
* expense calculation
* net financial movement
* count of transactions requiring review
* transaction review queue
* AI categorization review queue
* category assignment
* category approval
* category rejection
* selected cancellation/reversal workflows
* bookkeeping summary

Known function:

```text
get_bookkeeping_summary()
```

The summary uses posted transactions for revenue/expense/net calculations.

---

# 6. Bank Reconciliation

Bank reconciliation functionality is implemented.

Supported concepts include:

* exact matches
* possible matches
* no-match cases
* match type
* match confidence
* investigation status
* reconciliation confirmation
* reconciliation rejection
* investigation workflow

Important intended semantics:

```text
EXACT_MATCH
    → strong/final match behavior

POSSIBLE_MATCH
    → remains human-reviewable

NO_MATCH
    → investigate
```

Possible matches should not silently become final reconciliations.

Known review function:

```text
get_reconciliation_review_queue()
```

---

# 7. Audit Trail

Audit logging exists.

Known actions include:

```text
TRANSACTION_INVESTIGATED
RECONCILIATION_REJECTED
RECONCILIATION_CONFIRMED
REJECTION_CANCELLED
CATEGORY_REJECTED
CATEGORY_APPROVED
```

Known analytics function:

```text
get_audit_log()
```

The audit log is exposed through bookkeeping backend functionality.

---

# 8. Python Analytics Layer

Important file:

```text
python/analytics.py
```

Known implemented functionality includes:

* bookkeeping summary
* generic bookkeeping review queue
* AI categorization review queue
* reconciliation review queue
* audit log retrieval
* category actions
* reconciliation actions
* AI categorization batch integration

Known functions include:

```text
get_bookkeeping_summary()
get_transactions_requiring_review()
get_ai_categorization_review_queue()
get_reconciliation_review_queue()
get_audit_log()
```

There are additional action functions in the file.

Inspect the implementation before adding overlapping functionality.

---

# 9. FastAPI Backend

Main bookkeeping implementation files include:

```text
api/routers/bookkeeping.py
api/schemas/bookkeeping.py
```

Known bookkeeping API capabilities include:

```text
/bookkeeping/summary
/bookkeeping/review-queue
/bookkeeping/ai-review-queue
/bookkeeping/categories
/bookkeeping/reconciliation-review
/bookkeeping/audit-log
/bookkeeping/ai-categorize
/bookkeeping/ai-assistant
```

Additional category and reconciliation action endpoints also exist.

Do not assume this list contains every route.

Inspect `api/routers/bookkeeping.py` before changing API behavior.

---

# 10. React Frontend

Main known file:

```text
frontend/src/App.tsx
```

The application already contains dashboard functionality for areas including:

* Financial Overview
* Financial Performance
* Bookkeeping Summary
* AI Categorization Review
* Reconciliation Review
* Audit Log

AI Assistant frontend work has been started or scaffolded, but should NOT be treated as fully polished or complete.

Known AI Assistant-related state/integration work may include:

* assistant question
* assistant response
* assistant loading state

Inspect the actual current `App.tsx` before continuing frontend Assistant work.

The roadmap intentionally contains a later milestone for completing the AI Assistant UX.

---

# 11. AI Categorization

Important file:

```text
python/llm_categorizer.py
```

Implemented capabilities include:

* Demo/Mock Mode
* optional real OpenAI mode
* structured category suggestion
* AI confidence
* high-confidence threshold
* category validation against Oracle accounting categories
* invalid AI category protection
* prevention of overwriting finalized categories
* batch categorization
* RAG context injection

Known confidence threshold:

```text
0.80
```

Development should continue in Demo/Mock Mode unless real API use is explicitly requested.

---

# 12. OpenAI API Status

The project contains optional OpenAI integration.

The user currently prefers development without paid API calls.

The automated test suite should not depend on real API usage.

Real OpenAI tool-calling behavior is tested using mocks.

Do not confuse:

* ChatGPT/Codex subscription usage
* OpenAI API billing used by the application itself

They are separate.

---

# 13. Accounting RAG

Important file:

```text
python/accounting_rag.py
```

Known structure:

```text
AccountingContext
```

Known context includes:

* categories
* historical examples

RAG retrieves active Oracle accounting categories and finalized historical accounting examples.

Important trust rule:

```text
category IS NOT NULL / finalized accounting data
    → may be historical evidence

unconfirmed AI suggestion
    → must not become trusted historical truth
```

A known example of expected behavior:

A finalized Office Depot / Office Supplies transaction can be retrieved as a historical example.

A Microsoft 365 transaction with only an unapproved AI suggestion should not automatically become trusted RAG history.

---

# 14. AI Tool Layer

Important file:

```text
python/ai_tools.py
```

The architecture uses:

```text
TOOL_REGISTRY
TOOL_DEFINITIONS
```

Known registered tools at the current checkpoint:

```text
get_bookkeeping_summary
get_ai_review_queue
get_reconciliation_review
get_audit_log
get_transactions_by_date
get_transactions
```

Verify the live code before changing this registry.

---

# 15. Generic AI Tool Executor

Important file:

```text
python/ai_assistant.py
```

A generic execution layer exists:

```text
_execute_tool()
```

Conceptually:

```text
tool name
    ↓
validate against TOOL_REGISTRY
    ↓
arguments
    ↓
tool(**arguments)
```

Both Demo Mode and OpenAI Mode are intended to use this common execution path.

Do not reintroduce separate direct business-logic execution paths unnecessarily.

---

# 16. AI Assistant Modes

Important file:

```text
python/ai_assistant.py
```

The Assistant supports:

```text
demo
openai
```

Environment variable:

```text
AI_ASSISTANT_MODE
```

Default behavior is intended to be:

```text
demo
```

The public entry point is:

```text
ask_assistant(...)
```

---

# 17. Demo Assistant

Demo Mode currently includes deterministic routing and parsing.

Known capabilities include:

* bookkeeping summary selection
* AI review selection
* reconciliation review selection
* audit log selection
* multiple tools in one request
* ISO date range extraction
* transaction filter extraction
* formatted local responses

The multi-tool selector is expected to avoid duplicate tool names.

A regression was previously fixed where tools were appended twice.

Preserve deduplication behavior.

---

# 18. OpenAI Responses API Integration

The OpenAI Assistant path has been implemented and tested with mocks.

Known flow:

```text
1. send user question and TOOL_DEFINITIONS
2. receive function_call output
3. validate requested tool
4. parse JSON arguments
5. call _execute_tool(...)
6. return function_call_output
7. request final natural-language answer
```

The implementation uses `previous_response_id` for the follow-up Responses API call.

No real paid API request should be required by tests.

---

# 19. Date-Range Transaction Tool

Known tool:

```text
get_transactions_by_date
```

Purpose:

Retrieve financial transactions in an inclusive date range.

Known arguments:

```text
start_date
end_date
```

Expected date format:

```text
YYYY-MM-DD
```

Example Demo query:

```text
Show me transactions from 2026-08-01 to 2026-08-10.
```

---

# 20. General Transaction Query Tool

Known tool:

```text
get_transactions
```

Current known filter arguments:

```text
category
vendor
min_amount
max_amount
status
start_date
end_date
```

Amount comparisons use transaction magnitude through `ABS(amount)` where implemented.

This allows a negative expense such as:

```text
-129.00
```

to satisfy a natural-language condition such as:

```text
expenses over €50
```

Known supported query examples include:

```text
Show me Microsoft transactions
```

```text
Show me posted Office Depot Office Supplies expenses over €80 between 2026-08-01 and 2026-08-31
```

```text
Show me Software expenses over €50
```

```text
Show me pending Software transactions under €100
```

```text
Show me Software expenses over €50 between 2026-08-01 and 2026-08-31
```

---

# 21. Transaction Filter Parsing

Known Demo Mode parser:

```text
_extract_transaction_filters(...)
```

Current known parsed fields:

```text
category
vendor
min_amount
max_amount
status
start_date
end_date
```

Known categories recognized deterministically include accounting categories such as:

* Sales Revenue
* Cost of Goods Sold
* Software
* Office Supplies
* Bank Fees
* Travel
* Advertising
* Utilities

Known vendors recognized deterministically include:

* Amazon Web Services
* Microsoft
* Office Depot

Vendor matching in the SQL tool is case-insensitive and supports partial names.

Do not assume hard-coded category parsing is the final architecture.

Improving it is part of future roadmap work.

---

# 22. Date Parsing

Known deterministic function:

```text
_extract_date_range(...)
```

Current implementation recognizes two explicit ISO dates.

Example:

```text
2026-08-01
2026-08-31
```

Relative date language such as:

```text
last month
this month
last 30 days
```

is not yet considered complete.

It belongs to future roadmap work.

---

# 23. AI Tool Result Formatting

Assistant formatting functions exist for known tools.

Examples include formatters for:

* bookkeeping summary
* AI review queue
* reconciliation review
* audit log
* transactions by date
* general transaction results

Do not return raw internal Python objects to the user when an existing formatter is appropriate.

---

# 24. Tests

Known test files include:

```text
tests/test_analytics.py
tests/test_api.py
```

Current known baseline:

```text
92 passed
```

Tests currently cover significant areas including:

* analytics
* bookkeeping
* reconciliation
* categorization
* accounting RAG
* tool definitions
* generic tool execution
* Demo Assistant
* multi-tool routing
* transaction filters
* vendor-only and combined vendor filters
* date ranges
* OpenAI mode routing
* mocked Responses API function calling
* API endpoints
* shared environment-based database connection configuration

---

# 25. Known Recent Regression Fixes

These historical issues were already fixed and should not be reintroduced.

## Duplicate tool selection

`get_transactions` and `get_transactions_by_date` were accidentally appended twice in `_select_tools()`.

The selector was cleaned up and deduplicated.

## Missing bookkeeping summary route

A temporary rewrite of `_select_tools()` accidentally removed the bookkeeping summary rule.

The rule was restored.

## Pydantic datetime conversion

A transaction review response previously required correct datetime serialization.

Avoid broad global changes when a schema-specific conversion is sufficient.

## Accidental NameError

An earlier edit accidentally referenced `row` in category assignment logic.

This was corrected.

---

# 26. Current Known Design Principles

## SQL for deterministic finance

Prefer SQL for:

* totals
* grouping
* ranking
* financial aggregation
* date filtering

## AI for interpretation

Prefer AI for:

* understanding questions
* selecting tools
* explaining results
* categorization suggestions
* investigation
* recommendations

## Human for important writes

Prefer explicit user approval for important accounting changes.

---

# 27. Git / Secret Status

Database connections are centralized through the environment-based helper in:

```text
python/database.py
```

The legacy `python/db_connection.py` entry point reuses that helper and no
longer contains hard-coded Oracle credentials.

`python/.env` is ignored by Git through the repository's `.env` ignore rule
and is not tracked.

A database credential previously existed in committed Git history. Removing
it from the working tree does not remove it from earlier commits, so the
credential must be rotated manually before the repository is shared.

Do not assume that remains true forever.

Before milestone commits:

```cmd
git status
```

Verify no secret files are staged.

---

# 28. What Is NOT Yet Complete

The following should not be represented as finished.

## Natural-language financial querying

Still needs expansion beyond current filters.

Planned additions include:

* transaction_type
* reconciliation_status
* categorized / uncategorized
* AI confidence filtering
* improved amount parsing
* richer date expressions

## Financial analytics AI tools

Dedicated aggregation tools such as:

* spending by category
* vendor totals
* monthly revenue
* monthly expenses
* financial trends

are still roadmap work.

## AI Assistant frontend

The Assistant UI should be considered incomplete or partially implemented until inspected and finished.

Planned improvements include:

* polished response rendering
* structured tables
* suggested questions
* conversation history
* clearer tool transparency

## Advanced RAG

Similarity retrieval, policy documents, and source-aware answers remain future work.

## Agentic workflows

Read-only investigation agents are not yet considered complete.

## MCP

Not yet considered implemented.

## Docker / deployment

Not yet considered complete.

## Final portfolio documentation

Not yet complete.

---

# 29. Immediate Next Milestone

The next planned backend milestone is:

```text
Phase 1
Milestone 1.2 — Transaction Type Filtering
```

Extend `get_transactions` and deterministic Demo Mode parsing with a
`transaction_type` filter using the actual database values.

Primary files likely involved:

```text
python/ai_tools.py
python/ai_assistant.py
tests/test_analytics.py
```

Potential API changes are not expected unless implementation inspection shows they are needed.

---

# 30. Immediate Next Query Targets

After the next milestone, Demo Mode should be able to support queries conceptually similar to:

```text
Show me expense transactions.
```

```text
Show me posted bank fee transactions.
```

```text
Show me posted Microsoft expense transactions.
```

The exact parser behavior should be deterministic and covered by tests.

---

# 31. Next Milestone Definition of Done

The immediate milestone is complete when:

* `tool_get_transactions()` accepts `transaction_type`
* Oracle SQL uses bind parameters
* `TOOL_DEFINITIONS` exposes `transaction_type`
* Demo Mode extracts supported transaction types
* transaction type composes with category/vendor/status filters
* existing transaction filter behavior remains correct
* new tests are added
* full pytest suite passes
* this file is updated with the new baseline
* the corresponding roadmap milestone is marked complete

---

# 32. Codex Handoff State

When opening this repository in Codex, start by reading:

```text
AGENTS.md
PROJECT_STATUS.md
ROADMAP.md
```

Then inspect:

```text
python/ai_tools.py
python/ai_assistant.py
tests/test_analytics.py
```

before implementing the next milestone.

Do not assume this document is more current than the repository itself.
