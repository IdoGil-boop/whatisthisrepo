---
name: orchestrator
description: "Lists available custom agents and recommends when to use each."
tools:
  - Read
  - Glob
maxTurns: 5
---

# Agent Orchestrator

Overview of custom agents available in this repository. This orchestrator works alongside the **cc10x router** (`/cc10x:cc10x-router`) which handles BUILD/DEBUG/REVIEW/PLAN workflows.

## Available Agents

| Agent | File | When to Use |
|-------|------|-------------|
| **post-session-maintainer** | `.claude/agents/post-session-maintainer.md` | End of session, "wrap up", "do maintenance", `/maintain` |
| **doc-reviewer** | `.claude/agents/doc-reviewer.md` | Review documentation quality before maintenance |
| **doc-optimizer** | `.claude/agents/doc-optimizer.md` | Merge/consolidate docs (consumes doc-reviewer output) |
| **planner** | `.claude/agents/planner.md` | New features, complex changes, unclear requirements — waits for confirmation |
| **architect** | `.claude/agents/architect.md` | System design, scalability, schema changes, pipeline redesign |
| **python-reviewer** | `.claude/agents/python-reviewer.md` | Python code review: PEP 8, type hints, SQLAlchemy gotchas |
| **database-reviewer** | `.claude/agents/database-reviewer.md` | PostgreSQL schema/query/migration review, Alembic validation |
| **tdd-guide** | `.claude/agents/tdd-guide.md` | Test-driven development: RED-GREEN-REFACTOR, 80%+ coverage |
| **security-reviewer** | `.claude/agents/security-reviewer.md` | After writing auth, API, Celery, or Google Ads OAuth code |
| **refactor-cleaner** | `.claude/agents/refactor-cleaner.md` | Dead code cleanup, unused imports/deps, duplicate consolidation |
| **e2e-runner** | `.claude/agents/e2e-runner.md` | Create/maintain/run Playwright E2E tests for admin frontend |
| **code-reviewer** | `.claude/agents/code-reviewer.md` | Review any code change for quality, security, and patterns |

## Integration with cc10x

The cc10x router handles development workflows (BUILD/DEBUG/REVIEW/PLAN). Post-session maintenance is a **separate concern** that runs after development work is done:

- **cc10x** = development workflows (building, debugging, reviewing, planning)
- **post-session-maintainer** = repo hygiene after development (docs, skills, memory, recommendations)

The cc10x workflow-recommender skill can suggest promoting repeated cc10x patterns into new skills or agents.

## Hooks

| Hook | File | Fires On | Purpose |
|------|------|----------|---------|
| **Post-merge test runner** | `.claude/hooks/post-merge-test-runner.py` | PostToolUse (Bash) | Detects `git merge/pull/stash pop/rebase/cherry-pick` and reminds to run tests |
| **cc10x plugin update detector** | `.claude/hooks/cc10x_plugin_update_detector.py` | PostToolUse (Bash) | Detects cc10x plugin updates, warns if codex-review patch is missing |
| **Post-session maintenance** | `.claude/hooks/queue_post_session_maintenance.py` | SessionEnd | Queues `/maintain` reminder |

## Available Skills

See [`.claude/skills/INDEX.md`](../skills/INDEX.md) for all project-scoped skills, including **Stash Recovery** for safe git stash operations after merges and **Codex Review** for second-opinion code review via GPT-5.2/5.3-Codex on large or important changes.

## Quick Reference

- **Post-session maintenance:** `/maintain` or `claude --agent post-session-maintainer --continue "Run post-session maintenance"`
- **Review docs only:** `claude --agent doc-reviewer`
- **Development workflows:** `/cc10x:cc10x-router` (BUILD/DEBUG/REVIEW/PLAN)
- **See all skills:** Read `.claude/skills/INDEX.md`
- **Runbook:** See `docs/post-session-maintenance.md`
