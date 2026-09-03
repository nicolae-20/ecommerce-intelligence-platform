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

---

## Milestone 2.4 — Expense Trends

Support:

* monthly expenses
* category trends
* vendor trends
* month-over-month changes

Do calculations deterministically.

AI should explain the results, not invent them.

---

## Milestone 2.5 — Financial Statistics

Potential metrics:

* transaction count
* average expense
* largest expense
* median where useful
* posted vs pending
* categorized vs uncategorized

Only add metrics that improve the project.

---

# PHASE 3 — FINANCIAL INVESTIGATION

Goal:

Use the read-only tool layer to investigate accounting problems.

---

## Milestone 3.1 — Uncategorized Transaction Investigation

Workflow:

```text
find uncategorized transaction
        ↓
retrieve accounting context
        ↓
inspect vendor/history
        ↓
produce recommendation
        ↓
human decides
```

No automatic final write.

---

## Milestone 3.2 — Reconciliation Investigation

Questions:

```text
Why is this transaction unmatched?
```

```text
Which reconciliation issues need attention?
```

Agent/tooling may compare:

* amounts
* dates
* descriptions
* vendors
* possible matches
* confidence

Do not silently finalize reconciliation.

---

## Milestone 3.3 — Deterministic Anomaly Detection

Start with deterministic analytics.

Potential anomalies:

* unusually large expenses
* duplicate-looking transactions
* repeated fees
* new/unexpected vendors
* category spending spikes
* suspicious amount patterns

Expose results through read-only AI tools.

---

# PHASE 4 — AI ASSISTANT FRONTEND COMPLETION

Before editing this phase, inspect the current `frontend/src/App.tsx`.

Some AI Assistant scaffolding may already exist.

---

## Milestone 4.1 — Core Assistant Interaction

Complete:

* question input
* submit
* loading
* error handling
* response display

### Definition of Done

* [ ] endpoint works from frontend
* [ ] loading state works
* [ ] errors are readable
* [ ] no TypeScript errors
* [ ] production build passes

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
* [ ] dedicated financial analytics tools work
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
Phase 2
Milestone 2.3 — Revenue Analysis
```

Before implementation:

1. inspect the existing revenue and AI tool architecture
2. inspect `python/ai_tools.py` and `python/ai_assistant.py`
3. inspect relevant tests in `tests/test_analytics.py`
4. verify revenue source, sign, status, and period semantics
5. run or confirm the current test baseline
6. implement revenue analytics incrementally

Do not continue automatically into several later milestones in one large change unless explicitly requested.

Complete and test one milestone at a time.
