---
name: pr-review
description: Fetch automated PR review comments, triage by severity, fix all issues, and commit. Use when a PR has review comments from automated bots (cursor BugBot, chatgpt-codex-connector, etc.) that need to be resolved.
---

# PR Review Fix

Pulls all PR review comments, triages by severity, applies fixes across all affected files, and commits in one clean batch.

## When to Use

- Automated reviewer bots (cursor BugBot, chatgpt-codex-connector) have commented on a PR
- Manual code reviewer left inline comments to address
- `/review-pr` output needs to be acted on as a batch
- PR has been through multiple fix rounds — fetch all comments and cross-check each against current file state to produce a "fixed / still open" audit before touching code

## Workflow

### Step 0 — Sync Tracker

Read `.claude/pr-review-log.md` (create if missing). For each PR entry, check if it is still open:

```bash
gh pr view <number> --json state --jq '.state'
# "OPEN" → keep  |  "MERGED" / "CLOSED" → delete that section from the log
```

Remove all sections whose PR is no longer open. Save the pruned file before proceeding.

---

### Step 1 — Fetch All Comments

```bash
# Fetch all inline code review comments
gh api repos/<owner>/<repo>/pulls/<number>/comments \
  | python3 -c "
import sys, json
comments = json.load(sys.stdin)
for c in comments:
    print(f'FILE: {c[\"path\"]}')
    print(f'LINE: {c.get(\"line\", \"?\")}')
    print(f'BODY: {c[\"body\"][:300]}')
    print('---')
"

# Also fetch PR-level review summaries
gh pr view <number> --repo <owner>/<repo>
```

### Step 2 — Triage by Severity

Group comments into a task list before touching any code:

| Severity | Criteria | Fix order |
|----------|----------|-----------|
| **P1 (Fix immediately)** | Security (IDOR, injection, auth bypass), deploy blockers (migration crash), data corruption | First |
| **P2 (Fix this session)** | Incorrect behavior, wrong defaults, silent data loss, API contract mismatches | Second |
| **P3 (Consider)** | Performance, style, naming, non-critical UX | Only if time allows |

Create a task list with `TaskCreate` for each issue before starting fixes.

### Step 3 — Read All Affected Files First

Before editing anything, read every file mentioned in comments:

```
Read all affected files in parallel:
- backend/app/routes/recommendations.py
- backend/app/routes/metrics.py
- backend/alembic/versions/<migration>.py
- frontend/app/(dashboard)/performance/page.tsx
```

### Step 4 — Fix All Issues

Fix P1 issues first, then P2. Key patterns that commonly appear:

**IDOR / Missing ownership check:**
```python
# Add to list queries
where = [Model.user_id == current_user.id]

# Add to get/mutate after fetch
if record.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")
```

**Alembic NOT NULL without server_default:**
```python
# BAD — crashes on non-empty DB
op.add_column('users', sa.Column('field', sa.Boolean(), nullable=False))

# GOOD
op.add_column('users', sa.Column('field', sa.Boolean(), nullable=False, server_default=sa.false()))
```

**Alembic None constraint names in downgrade:**
```python
# BAD — TypeError at runtime
op.drop_constraint(None, 'table', type_='unique')

# GOOD — name matches what upgrade() created
op.create_unique_constraint('uq_table_field', 'table', ['field'])
op.drop_constraint('uq_table_field', 'table', type_='unique')
```

**FastAPI POST bare params (treated as query params):**
```python
# BAD — JSON body silently ignored
async def endpoint(id: str, reason: Optional[str] = None):

# GOOD — Pydantic body
class RequestBody(BaseModel):
    reason: Optional[str] = None

async def endpoint(id: str, body: RequestBody):
```

**Frontend metric/enum mismatch:**
```typescript
// Remove values the backend validator doesn't accept
const METRICS = [
  { value: "clicks", label: "Clicks" },
  // { value: "cpa", label: "CPA" },  // backend returns 400
];
```

### Step 5 — Validate Syntax

```bash
python3 -c "import ast; ast.parse(open('backend/app/routes/foo.py').read()); print('OK')"
cd frontend && npx tsc --noEmit
```

### Step 6 — Commit

Stage only the changed files (never `git add .`). Write a comprehensive commit message organized by severity:

```
fix: address all PR #N review issues — security, migration, correctness

Backend security (IDOR fixes):
- <file>: <what changed and why>

Migration:
- <file>: <what changed and why>

Frontend:
- <file>: <what changed and why>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### Step 7 — Update Tracker

Append or update the PR's section in `.claude/pr-review-log.md` with one line per issue:

```markdown
## PR #<N> · <branch-name>
- [x] P1 · <file>: <one-line description>
- [x] P2 · <file>: <one-line description>
- [ ] P3 · <file>: skipped (not critical)
```

Rules:
- `[x]` = fixed and committed  |  `[ ]` = skipped/deferred
- One line per distinct issue — no prose
- If the section already exists (re-run), update in place (don't duplicate)

### Step 8 — Push

```bash
git push origin <branch>
```

## Common Pitfalls

- **Unused imports**: Adding `import sqlalchemy as sa` then only using it in one place may not be needed in all files — the pre-commit ruff hook will catch this, causing the commit to fail. Remove before committing.
- **Check ALL endpoints, not just the one mentioned**: If a reviewer flags `approve_recommendation` for missing ownership, check `list`, `get`, `decline` too — same pattern likely applies.
- **Migration constraint names must be consistent**: If you rename a constraint in `upgrade()`, the corresponding `downgrade()` must use the same name.
- **403 vs 404 for ownership failures**: Return 403 (not 404) when a resource exists but belongs to another user. 404 would leak existence information.

- **Alembic enum rename order in downgrade**: `ALTER TYPE old RENAME TO new` must come **before** `alter_column` that references it — in both upgrade AND downgrade. In downgrade, the post-upgrade name is still active; rename first or the type reference fails.
- **Fail-open vs fail-closed**: When fixing one delete endpoint for missing ownership check, scan for sibling endpoints with the same pattern (`delete_context_item` and `delete_guardrail_rule` had the same bug — only one was caught initially).

## Example from This Project

Session 2026-02-18 fixed 8 issues from PR #4 in commit `b86923d`:
- P1: Recommendations IDOR (list/get/approve/decline all missing `user_id` filter)
- P1: Metrics IDOR (account ownership not checked)
- P1: Metrics `day_offset` computed from calendar start, not `optimization_enabled_at`
- P1: Migration NOT NULL without `server_default` (would block production deploy)
- P2: CPA metric in frontend, rejected by backend validator
- P2: Google OAuth ignoring `email_verified` claim from token
- P2: Decline endpoint body fields treated as query params
- P2: Migration `downgrade()` calling `drop_constraint(None, ...)` → TypeError
