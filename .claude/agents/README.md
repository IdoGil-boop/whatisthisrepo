# Claude Agents Registry

This directory contains definitions and documentation for Claude agents used in the project.

## Available Agents

### 1. Documentation Reviewer
**File**: `doc-reviewer.md`
**Purpose**: Reviews and classifies documentation for quality, clarity, and completeness
**Use for**:
- Pre-maintenance checks on documentation quality
- Identifying overlapping or redundant docs
- Flagging outdated or incomplete documentation
- Suggesting merge candidates

**Anti-inflation principle**: Flag merge candidates; prefer updating existing docs over creating new ones. Recommend consolidation, not proliferation.

### 2. Documentation Optimizer
**File**: `doc-optimizer.md`
**Purpose**: Consolidates, indexes, and optimizes documentation (consumes doc-reviewer output)
**Use for**:
- Merging overlapping documents
- Generating/updating documentation indexes
- Reducing verbose documentation
- Streamlining examples and explanations

**Anti-inflation principle**: Merge into existing docs; do not create new summary docs. Max one new doc per run.

### 3. Code Cleanup Agent
**File**: `code-cleanup.md` (if present)
**Purpose**: Removes dead code, consolidates utilities, enforces patterns
**Use for**:
- Removing unused functions/classes
- Consolidating duplicate utilities
- Enforcing single-source-of-truth principle
- Refactoring to canonical implementations

---

## When to Use Agents

### Documentation Maintenance
```bash
# Phase 1: Review documentation
/doc-reviewer

# Phase 2: Optimize and consolidate
/doc-optimizer
```

### Code Cleanup
```bash
/code-cleanup
```

---

## Creating New Agents

**Guidelines**:
1. Document purpose clearly
2. List use cases
3. Specify output format
4. Include safety guardrails
5. Add "Anti-inflation" or similar principles if applicable
6. Update this README with a new section

### 4. Post-Session Maintainer
**File**: `post-session-maintainer.md`
**Purpose**: Runs end-of-session maintenance (docs, skills, memory, workflow recommendations)
**Use for**:
- Wrapping up a session ("do maintenance", "wrap up")
- Keeping docs, skills, and memory coherent
- Getting recommendations for new automations

**Preloads skills**: docs-maintenance, skills-maintenance, memory-curation, workflow-recommender

### 5. Orchestrator
**File**: `orchestrator.md`
**Purpose**: Lists all available agents and recommends when to use each
**Use for**:
- Finding the right agent for a task
- Quick reference of all custom agents

### 6. Planner
**File**: `planner.md`
**Purpose**: Creates implementation plans, assesses risks, breaks down features into phases
**Use for**:
- New feature planning, complex refactoring, multi-file changes
- Waits for explicit user confirmation before any code is written

### 7. Architect
**File**: `architect.md`
**Purpose**: System design, scalability decisions, ADR documentation
**Use for**:
- Schema changes, pipeline redesign, new subsystems, architectural decisions

### 8. Python Reviewer
**File**: `python-reviewer.md`
**Purpose**: Python-specific code review (PEP 8, type hints, linting, ORM patterns)
**Use for**:
- After writing Python code; catches common ORM and language-specific gotchas

### 9. Database Reviewer
**File**: `database-reviewer.md`
**Purpose**: Database schema, query, and migration review
**Use for**:
- Migrations, new models, query performance, indexing decisions

### 10. TDD Guide
**File**: `tdd-guide.md`
**Purpose**: Enforces test-driven development (RED-GREEN-REFACTOR) with 80%+ coverage
**Use for**:
- New features, bug fixes, security-critical code

### 11. Security Reviewer
**File**: `security-reviewer.md`
**Purpose**: OWASP-based security analysis
**Use for**:
- After writing auth, API endpoints, tasks, or code handling sensitive data

### 12. Refactor Cleaner
**File**: `refactor-cleaner.md`
**Purpose**: Dead code cleanup using analysis tools; duplicate consolidation
**Use for**:
- Post-migration cleanup, removing competing logic, dependency cleanup

### 13. E2E Runner
**File**: `e2e-runner.md`
**Purpose**: Playwright E2E test creation, maintenance, and execution
**Use for**:
- Critical user flows, admin console testing, Page Object Model patterns

### 14. Code Reviewer
**File**: `code-reviewer.md`
**Purpose**: General code review for quality, security, and project-specific patterns
**Use for**:
- Review any code change; checks for common issues and project conventions

---

## Related Files

- `.claude/commands/` — Custom commands
- `.claude/skills/INDEX.md` — Skills registry
