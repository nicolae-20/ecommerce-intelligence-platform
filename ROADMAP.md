# ROADMAP.md

# E-commerce Intelligence Platform — Delivery Roadmap

## Purpose

This roadmap defines the intended development sequence from the current working application to a portfolio-ready E-commerce Intelligence and AI Bookkeeping platform.

It is written for both:

* the developer
* coding agents such as Codex

It must distinguish clearly between:

* completed foundations
* current work
* future work

Do not mark a milestone complete until its Definition of Done has been satisfied.

---

# CURRENT CHECKPOINT

Current verified test baseline:

```text
122 passed
0 failed
0 errors
```

Current automated regression command:

```cmd
pytest tests
```

Credential-history remediation is complete and fresh-clone validated.

Current next area:

```text
Natural-Language Financial Querying
```

---

# COMPLETED FOUNDATIONS

The following are considered substantially implemented, subject to normal future refinement.

## Database foundation

* [x] Oracle AI Database 26ai Free setup
* [x] core e-commerce schema
* [x] accounting categories
* [x] financial transactions
* [x] bank transactions
* [x] audit log

## Backend foundation

* [x] Python analytics/business logic
* [x] FastAPI application
* [x] bookkeeping endpoints
* [x] reconciliation endpoints
* [x] audit retrieval
* [x] automated backend tests

## Frontend foundation

* [x] React
* [x] TypeScript
* [x] Vite
* [x] financial dashboard foundation
* [x] bookkeeping views
* [x] AI categorization review UI
* [x] reconciliation review UI
* [x] audit log UI

AI Assistant frontend polish is NOT included in this completed list.

## Bookkeeping

* [x] bookkeeping summary
* [x] category assignment
* [x] category approval/rejection
* [x] review queues
* [x] posted revenue/expense calculations

## Reconciliation

* [x] exact-match workflow
* [x] possible-match review
* [x] no-match investigation
* [x] match confidence/type
* [x] reconciliation actions
* [x] audit integration

## AI categorization

* [x] Demo/Mock Mode
* [x] optional OpenAI path
* [x] category suggestions
* [x] confidence score
* [x] validation against accounting categories
* [x] protection against invalid categories
* [x] finalized category protection
* [x] batch categorization

## Accounting RAG foundation

* [x] retrieve active accounting categories
* [x] retrieve finalized historical examples
* [x] avoid treating unconfirmed AI suggestions as trusted truth
* [x] inject context into categorization

## AI Assistant foundation

* [x] Demo Mode
* [x] OpenAI mode architecture
* [x] generic tool registry
* [x] generic `_execute_tool()`
* [x] mocked Responses API tool calling
* [x] multiple read-only tools
* [x] multi-tool Demo routing
* [x] explicit ISO date-range querying
* [x] category filtering
* [x] minimum amount filtering
* [x] maximum amount filtering
* [x] transaction status filtering
* [x] date filtering in general transaction query
* [x] vendor filtering

## Security remediation

* [x] exposed Oracle credential rotated
* [x] hard-coded database credentials removed from tracked source
* [x] credential-bearing Git history removed with `git-filter-repo` sensitive-data-removal mode
* [x] rewritten `main` updated with exact force-with-lease protection
* [x] fresh-clone history, source, and automated-test validation completed
* [x] `.env` remains ignored and untracked

---

# PHASE 1 — COMPLETE NATURAL-LANGUAGE FINANCIAL QUERYING

Goal:

Build a strong deterministic querying layer before adding more autonomous AI behavior.

Status: complete. All Phase 1 transaction filters compose correctly, SQL bind
safety is verified, and complex Demo Mode routing passes through the generic
`_execute_tool()` architecture.

---

## Milestone 1.1 — Vendor Filtering

### Goal

Allow `get_transactions` to filter transactions by vendor.

### Likely files

```text
python/ai_tools.py
python/ai_assistant.py
tests/test_analytics.py
```

### Implementation requirements

* add optional `vendor`
* use Oracle bind parameters
* expose vendor in `TOOL_DEFINITIONS`
* preserve current filters
* extract known vendor language in Demo Mode
* support vendor combined with existing filters

### Example queries

```text
Show me Microsoft transactions.
```

```text
Show me Microsoft Software expenses over €50.
```

### Definition of Done

* [x] tool accepts vendor
* [x] SQL filtering works
* [x] OpenAI schema exposes vendor
* [x] Demo parser extracts vendor
* [x] combined filtering works
* [x] tests added
* [x] full pytest suite passes
* [x] PROJECT_STATUS updated

---

## Milestone 1.2 — Transaction Type Filtering

### Goal

Filter by values such as:

```text
SALE
EXPENSE
BANK_FEE
```

Use actual database values found in the repository rather than assuming these are exhaustive.

### Example queries

```text
Show me expense transactions.
```

```text
Show me posted bank fees.
```

### Definition of Done

* [x] `transaction_type` filter added
* [x] SQL is parameterized
* [x] tool schema updated
* [x] deterministic parser updated
* [x] combination with category/vendor/status works
* [x] tests pass — 96 passed

---

## Milestone 1.3 — Reconciliation Status Filtering

### Goal

Allow natural-language queries based on reconciliation state.

### Examples

```text
Show me unmatched Software transactions.
```

```text
Show me unmatched Microsoft expenses.
```

### Definition of Done

* [x] reconciliation filter exists
* [x] actual database status values are validated
* [x] parser supports relevant vocabulary
* [x] combined filtering works
* [x] regression tests pass — 99 passed

---

## Milestone 1.4 — Categorization State Filtering

Support concepts such as:

```text
categorized
uncategorized
```

Potential implementation may use:

```text
category IS NULL
category IS NOT NULL
```

Do not create fake accounting categories to represent uncategorized state.

### Definition of Done

* [x] query layer supports categorized state
* [x] SQL semantics are correct
* [x] Demo parser supports natural language
* [x] tests pass — 102 passed

---

## Milestone 1.5 — AI Confidence Filtering

Support questions such as:

```text
Show me AI suggestions below 80% confidence.
```

```text
Show high-confidence uncategorized transactions.
```

### Requirements

* define threshold semantics explicitly
* do not confuse AI suggestion confidence with finalized category confidence
* preserve existing human-review rules

### Definition of Done

* [x] confidence filtering implemented
* [x] percentage parsing tested
* [x] review workflow semantics preserved
* [x] tests pass — 105 passed

---

## Milestone 1.6 — Amount Parsing Improvements

Current deterministic parser supports basic amount comparisons.

Expand support for:

```text
over 50
above €50
more than €50
at least €50
under €100
below 100
less than 100 euros
at most €100
between €50 and €200
```

### Requirements

Define inclusive/exclusive behavior explicitly.

Examples:

```text
over 50
    → > or >= must be intentionally chosen

at least 50
    → >= 50

at most 100
    → <= 100
```

If current SQL only supports inclusive min/max filters, document and test that behavior rather than pretending linguistic distinctions are exact.

### Definition of Done

* [x] supported phrases documented
* [x] parser is deterministic
* [x] amount range supported
* [x] ambiguous input does not crash
* [x] tests pass — 111 passed

---

## Milestone 1.7 — Date Parsing Improvements

Current parser supports explicit ISO date ranges.

Add deterministic support for useful expressions such as:

```text
this month
last month
this year
last 30 days
```

Only add expressions that can be implemented reliably.

### Requirements

* use explicit timezone/date assumptions
* keep date resolution testable
* avoid dependence on OpenAI for Demo Mode dates

### Definition of Done

* [x] relative dates resolved deterministically
* [x] boundary dates tested
* [x] current ISO behavior preserved
* [x] tests pass — 111 passed

---

## Milestone 1.8 — Combined Filter Hardening

Goal:

Ensure all supported filters compose correctly.

Target query:

```text
Show me posted Microsoft Software expenses over €50 between 2026-08-01 and 2026-08-31.
```

Expected conceptual arguments:

```python
{
    "category": "Software",
    "vendor": "Microsoft",
    "min_amount": 50,
    "max_amount": None,
    "status": "POSTED",
    "start_date": "2026-08-01",
    "end_date": "2026-08-31",
}
```

Additional fields may exist by this milestone.

### Definition of Done

* [x] filters compose safely
* [x] no duplicate tool routing
* [x] no invalid Oracle binds
* [x] tests cover representative combinations
* [x] full suite passes — 114 passed

---

# PHASE 2 — FINANCIAL ANALYTICS TOOLKIT

Goal:

Move calculations into dedicated SQL-backed financial tools rather than asking AI to infer totals from raw transactions.

`financial_transactions` is the accounting source of truth. Posted `EXPENSE`
and `BANK_FEE` spending uses `ABS(amount)`, with optional inclusive date filters
passed through Oracle bind parameters.

---

## Milestone 2.1 — Spending by Category

Create a read-only analytics tool.

Example:

```text
get_spending_by_category
```

Questions:

```text
How much did we spend on Software?
```

```text
Which expense category costs the most?
```

### Definition of Done

* [x] Oracle aggregation implemented
* [x] tool registry/schema updated
* [x] Demo routing supported where useful
* [x] formatter implemented
* [x] tests pass — 122 passed

---

## Milestone 2.2 — Vendor Spending Analysis

Potential tool:

```text
get_vendor_totals
```

Questions:

```text
Which vendors cost us the most?
```

```text
How much did we spend with Microsoft?
```

### Definition of Done

* [x] vendor totals use SQL aggregation
* [x] top-N supported where appropriate
* [x] date range supported
* [x] tests pass — 122 passed

---

## Milestone 2.3 — Revenue Analysis

Support:

* total revenue
* revenue by period
* date ranges
* monthly revenue

Questions:

```text
How much revenue did we make in August?
```

```text
Show monthly revenue.
```

### Definition of Done

* [x] `financial_transactions` is the accounting source of truth
* [x] revenue uses posted `SALE` transactions
* [x] total and period-based revenue are deterministic
* [x] named months and inclusive date ranges are supported
* [x] period SQL is selected from a closed allow-list
* [x] date values use Oracle bind parameters
* [x] AI tool registry/schema integration is complete
* [x] Demo Mode routes through generic `_execute_tool()`
* [x] empty-result behavior is deterministic
* [x] tests pass — 132 passed

---

## Milestone 2.4 — Expense Trends

Support:

* monthly expenses
* category trends
* vendor trends
* month-over-month changes

Do calculations deterministically.

AI should explain the results, not invent them.

### Definition of Done

* [x] `financial_transactions` is the accounting source of truth
* [x] expenses use posted `EXPENSE` and `BANK_FEE` transactions
* [x] existing expense sign semantics are preserved
* [x] monthly and yearly trend grouping is deterministic
* [x] category and vendor trend filters are supported
* [x] date/filter values use Oracle bind parameters
* [x] missing calendar months are represented as zero-value gaps before month-over-month comparison
* [x] first-period and zero-period behavior is deterministic
* [x] AI tool registry/schema integration is complete
* [x] Demo Mode routes through generic `_execute_tool()`
* [x] tests pass — 132 passed

---

## Milestone 2.5 — Financial Statistics

Implemented metrics:

* transaction count
* average posted expense
* largest posted expense
* posted vs pending counts
* categorized vs uncategorized counts

Median was deliberately not added because the current investigation workflow
does not justify the additional metric.

### Definition of Done

* [x] `financial_transactions` remains the accounting source of truth
* [x] transaction count is deterministic
* [x] average expense uses posted `EXPENSE` and `BANK_FEE` transactions with `ABS(amount)`
* [x] largest expense uses the same posted expense semantics
* [x] posted and pending counts are exposed
* [x] categorized and uncategorized counts are exposed
* [x] optional inclusive date filters use Oracle bind parameters
* [x] implementation is read-only
* [x] AI tool registry and strict schema integration are complete
* [x] Demo Mode routes through generic `_execute_tool()`
* [x] deterministic formatting is covered by tests
* [x] tests pass — 138 passed

### Phase 2 Status

**COMPLETE — verified baseline: 138 passed.**

---

# PHASE 3 — FINANCIAL INVESTIGATION

Goal:

Use the read-only tool layer to investigate accounting problems.

---

## Milestone 3.1 — Uncategorized Transaction Investigation

Implemented workflow:

```text
identify transaction
        ?
retrieve accounting context
        ?
inspect vendor/history
        ?
produce read-only recommendation
        ?
human decides
```

The implementation introduces the read-only
`investigate_uncategorized_transaction` AI tool.

The investigation result includes:

* transaction details
* any existing stored AI suggestion
* active accounting-category context
* confirmed historical examples
* a validated category recommendation
* recommendation confidence
* evidence-based rationale
* explicit human-review requirement

Stored AI suggestions are explicitly distinguished from approved accounting
truth.

### Definition of Done

* [x] one uncategorized transaction can be investigated by transaction ID
* [x] investigation uses `financial_transactions` as the transaction source
* [x] accounting context is retrieved through the existing RAG layer
* [x] confirmed vendor/description history is exposed as evidence
* [x] recommendations are validated against the active Chart of Accounts
* [x] stored AI suggestions remain distinct from investigation recommendations
* [x] categorized and missing-transaction behavior is deterministic
* [x] investigation performs no category approval or accounting write
* [x] no database commit occurs in the investigation path
* [x] AI tool registry and strict schema integration are complete
* [x] Demo Mode routes through generic `_execute_tool()`
* [x] final categorization remains human-controlled
* [x] tests pass — 146 passed

---

## Milestone 3.2 — Reconciliation Investigation

Implemented workflow:

```text
identify reconciliation issue
        ↓
retrieve bank transaction
        ↓
inspect linked candidate
        ↓
compare deterministic evidence
        ↓
explain uncertainty
        ↓
human decides
```

The implementation introduces the read-only
`investigate_reconciliation_issue` AI tool.

The investigation result includes:

* bank transaction details
* linked financial-transaction candidate where available
* stored match type
* stored match confidence
* absolute amount difference
* exact amount-match indicator
* date difference in days
* deterministic meaningful-token description overlap
* deterministic reconciliation assessment
* explicit human-review requirement

The existing bulk `get_reconciliation_review` tool remains responsible for
listing reconciliation issues. Specific bank-transaction drill-down routes
through `investigate_reconciliation_issue`.

The investigation path is deliberately separate from the existing write
functions that confirm, reject, or mark reconciliation items investigated.

### Definition of Done

* [x] one reconciliation issue can be investigated by bank transaction ID
* [x] bank and linked financial transaction evidence is retrieved read-only
* [x] Oracle bind parameters are used for the transaction lookup
* [x] amount difference and exact amount matching are deterministic
* [x] date difference is calculated where both dates are available
* [x] description overlap is calculated deterministically
* [x] possible-match confidence is exposed without treating it as truth
* [x] `POSSIBLE_MATCH`, `NO_MATCH`, matched, and missing-item behavior is deterministic
* [x] specific investigation requests use a dedicated AI tool
* [x] bulk reconciliation review remains on `get_reconciliation_review`
* [x] AI tool registry and strict schema integration are complete
* [x] Demo Mode routes through generic `_execute_tool()`
* [x] investigation performs no reconciliation `UPDATE`, `INSERT`, or `DELETE`
* [x] investigation performs no database commit
* [x] possible matches remain human-reviewable
* [x] tests pass — 154 passed

---

## Milestone 3.3 — Deterministic Anomaly Detection

Implemented deterministic read-only anomaly detection through:

```text
get_financial_anomalies
```

The first anomaly set includes:

* unusually large posted expenses
* exact duplicate-looking transactions
* repeated bank-fee signatures

Large-expense detection uses an explicit deterministic baseline:

* only posted `EXPENSE` and `BANK_FEE` transactions
* absolute transaction amounts
* minimum baseline size of 3 transactions
* threshold = max(EUR 100, 1.5 x average posted expense)

Duplicate-looking transactions require the same:

* transaction date
* transaction type
* absolute amount
* normalized description
* normalized vendor

Repeated bank fees group matching:

* absolute amount
* normalized description
* normalized vendor

Every anomaly includes:

* anomaly type
* severity
* affected transaction IDs
* deterministic reason
* supporting evidence
* explicit human-review requirement

Anomaly signals are investigation aids, not confirmed accounting errors.

The implementation is fully read-only:

* no `UPDATE`
* no `INSERT`
* no `DELETE`
* no database commit
* no categorization or reconciliation action

Assistant Demo Mode routes anomaly questions through the generic
`_execute_tool()` boundary.

### Definition of Done

* [x] deterministic anomaly detection is implemented
* [x] unusually large expenses are detected with an explicit threshold
* [x] duplicate-looking transactions are detected deterministically
* [x] repeated bank-fee signatures are detected deterministically
* [x] every anomaly includes a reason and supporting evidence
* [x] anomaly results remain investigation signals rather than accounting truth
* [x] all anomaly detection is read-only
* [x] no accounting state is modified
* [x] strict AI tool schema integration is complete
* [x] Demo Mode routing and formatting are deterministic
* [x] generic `_execute_tool()` remains the execution boundary
* [x] tests pass — 161 passed

---

# PHASE 4 — AI ASSISTANT FRONTEND COMPLETION

Before editing this phase, inspect the current `frontend/src/App.tsx`.

Some AI Assistant scaffolding may already exist.

---

## Milestone 4.1 — Core Assistant Interaction

Completed and hardened the existing Assistant frontend rather than rebuilding it.

The frontend now provides:

* question input
* submit by button
* submit by Enter
* duplicate-submit protection while a request is active
* visible loading state
* disabled input and button while loading
* dedicated Assistant error state
* readable HTTP/API errors
* response contract validation
* multiline response rendering
* recovery after backend/network failure

The frontend continues to call:

```text
POST /bookkeeping/ai-assistant
```

with:

```json
{
  "question": "..."
}
```

and renders the backend `message` response.

Manual verification covered:

* bookkeeping summary
* AI categorization review
* deterministic anomaly investigation
* reconciliation investigation
* backend unavailable/error recovery

### Definition of Done

* [x] endpoint works from frontend
* [x] loading state works
* [x] errors are readable
* [x] response display works
* [x] duplicate submit is prevented while loading
* [x] multiline responses remain readable
* [x] no TypeScript errors
* [x] frontend lint passes with 0 warnings and 0 errors
* [x] production build passes

---

## Milestone 4.2 — Structured Tool Results

Where appropriate, render financial results as UI structures rather than raw JSON.

Example transaction columns:

* date
* description
* vendor
* amount
* category
* status
* reconciliation status

---

## Milestone 4.3 — Suggested Questions

Add useful examples such as:

```text
What's our bookkeeping summary?
```

```text
Which transactions need AI review?
```

```text
Show reconciliation issues.
```

```text
Show Software expenses over €50.
```

---

## Milestone 4.4 — Tool Transparency

Optionally expose:

* tool used
* filters applied
* number of results

This is valuable for portfolio explainability.

Do not expose internal chain-of-thought reasoning.

---

## Milestone 4.5 — Session Conversation History

Add local/session conversation history.

Persistent database-backed chat history is not required initially.

---

# PHASE 5 — RAG IMPROVEMENTS

---

## Milestone 5.1 — Better Historical Retrieval

Improve deterministic retrieval through:

* normalized vendor names
* normalized descriptions
* keywords
* exact vendor history
* category frequency

Avoid premature embedding complexity.

---

## Milestone 5.2 — Accounting Policy Knowledge

Add a small internal accounting policy knowledge source.

Potential content:

* category definitions
* vendor-specific rules
* approval policies
* bookkeeping conventions

---

## Milestone 5.3 — Source-Aware Recommendations

AI categorization/investigation should be able to indicate the evidence type used.

Examples:

```text
historical approved transaction
accounting category definition
company policy
vendor history
```

Do not fabricate sources.

---

## Milestone 5.4 — Optional Semantic Retrieval

Evaluate embeddings only if deterministic retrieval is insufficient.

If embeddings are introduced:

* keep an offline/mock development path
* document cost implications
* test retrieval separately from paid model calls

---

# PHASE 6 — AI CATEGORIZATION QUALITY

---

## Milestone 6.1 — Vendor-Aware Categorization

Use approved vendor history.

---

## Milestone 6.2 — Description-Aware Categorization

Use normalized descriptions and historical patterns.

---

## Milestone 6.3 — Human Feedback Loop

Approved/corrected categories become future trusted examples.

Rejected suggestions do not.

---

## Milestone 6.4 — Categorization Metrics

Potential dashboard metrics:

* suggestion coverage
* approval rate
* rejection rate
* correction rate
* average confidence
* categories requiring most review

---

# PHASE 7 — READ-ONLY AGENTIC WORKFLOWS

Do not create write-capable agents first.

---

## Milestone 7.1 — Bookkeeping Investigation Agent

Example request:

```text
Investigate the bookkeeping issues that need attention.
```

Possible sequence:

```text
bookkeeping summary
        ↓
AI review queue
        ↓
reconciliation queue
        ↓
relevant transactions
        ↓
audit context
        ↓
findings
```

The agent should be able to use multiple read-only tools.

---

## Milestone 7.2 — Categorization Investigation Agent

For each selected transaction:

1. retrieve data
2. retrieve historical evidence
3. assess likely category
4. report confidence/evidence
5. recommend action

Do not finalize automatically.

---

## Milestone 7.3 — Reconciliation Investigation Agent

Agent may:

1. inspect unmatched items
2. retrieve candidate matches
3. compare evidence
4. rank candidates
5. explain recommendation

Human confirms final action.

---

# PHASE 8 — HUMAN-IN-THE-LOOP WRITE TOOLS

Only begin after Phase 7 is stable.

---

## Milestone 8.1 — Approval-Gated Categorization Tool

Potential AI-assisted write:

```text
propose category
    ↓
user approval
    ↓
execute existing category action
    ↓
audit
```

Do not allow silent categorization finalization.

---

## Milestone 8.2 — Approval-Gated Reconciliation Tool

Potential flow:

```text
AI recommends match
    ↓
user approval
    ↓
existing reconciliation action
    ↓
audit
```

---

## Milestone 8.3 — Write Tool Security Review

Before considering write agents complete:

* validate IDs
* validate enums
* validate state transitions
* prevent duplicate writes
* audit actions
* test rejection paths
* test unauthorized tool names
* test invalid arguments

---

# PHASE 9 — MCP

Only begin after internal tools are stable.

---

## Milestone 9.1 — MCP Architecture Documentation

Document:

* MCP server
* MCP client
* tools
* resources
* schemas

---

## Milestone 9.2 — Read-Only MCP Server

Expose selected safe capabilities.

Potential examples:

```text
bookkeeping summary
transaction search
AI review queue
reconciliation review
audit history
```

---

## Milestone 9.3 — MCP Client Demonstration

Verify:

* discovery
* schema inspection
* tool calls
* returned results
* error handling

---

## Milestone 9.4 — MCP Portfolio Explanation

Explain why MCP is useful relative to hard-coded tool integration.

---

# PHASE 10 — SECURITY AND RELIABILITY

---

## Milestone 10.1 — Validation Review

Review:

* transaction IDs
* bank transaction IDs
* dates
* amounts
* statuses
* categories
* reconciliation states
* AI tool arguments

---

## Milestone 10.2 — Database Transaction Review

Audit:

* commits
* rollbacks
* error paths
* connection cleanup
* write atomicity

---

## Milestone 10.3 — API Error Consistency

Provide clean FastAPI errors without exposing unnecessary database internals.

---

## Milestone 10.4 — Logging

Introduce useful structured logging for:

* application errors
* AI tool calls
* important accounting writes
* reconciliation activity

Never log secrets.

---

## Milestone 10.5 — AI Tool Security Tests

Test:

* unknown tool rejected
* invalid arguments rejected
* malformed model output handled
* no arbitrary function execution
* write operations approval-gated

---

# PHASE 11 — TESTING MATURITY

Testing already exists throughout development.

This phase is a dedicated final quality pass.

## Milestone 11.1 — Test Suite Separation

Separate the current live-Oracle-heavy backend suite into clearly selected
test layers.

### Definition of Done

* [ ] fast unit and API tests can run without database credentials
* [ ] live Oracle integration tests are explicitly marked or isolated
* [ ] `python/test_database.py` performs no database work during pytest discovery
* [ ] local and CI test commands document which layer they execute
* [ ] Demo/OpenAI mock tests continue without paid API calls

Review coverage for:

* analytics
* bookkeeping
* reconciliation
* audit
* categorization
* RAG
* tool registry
* tool arguments
* Demo Assistant
* OpenAI mocked calls
* APIs
* frontend production build

Real OpenAI API calls must remain optional.

---

# PHASE 12 — DOCKERIZATION

---

## Milestone 12.1 — Backend Container

Dockerize FastAPI/Python.

---

## Milestone 12.2 — Frontend Production Container

Create production React build.

Optionally serve through nginx if appropriate.

---

## Milestone 12.3 — Environment Configuration

Document required variables.

Never bake secrets into container images.

---

## Milestone 12.4 — Oracle Strategy

Document the practical Oracle setup.

Do not containerize Oracle merely to claim everything is containerized if it makes the project significantly harder to reproduce.

---

# PHASE 13 — DEPLOYMENT READINESS

Prepare:

* production CORS
* API base URLs
* environment config
* health endpoint
* startup commands
* deployment documentation
* frontend production config

Deployment may be documented even if the Oracle database remains primarily local/demo infrastructure.

---

# PHASE 14 — DASHBOARD PORTFOLIO POLISH

Potential improvements:

* stronger KPI cards
* expense trends
* revenue trends
* category totals
* vendor totals
* reconciliation statistics
* AI categorization metrics
* anomaly alerts
* Assistant UX polish

Avoid decorative work before core functionality is stable.

---

# PHASE 15 — PORTFOLIO README

Create a strong root README containing:

## Project overview

What business problem is solved.

## Architecture

Example:

```text
React
  ↓
FastAPI
  ↓
Python business logic
  ↓
Oracle AI Database
```

AI:

```text
User question
    ↓
AI Assistant
    ↓
Tool selection
    ↓
TOOL_REGISTRY
    ↓
Financial tools / RAG
    ↓
Oracle
```

## Technologies

Include:

* Oracle AI Database 26ai
* SQL / PL/SQL
* Python
* FastAPI
* Pydantic
* pytest
* React
* TypeScript
* Vite
* OpenAI Responses API
* RAG
* function/tool calling
* MCP
* Docker where completed

## Screenshots

Potential screenshots:

* dashboard
* categorization review
* reconciliation review
* AI Assistant
* audit history

## AI safety design

Explain:

* Demo Mode
* optional OpenAI Mode
* approved history trust boundary
* human-in-the-loop
* allow-listed tools

## Setup instructions

Must be reproducible.

## Testing

Record the final current passing test baseline.

---

# PHASE 16 — ARCHITECTURE DOCUMENTATION

Document important decisions such as:

* Oracle choice
* database schema
* bookkeeping model
* reconciliation semantics
* audit architecture
* categorization confidence
* trusted vs untrusted AI data
* RAG architecture
* tool registry
* generic executor
* Demo vs OpenAI mode
* agent design
* MCP design

---

# PHASE 17 — FINAL REPOSITORY CLEANUP

Before declaring the project portfolio-ready:

* [ ] remove dead code
* [ ] remove duplicate functions
* [ ] remove debug prints
* [ ] clean imports
* [ ] verify `.env` ignored
* [ ] verify no secrets committed
* [ ] inspect Git status
* [ ] run all tests
* [ ] run frontend production build
* [ ] verify README commands
* [ ] review error messages
* [ ] review comments
* [ ] review API documentation
* [ ] verify screenshots
* [ ] verify architecture docs
* [ ] verify roadmap/status accuracy

---

# FINAL DEFINITION OF DONE

The project is portfolio-ready when:

* [ ] Oracle schema and setup are documented
* [ ] e-commerce data model works
* [ ] bookkeeping workflows work
* [ ] reconciliation workflow works
* [ ] audit trail works
* [ ] AI categorization works
* [ ] accounting RAG works
* [ ] natural-language financial querying is strong
* [x] dedicated financial analytics tools work
* [ ] AI Assistant backend works
* [ ] AI Assistant frontend is polished
* [ ] Demo Mode works with zero paid model usage
* [ ] optional real OpenAI mode works
* [ ] read-only agentic workflow is demonstrated
* [ ] important writes require human approval
* [ ] MCP integration is demonstrated
* [ ] security review is complete
* [ ] automated tests pass
* [ ] frontend production build passes
* [ ] Docker/deployment strategy is documented or implemented
* [ ] README is portfolio-quality
* [ ] architecture documentation exists
* [ ] repository contains no secrets
* [ ] repository is reproducible for another developer

---

# CURRENT NEXT ACTION

Start with:

```text
Phase 4
Milestone 4.2 — Structured Tool Results
```

Goal:

Render useful financial Assistant results as structured frontend UI where the
backend already provides enough structure, instead of relying only on a plain
text paragraph.

Before implementation:

1. inspect the current Assistant response schema returned by the backend
2. inspect whether tool name and structured result data already reach the API
3. avoid changing the generic `_execute_tool()` backend boundary unnecessarily
4. identify the smallest high-value result type for structured rendering
5. prefer reusable Assistant result components over adding more logic directly
   into the existing large `App.tsx`
6. preserve the plain-text Assistant message as a safe fallback
7. do not add accounting write actions to Assistant result cards
8. run frontend lint and production build before closing the milestone

Initial structured-result candidates:

* transaction lists
* AI review queue results
* anomaly investigation results
* financial statistics

Do not turn Milestone 4.2 into a full frontend redesign.
