---
name: verify-plan
description: Verifies a plan document was fully executed by cross-checking each phase/item against actual file contents and code. Produces a pass/fail assessment per item and a summary of gaps. Use after a multi-agent implementation session to confirm nothing was missed before merging.
---

# Plan Verification

Systematic code-level audit of a plan document against the actual codebase. More reliable than accepting agent handoff claims at face value.

## When to Use

- After a multi-agent implementation session before creating a PR
- When an agent reports "COMPLETE" but you want independent verification
- When handing off between sessions (verify what was actually done)
- When a handoff doc says "all waves complete" and you need to trust but verify

## Workflow

### Step 1 — Read the Plan

Read the plan file in full. Extract each phase/sub-item as a checklist:

```
plan: /path/to/plan.md
```

Identify for each item:
- What file should be created or modified?
- What specific behavior or content should exist?
- Is it marked required or optional?

### Step 2 — Check Each Item Against Code

For each plan item, don't accept the handoff doc — go to the source:

**File existence checks:**
```bash
ls path/to/expected/file.tsx
```

**Content verification (grep for specific patterns):**
```bash
# Verify method exists
grep -n "addLandingPage" frontend/lib/api/settings.ts

# Verify field name is correct
grep -n "structured_rules" frontend/lib/types/api.ts

# Verify security dep added
grep -n "get_current_user" backend/app/routes/scope_settings.py

# Verify link target changed
grep -n '"/accounts"' frontend/app/connect/callback/page.tsx
```

**Type compile check:**
```bash
cd frontend && npx tsc --noEmit
```

**Test existence + pass:**
```bash
cd backend && pytest tests/test_scope_settings_ownership.py -v --tb=short
```

### Step 3 — Produce Assessment Table

Write a verification table per phase:

| Phase | Item | Status | Evidence |
|-------|------|--------|----------|
| 1A | `addLandingPage()` in settings.ts | ✅ VERIFIED | `settings.ts:10` |
| 1B | `structured_rules` type field | ✅ VERIFIED | `api.ts:324` |
| 1E | DELETE ownership check | ✅ VERIFIED | `scope_settings.py:718-757` |
| 2A | Dashboard card → `/accounts/${id}` | ✅ VERIFIED | `account-card.tsx:53` |
| 5B | Scope detail page | ⏭️ SKIPPED | Optional per plan |
| 6C | Browser testing | ⚠️ NOT VERIFIABLE | Manual step, no code artifact |

Status codes:
- ✅ VERIFIED — code confirms it
- ℹ️ KEPT INTENTIONALLY — not done because correct reasoning (e.g., still referenced)
- ⏭️ SKIPPED — plan marked it optional
- ⚠️ NOT VERIFIABLE — requires manual check (browser test, runtime behavior)
- ❌ MISSING — plan required it but not found in code

### Step 4 — Flag Gaps and Contradictions

Look specifically for:
- **File deleted that was supposed to be modified** (plan said "fix link in X" but X was deleted)
- **Handoff says "modified" but file content doesn't match** (silently wrong)
- **New files exist but not wired up** (created but no import/route)
- **Type mismatches** between frontend types and backend response schema
- **Test file created but tests don't actually cover the claimed scenarios**

### Step 5 — Git Status and Commit State

```bash
git status --short   # Anything unstaged that should be committed?
git log --oneline -10  # Are all changes actually committed?
```

Unstaged changes = work done but not saved. Flag this prominently.

### Step 6 — Write Assessment to Handoff Doc

Append a `## Independent Verification Assessment` section to the handoff doc with:
- Phase-by-phase table (Step 3)
- TypeScript compile status
- Test pass count
- Git commit state
- Building session instructions (what's left to do)

## Key Verification Heuristics

**"Trust but verify" checklist:**
1. Agent said "COMPLETE" → grep for the specific method/class name in the file
2. Agent said "deleted" → verify with `git status -D` or `ls`
3. Agent said "fixed type" → grep the exact field name in types file
4. Agent said "added ownership check" → read the endpoint function, not just the function signature
5. Agent said "8 tests pass" → run `pytest test_file.py -v` yourself

**Common silent failures to check:**
- Frontend sends to `PUT /items/{id}` but backend expects `PATCH /items/{id}` → method mismatch
- Frontend sends `account_id` in URL but backend DELETE route has no path param for it
- Backend adds security dep but imports aren't present → `ImportError` at runtime
- New hook/component created but not imported by any page → dead code

## Output Format

Produce the assessment as markdown suitable for appending to a handoff doc:

```markdown
## Independent Verification Assessment (YYYY-MM-DD)

| Phase | Item | Status | Notes |
|-------|------|--------|-------|
...

### TypeScript: ✅ Zero errors (`npx tsc --noEmit`)
### Tests: ✅ 8/8 passing (`pytest test_scope_settings_ownership.py`)
### Git: ⚠️ 15 files unstaged — commit before merging

## Building Session Instructions
1. Run: `cd backend && pytest tests/test_scope_settings_ownership.py -v`
2. Commit all changes (see grouping below)
3. Open PR to main
```
