# Skills Index

All project-scoped Claude Code skills.

| Skill | Path | Purpose |
|-------|------|---------|
| [Docs Maintenance](docs-maintenance/SKILL.md) | `.claude/skills/docs-maintenance/` | Update docs to match code changes made this session |
| [Skills Maintenance](skills-maintenance/SKILL.md) | `.claude/skills/skills-maintenance/` | Evolve skills based on new patterns discovered this session |
| [Memory Curation](memory-curation/SKILL.md) | `.claude/skills/memory-curation/` | Capture session decisions, conventions, gotchas into project docs |
| [Workflow Recommender](workflow-recommender/SKILL.md) | `.claude/skills/workflow-recommender/` | Recommend automations based on session friction |
| [Hooks Authoring](hooks-authoring/SKILL.md) | `.claude/skills/hooks-authoring/` | Correct format, common patterns, and gotchas for `.claude/settings.json` hooks |
| [Stash Recovery](stash-recovery/SKILL.md) | `.claude/skills/stash-recovery/` | Safely recover git stashes that predate merges; avoid deleting merge-added files |
| [Codex Review](codex-review/SKILL.md) | `.claude/skills/codex-review/` | Second-opinion code review via external model for large/important changes |
| [cc10x Codex Patch](cc10x-codex-patch/SKILL.md) | `.claude/skills/cc10x-codex-patch/` | Re-apply codex-review integration into cc10x-router after plugin updates |
| [Security Review](security-review/SKILL.md) | `.claude/skills/security-review/` | Security checklist for Python/SQLAlchemy/Celery (OWASP, JSONB safety, serializer) |
| [Coding Standards](coding-standards/SKILL.md) | `.claude/skills/coding-standards/` | Python coding standards: PEP 8, type hints, ORM conventions, linters |
| [Backend Patterns](backend-patterns/SKILL.md) | `.claude/skills/backend-patterns/` | SQLAlchemy ORM, Celery tasks, Alembic migrations, session management, pipeline patterns |
| [Frontend Patterns](frontend-patterns/SKILL.md) | `.claude/skills/frontend-patterns/` | React/Next.js patterns: TanStack Query, Playwright E2E, POM |
| [Python Patterns](python-patterns/SKILL.md) | `.claude/skills/python-patterns/` | Pythonic idioms, PEP 8 standards, type hints, decorators, concurrency |
| [Python Testing](python-testing/SKILL.md) | `.claude/skills/python-testing/` | pytest, fixtures, mocking, parametrization, async testing, TDD |
| [PostgreSQL Patterns](postgres-patterns/SKILL.md) | `.claude/skills/postgres-patterns/` | Indexes, data types, RLS, UPSERT, pagination, query optimization |
| [TDD Workflow](tdd-workflow/SKILL.md) | `.claude/skills/tdd-workflow/` | RED-GREEN-REFACTOR methodology, unit/integration/E2E test patterns |
| [Instinct Learning](instinct-learning/SKILL.md) | `.claude/skills/instinct-learning/` | Instinct-based learning: atomic observations, confidence scoring, evolution |
| [Iterative Retrieval](iterative-retrieval/SKILL.md) | `.claude/skills/iterative-retrieval/` | Progressive context refinement for sub-agent and multi-step workflows |
| [Commit by Feature](commit-by-feature/SKILL.md) | `.claude/skills/commit-by-feature/` | Group large unstaged batches into logical commits by domain, with conventional commit messages |
| [Verify Plan](verify-plan/SKILL.md) | `.claude/skills/verify-plan/` | Cross-check a plan document against actual code after a multi-agent session; produce pass/fail assessment per item |
| [PR Review](pr-review/SKILL.md) | `.claude/skills/pr-review/` | Fetch automated PR review comments, triage by severity (P1/P2), fix all issues, and commit in one clean batch |
| [Ownership Test Scaffold](ownership-test-scaffold/SKILL.md) | `.claude/skills/ownership-test-scaffold/` | Scaffold standard TDD ownership test cases for any JWT-authenticated endpoint |

## Adding a New Skill

1. Create `.claude/skills/<skill-name>/SKILL.md`
2. Follow the template in [Skills Maintenance](skills-maintenance/SKILL.md)
3. Add an entry to this table
4. Reference from `.claude/agents/README.md` if used by an agent
