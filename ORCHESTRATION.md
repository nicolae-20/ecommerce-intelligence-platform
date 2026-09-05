# ORCHESTRATION.md

# E-commerce Intelligence Platform — Development-Agent Orchestration

## 1. Purpose and Default

This file defines how development agents are selected, delegated, coordinated,
and reviewed in this repository.

Apply Lean Orchestration:

* use one Lead / Orchestrator agent by default
* delegate only when it is materially useful
* use the minimum number of agents needed
* do not add a reviewer automatically
* do not introduce parallel work automatically

Roles in this document are capabilities the Lead may invoke when useful, not a
standing requirement to spawn several agents.

The Lead remains accountable for scope, integration, verification,
documentation, and the final report even when work is delegated.

---

## 2. Default Workflow

For an ordinary milestone:

```text
Developer
    → Lead
    → one implementation owner
    → targeted tests during iteration
    → independent review only when justified
    → Lead resolves findings
    → final quality gate
    → documentation update
    → developer report
```

Tiny mechanical or documentation-only changes normally remain with the Lead
and do not require an independent reviewer.

---

## 3. Available Roles

### 3.1 Lead / Orchestrator

The Lead is responsible for:

* identifying the current roadmap milestone
* reading only the relevant project state and roadmap sections
* inspecting only the implementation and tests needed for the task
* defining scope and acceptance criteria
* deciding whether delegation materially helps
* assigning one owner per implementation area
* integrating delegated results
* enforcing the appropriate quality gates
* resolving review findings
* updating project documentation after verification
* reporting the integrated result to the developer

### 3.2 Backend / Database Specialist

Primary areas:

* `python/`
* `api/`
* Oracle SQL and PL/SQL
* FastAPI and Pydantic
* database transactions

This specialist must preserve:

* parameterized SQL and bind variables
* reliable connection and transaction cleanup
* existing accounting and reconciliation semantics
* existing API contracts unless a change is intentional and coordinated

### 3.3 Frontend Specialist

Primary areas:

* `frontend/`
* React
* TypeScript
* Vite
* API integration

This specialist must preserve backend contracts, maintain TypeScript
correctness, and run the production build when frontend code changes.

### 3.4 AI / RAG Specialist

Primary areas:

* `python/ai_assistant.py`
* `python/ai_tools.py`
* `python/accounting_rag.py`
* `python/llm_categorizer.py`

This specialist must preserve:

* the `TOOL_REGISTRY` allow-list
* the generic `_execute_tool()` boundary
* deterministic Demo Mode
* mocked OpenAI tests
* development without required paid OpenAI calls
* the finalized-accounting trust boundary
* human approval for important accounting writes

### 3.5 Independent Test / Reviewer

This is a review-oriented role by default.

Responsibilities:

* inspect the implementation diff and acceptance criteria
* identify concrete regressions and missing edge cases
* verify relevant tests and architectural invariants
* distinguish defects from optional style preferences

The reviewer should report actionable defects. It should not rewrite an
implementation merely because another style is possible.

### 3.6 Security Reviewer

Use this role only when the task materially involves:

* credentials or secret handling
* SQL injection risk
* AI tool argument validation
* write permissions or approval boundaries
* destructive operations
* deployment or security review

---

## 4. Delegation Rules

Delegate only when at least one of these is true:

* workstreams are genuinely independent
* specialized expertise materially improves confidence
* independent review materially reduces regression risk
* frontend and backend work can be separated behind a stable contract
* investigation can be safely parallelized

Do not delegate simple mechanical changes. Do not automatically use multiple
reviewers.

The Lead should state the delegated scope, expected output, file ownership, and
acceptance criteria. Delegation does not transfer final responsibility away
from the Lead.

---

## 5. Ownership and Worktrees

Only one implementation agent may modify a given file or logical implementation
area at a time.

Do not assign multiple agents to edit the same core file concurrently. In
particular, do not have several agents independently redesign
`python/ai_assistant.py` or the same API contract.

Parallel implementation is appropriate only for clearly independent areas or
intentionally isolated worktrees.

Use isolated worktrees only when parallel implementation is genuinely useful,
such as:

* a stable backend API contract and a separate frontend implementation
* an unrelated analytics tool and independent frontend work

Do not create worktrees merely to make a small sequential task appear parallel.

---

## 6. Quality Gates

### 6.1 Backend milestone

During iteration, run targeted tests that diagnose the current change.

At milestone completion, run:

```cmd
pytest tests
```

The current verified baseline is recorded in `PROJECT_STATUS.md` and
`ROADMAP.md`. Future milestones may increase this count. Success means zero
failures and zero errors, not preserving a historical test count.

### 6.2 Frontend milestone

Run relevant checks and then:

```cmd
cd frontend
npm run build
```

Do not run the frontend production build when frontend code was untouched.

### 6.3 Cross-stack milestone

Require:

* backend regression tests
* frontend production build
* explicit API contract verification

### 6.4 AI milestone

Require:

* deterministic Demo Mode remains functional
* mocked OpenAI behavior passes
* no real paid OpenAI API call is required
* all tool execution remains allow-listed through `_execute_tool()`

For bounded read-only multi-tool composition, also require:

* a fixed allow-list and fixed execution plan
* every source execution through `_execute_tool()`
* no recursive Assistant or prior-phase runner orchestration
* no model-selected expansion of tool count
* explicit per-source provenance and detail level
* bounded drill-down count with no queue-wide drill-down loop

### 6.5 Database milestone

Require:

* bind parameters or parameterized SQL
* deliberate commit, rollback, and cleanup behavior
* review of accounting and reconciliation semantics
* no accidental coupling between categorization and reconciliation

---

## 7. Usage-Efficiency Rules

Codex usage is finite. Apply these rules permanently:

* use one agent by default
* use the minimum number of specialists necessary
* use High reasoning for meaningful coding tasks
* use Medium reasoning for mechanical edits and routine documentation
* reserve Extra High for difficult architecture, debugging, security, RAG,
  agents, or complex cross-stack work
* reserve Ultra for rare repository-wide audits or exceptional problems
* do not reread the entire repository for every milestone
* read only relevant `PROJECT_STATUS.md` and `ROADMAP.md` sections
* inspect only files needed for the current task
* prefer targeted tests during iteration
* run the full backend regression suite once at milestone completion
* do not repeatedly rerun expensive full suites when targeted tests can
  diagnose an intermediate failure
* do not run frontend gates when frontend code was untouched
* avoid repeated repository-wide security or architecture audits without a
  concrete reason
* keep command output concise when practical
* do not delegate simple mechanical work
* do not automatically use multiple reviewers

---

## 8. Human Approval Gates

Explicit developer approval is required before:

* destructive database or schema changes
* major architectural migrations
* autonomous accounting writes
* disabling important accounting safeguards
* real paid OpenAI API calls
* secret or credential operations
* Git history rewriting
* unrestricted force pushes
* deletion of major project components

When an approval boundary is reached, the Lead must stop and request approval.

---

## 9. Accounting and AI Invariants

Every role must preserve these rules:

* finalized or approved accounting history is trusted evidence
* unapproved AI suggestions are not trusted accounting truth
* possible reconciliation matches remain human-reviewable
* important accounting writes remain human-controlled
* AI tools remain explicitly allow-listed
* `_execute_tool()` remains the generic tool-execution boundary

---

## 10. Current Test-Architecture Limitation

The backend regression suite is heavily dependent on the live Oracle database.
Also, `python/test_database.py` performs live database work during pytest
discovery.

Do not solve that issue incidentally inside an unrelated milestone. Future test
hygiene should separate:

* fast credential-free tests
* live Oracle integration tests
* explicit smoke tests

Until that work is completed, `pytest tests` is the defined automated backend
regression command. Credentials and `.env` files must remain outside tracked
source and must never be exposed through agent output.

---

## 11. Documentation Ownership

Keep these responsibilities separate:

* `AGENTS.md` — permanent engineering rules and project map
* `PROJECT_STATUS.md` — current verified implementation state
* `ROADMAP.md` — future milestones and completion state
* `ORCHESTRATION.md` — roles, delegation, ownership, quality gates, approval
  gates, and usage-efficiency rules

Avoid copying large sections between these documents.

---

## 12. Session Startup When Asked to Continue

When the developer says "continue the project":

1. Read `AGENTS.md`.
2. Read the current `PROJECT_STATUS.md` sections relevant to the next milestone.
3. Read only the relevant `ROADMAP.md` milestone.
4. Read `ORCHESTRATION.md`.
5. Inspect the relevant code and tests.
6. Select the minimum orchestration needed.
7. Implement only the current milestone.
8. Run the appropriate quality gates.
9. Update status and roadmap only after verification.
10. Report the result and identify the next milestone.

The Lead should not expand scope merely because additional roles are available.
