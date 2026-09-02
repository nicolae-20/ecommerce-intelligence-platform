# AGENTS.md

# E-commerce Intelligence Platform — Codex Working Instructions

## 1. Purpose of This File

This file contains persistent instructions for coding agents working in this repository.

It defines:

* how to understand the project
* how to choose the next task
* how to modify the code safely
* which architectural rules must be preserved
* how testing must be performed
* how AI/accounting safety boundaries work
* how project status and roadmap documentation must be maintained

This file is not a project status report.

Current implementation state belongs in `PROJECT_STATUS.md`.

Future work belongs in `ROADMAP.md`.

Delegation and multi-agent workflow rules belong in `ORCHESTRATION.md`.

---

# 2. Project Mission

Build a portfolio-grade E-commerce Intelligence and AI Bookkeeping platform demonstrating practical software engineering across:

* Oracle AI Database 26ai Free
* SQL and PL/SQL
* Python
* FastAPI
* Pydantic
* React
* TypeScript
* Vite
* pytest
* bookkeeping workflows
* accounting categorization
* bank reconciliation
* auditability
* Retrieval-Augmented Generation
* AI tool calling
* AI assistants
* human-in-the-loop workflows
* agentic workflows
* Model Context Protocol
* Docker
* deployment readiness
* portfolio-quality documentation

The project should remain functional for development and demonstration without requiring paid OpenAI API calls.

---

# 3. Source-of-Truth Hierarchy

At the beginning of every new coding session, use the following hierarchy.

## 3.1 Permanent engineering rules

Read:

`AGENTS.md`

This file defines how work must be performed.

## 3.2 Current project state

Read:

`PROJECT_STATUS.md`

This file defines what is currently known to be implemented.

## 3.3 Future direction

Read:

`ROADMAP.md`

This file defines the planned order of future work.

## 3.4 Agent orchestration

Read:

`ORCHESTRATION.md`

This file defines role selection, delegation, ownership, quality gates, and
usage-efficiency rules.

## 3.5 Actual implementation

Inspect the repository.

The code and tests are authoritative when documentation and implementation disagree.

## 3.6 Git history

Use Git history when architectural intent or previous changes are unclear.

---

# 4. Mandatory Session Startup Protocol

Before implementing a roadmap task:

1. Read `AGENTS.md`.
2. Read the current `PROJECT_STATUS.md` sections relevant to the task.
3. Read the relevant section of `ROADMAP.md`.
4. Read `ORCHESTRATION.md`.
5. Inspect the files related to the current milestone.
6. Inspect existing tests covering that functionality.
7. Check `git status`.
8. Determine whether documentation still matches the implementation.
9. Do not begin unrelated roadmap work.
10. Make the smallest coherent change that advances the current milestone.
11. Run the relevant tests after implementation.

Do not rely only on roadmap descriptions.

Inspect the actual implementation first.

---

# 5. Development Environment

Primary development environment:

* Windows 11
* VS Code
* Python 3.10
* Oracle AI Database 26ai Free
* SQL Developer
* Node.js / npm
* Git
* GitHub

Project root:

```text
C:\Users\WINDOWS 10\ecommerce-intelligence-platform
```

Python virtual environment:

```text
python\.venv
```

Activate from the project root:

```cmd
python\.venv\Scripts\activate
```

Backend:

```cmd
uvicorn api.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Frontend development server:

```cmd
cd frontend
npm run dev
```

Typical frontend URL:

```text
http://localhost:5173
```

Frontend production build:

```cmd
cd frontend
npm run build
```

Backend test suite:

```cmd
pytest tests
```

---

# 6. Current Known Test Snapshot

At the current verified checkpoint:

```text
92 passed
```

This is a historical checkpoint, not a permanently hard-coded expected test count.

Future changes may legitimately increase the number of tests.

The important invariant is:

```text
0 failed
0 errors
```

unless a milestone explicitly introduces a temporary expected failure during implementation.

Do not modify tests merely to recover a particular numeric test count.

---

# 7. General Engineering Rules

## 7.1 Inspect before editing

Never assume the implementation matches documentation exactly.

Open and inspect relevant functions before modifying them.

## 7.2 Prefer incremental changes

Prefer:

* one coherent feature
* corresponding tests
* verification
* then the next feature

Avoid broad rewrites while implementing a small roadmap item.

## 7.3 Preserve working architecture

Do not redesign existing architecture unless:

* the current architecture blocks the milestone
* there is a demonstrated bug
* a refactor materially improves maintainability
* the roadmap explicitly requires the change

## 7.4 Avoid duplicated logic

Reuse shared mechanisms where they already exist.

Examples:

* generic AI tool execution
* shared analytics functions
* existing review workflows
* common API schemas

## 7.5 Maintain backwards compatibility

Preserve existing API contracts unless a milestone intentionally changes them.

If an API response must change:

1. inspect frontend usage
2. update schema
3. update backend
4. update tests
5. update frontend
6. verify the production build

---

# 8. Testing Rules

## Backend changes

Run:

```cmd
pytest tests
```

after a meaningful backend milestone.

For small iterative fixes, targeted tests may be used first, but the complete suite must pass before the milestone is considered complete.

## Frontend changes

After React or TypeScript changes:

```cmd
cd frontend
npm run build
```

The production build must succeed.

## Regression tests

When fixing a bug, add a regression test when practical.

## OpenAI tests

Automated tests must not require paid OpenAI API access.

Use mocks for real OpenAI Responses API behavior.

---

# 9. Database Rules

Use parameterized Oracle SQL.

Never construct SQL by directly interpolating user-controlled values.

Good:

```python
cursor.execute(
    """
    SELECT *
    FROM financial_transactions
    WHERE status = :status
    """,
    {"status": status},
)
```

Do not use string formatting to insert SQL parameters.

Database connections must be closed reliably.

Use existing connection helpers rather than creating unrelated connection logic.

Review transaction boundaries carefully for writes.

Use:

* commit when intended
* rollback when appropriate
* finally blocks for cleanup

Prefer database-side aggregation for financial analytics.

Do not retrieve an entire dataset into an AI model merely to calculate SQL-friendly totals.

---

# 10. Accounting Domain Invariants

These rules are critical.

## 10.1 Trusted accounting history

Finalized or human-approved accounting data may be treated as historical evidence.

## 10.2 Unapproved AI suggestions

Unapproved AI suggestions must NOT be treated as accounting truth.

The following invariant must remain true:

```text
approved/finalized accounting data
    =
trusted historical evidence

unapproved AI suggestions
    ≠
trusted accounting ground truth
```

## 10.3 Human-in-the-loop writes

Important accounting write operations should remain human-controlled.

Examples include:

* final category assignment
* category approval
* category rejection
* reconciliation confirmation
* reconciliation rejection

AI may:

* retrieve
* analyze
* recommend
* rank
* explain
* investigate

AI should not silently finalize important accounting changes.

---

# 11. Reconciliation Invariants

Current semantics must be preserved unless intentionally redesigned.

```text
EXACT_MATCH
    → strong match behavior

POSSIBLE_MATCH
    → human review

NO_MATCH
    → investigation
```

Do not automatically convert ambiguous possible matches into finalized reconciliation matches.

---

# 12. Auditability Rules

Important human or automated accounting actions should remain auditable.

Existing audit concepts include actions such as:

* CATEGORY_APPROVED
* CATEGORY_REJECTED
* RECONCILIATION_CONFIRMED
* RECONCILIATION_REJECTED
* TRANSACTION_INVESTIGATED
* REJECTION_CANCELLED

When adding new accounting write workflows, evaluate whether an audit event should also be created.

---

# 13. AI Development Rules

## 13.1 Demo Mode first

The application supports AI development without paid external calls.

Default development should use Demo/Mock Mode.

Do not make real paid OpenAI API calls unless explicitly requested.

## 13.2 Demo Mode purpose

Demo Mode should be:

* deterministic
* understandable
* inexpensive
* testable

Do not attempt to turn the deterministic parser into a full natural-language model.

It exists to demonstrate the architecture without requiring external API spend.

## 13.3 OpenAI Mode

OpenAI Mode should use the same application tool layer as Demo Mode.

Conceptually:

```text
OpenAI model
    ↓
validated function/tool call
    ↓
_execute_tool(...)
    ↓
TOOL_REGISTRY
    ↓
local Python / Oracle
```

Do not create an alternate business-logic path specifically for OpenAI.

## 13.4 Tool allow-list

Only functions registered in `TOOL_REGISTRY` may be executed by the AI tool layer.

Unknown tools must be rejected.

Never dynamically execute arbitrary Python functions based solely on model output.

## 13.5 Tool arguments

Arguments must be validated or constrained.

Prefer explicit typed arguments.

Future write-capable tools require stricter validation and approval boundaries than read-only tools.

---

# 14. AI Tool Implementation Protocol

Before adding a new AI tool, determine whether an existing tool can be extended safely.

When a new tool is justified:

1. implement the Python function
2. use existing database/business helpers where appropriate
3. add the function to `TOOL_REGISTRY`
4. add its function schema to `TOOL_DEFINITIONS`
5. ensure `_execute_tool()` can invoke it
6. add deterministic Demo Mode support if required
7. add output formatting if required
8. add tests
9. verify existing multi-tool behavior
10. run the full test suite

Do not bypass `_execute_tool()`.

---

# 15. Current AI Architecture

High-level application:

```text
React / TypeScript
        ↓
FastAPI
        ↓
Python analytics and business logic
        ↓
Oracle AI Database
```

AI architecture:

```text
Demo Assistant ───────┐
                      │
                      ↓
                 _execute_tool()
                      ↓
                 TOOL_REGISTRY
                      ↓
               Python / Oracle
                      ↑
                      │
OpenAI Assistant ─────┘
```

RAG architecture:

```text
Oracle accounting categories
           +
approved historical examples
           ↓
AccountingContext
           ↓
AI categorization context
```

---

# 16. Current AI Tool Registry

At this checkpoint, expected tool names include:

```text
get_bookkeeping_summary
get_ai_review_queue
get_reconciliation_review
get_audit_log
get_transactions_by_date
get_transactions
```

Verify the actual registry before relying on this list.

---

# 17. RAG Rules

Accounting RAG may use:

* active accounting categories
* approved/finalized historical categories
* historical transaction descriptions
* historical vendors
* future approved company accounting policies

Do not use rejected or unapproved AI categorization output as historical truth.

When improving retrieval, deterministic methods are preferred before introducing paid embeddings unless embeddings provide clear value.

---

# 18. Security Rules

Never commit:

* `.env`
* OpenAI API keys
* database passwords
* tokens
* credentials
* secrets

Before commits involving configuration changes, inspect:

```cmd
git status
```

If uncertain, inspect staged files before committing.

Do not log secrets.

Do not expose secrets through FastAPI responses.

---

# 19. Git Working Protocol

Before substantial work:

```cmd
git status
```

After a completed milestone:

```cmd
git status
git add <relevant files>
git commit -m "<meaningful milestone description>"
git push
```

Do not blindly stage secrets or unrelated files.

Prefer milestone-based commits.

---

# 20. Roadmap Discipline

Normally work on the first incomplete milestone in `ROADMAP.md`.

Do not jump directly to:

* write-capable agents
* MCP
* Docker
* deployment

while foundational financial querying or read-only agent functionality remains incomplete, unless explicitly requested.

A milestone is complete only when:

* implementation is complete
* new behavior is tested
* regression tests pass
* frontend builds if affected
* documentation is updated when appropriate

---

# 21. Documentation Maintenance

## PROJECT_STATUS.md

Update after meaningful milestones.

Record:

* what was implemented
* files affected
* architecture changes
* new endpoints/tools
* new tests
* latest passing test count
* known limitations
* immediate next task

Do not turn it into a long chronological diary.

It should describe the current state.

## ROADMAP.md

Mark milestone items complete only after verification.

Do not mark future plans as implemented.

If the architecture changes materially, update future roadmap assumptions.

---

# 22. How to Resolve Documentation Conflicts

If documentation says something exists but the code does not:

1. inspect tests
2. inspect Git history if useful
3. trust current code/tests
4. correct the documentation

Do not implement functionality merely to make stale documentation appear correct unless it is still part of the roadmap.

---

# 23. Portfolio Quality Standard

Code should demonstrate professional engineering practices.

Prefer:

* meaningful function names
* readable SQL
* typed interfaces
* explicit business rules
* clean FastAPI schemas
* predictable frontend state
* strong tests
* transparent AI architecture

Avoid:

* unexplained magic values
* unnecessary abstractions
* hidden AI side effects
* giant functions
* arbitrary architecture rewrites
* fake functionality used only for screenshots

---

# 24. Definition of a Completed Coding Session

Before ending a milestone session:

1. implementation is saved
2. relevant tests pass
3. full test suite passes when appropriate
4. frontend build passes if frontend changed
5. `git status` is understood
6. `PROJECT_STATUS.md` is updated if the milestone changed project state
7. `ROADMAP.md` is updated if a milestone was completed
8. unresolved issues are explicitly documented
9. the next roadmap step is clear

---

# 25. Instruction to Codex

When asked simply to continue the project:

1. read `AGENTS.md`
2. read the current `PROJECT_STATUS.md` sections relevant to the next milestone
3. read only the relevant `ROADMAP.md` milestone
4. read `ORCHESTRATION.md`
5. inspect the relevant implementation and tests
6. identify the first incomplete milestone
7. implement only that milestone
8. run the appropriate quality gates
9. fix regressions
10. update project status and roadmap only after verification
11. explain what changed and what should happen next

Do not ask the user to manually copy code when direct repository editing is available.

Do not make paid OpenAI API calls unless explicitly instructed.
