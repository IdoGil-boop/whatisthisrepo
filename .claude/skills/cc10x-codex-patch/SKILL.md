# cc10x Codex Patch (Post-Update)

Re-apply custom patches to the cc10x-router's BUILD workflow after a plugin update overwrites the cached router file.

## Context

The cc10x plugin stores its router at `~/.claude/plugins/cache/cc10x/cc10x/*/skills/cc10x-router/SKILL.md`. Plugin updates overwrite this file, losing our customizations. This skill re-applies all surgical edits needed to restore them.

**Current custom patches (3 total):**
1. **codex-review step** — adds `[codex-review]` agent to the BUILD chain between reviewers and integration-verifier
2. **`/maintain` file coverage** — adds `docs/reference/COMMON_GOTCHAS.md` to the memory load step so the router picks up project-level gotchas written by `/maintain`
3. **`OPENAI_API_KEY_CODE_REVIEW` reference** — corrects the stale `OPENROUTER_API_KEY` in the codex task description

**Run this skill when:**
- The cc10x plugin was updated (you'll notice BUILD workflows no longer include the codex-review step)
- A new session starts and `CC10X codex-review` tasks aren't being created in BUILD workflows
- The router file was reset or recreated

## Workflow

### Step 1: Find the current router file

```bash
find ~/.claude/plugins/cache/cc10x -name "SKILL.md" -path "*/cc10x-router/*" 2>/dev/null
```

Store the path as `$ROUTER_FILE`.

### Step 2: Verify patch is needed

Check if codex-review is already present:
```bash
grep -c "codex-review" "$ROUTER_FILE"
```
If count > 0, the patch is already applied — stop here.

### Step 3: Apply 4 edits

**Edit 1 — Agent Chains table:** Add `[codex-review]` to the BUILD chain.

```
old: | BUILD | component-builder → **[code-reviewer ∥ silent-failure-hunter]** → integration-verifier |
new: | BUILD | component-builder → **[code-reviewer ∥ silent-failure-hunter]** → **[codex-review]** → integration-verifier |
```

**Edit 2 — BUILD parent task description:** Update the chain description.

```
old: Chain: component-builder → [code-reviewer ∥ silent-failure-hunter] → integration-verifier
new: Chain: component-builder → [code-reviewer ∥ silent-failure-hunter] → [codex-review] → integration-verifier
```

**Edit 3 — BUILD Workflow Tasks:** Add codex-review task + re-wire verifier dependency.

Find the block:
```
TaskCreate({ subject: "CC10X integration-verifier: Verify integration", description: "Run tests, verify E2E functionality", activeForm: "Verifying integration" })
# Returns verifier_task_id
TaskUpdate({ taskId: verifier_task_id, addBlockedBy: [reviewer_task_id, hunter_task_id] })
```

Replace with:
```
TaskCreate({ subject: "CC10X codex-review: Second-opinion review", description: "Conditional: runs if change is large (200+ lines) or touches important files.\nAssess via: python3 .claude/scripts/codex_review.py --assess-only\nIf should_review=true: python3 .claude/scripts/codex_review.py\nIf should_review=false: skip and mark completed immediately.\nRequires OPENAI_API_KEY_CODE_REVIEW (backend/.env or env).", activeForm: "Running Codex review" })
# Returns codex_task_id
TaskUpdate({ taskId: codex_task_id, addBlockedBy: [reviewer_task_id, hunter_task_id] })

TaskCreate({ subject: "CC10X integration-verifier: Verify integration", description: "Run tests, verify E2E functionality", activeForm: "Verifying integration" })
# Returns verifier_task_id
TaskUpdate({ taskId: verifier_task_id, addBlockedBy: [codex_task_id] })
```

**Edit 4 — Codex Review Execution section:** Add after "Parallel Execution" section, before "Workflow-Final Memory Persistence".

Insert this new section:
```markdown
### Codex Review Execution (Conditional)

When the `CC10X codex-review` task becomes runnable (after code-reviewer + silent-failure-hunter complete):

\```
1. Assess change size:
   Bash(command="python3 .claude/scripts/codex_review.py --assess-only")

2. If output shows "Should review: False":
   → Mark task completed immediately (skip)
   → TaskUpdate({ taskId: codex_task_id, status: "completed" })
   → Proceed to integration-verifier

3. If output shows "Should review: True":
   → Check OPENAI_API_KEY_CODE_REVIEW:
     Bash(command="test -n \"$OPENAI_API_KEY_CODE_REVIEW\" && echo 'SET' || echo 'NOT_SET'")
   → If NOT_SET:
     AskUserQuestion: "Codex review needs OPENAI_API_KEY_CODE_REVIEW. Skip / Set key and retry"
   → If SET:
     Bash(command="python3 .claude/scripts/codex_review.py", timeout=120000)
   → Parse findings from output
   → If CRITICAL/HIGH findings: include in integration-verifier prompt
   → TaskUpdate({ taskId: codex_task_id, status: "completed" })
\```

**Cost note:** GPT-5.2-Codex costs ~$0.50-2.00 per review. The threshold gate prevents wasting budget on small changes.

**Data safety:** The script sanitizes secrets (API keys, tokens, .env contents) before sending to OpenAI.
```

**Edit 5 (optional) — Results Collection:** In the integration-verifier prompt template, add Codex findings section after Silent Failure Hunter:

```markdown
   ### Codex Review (Second Opinion)
   **Status:** {Ran/Skipped (change too small)}
   **Verdict:** {Approve/Needs Work/Block or 'N/A if skipped'}
   **Findings:**
   {CODEX_FINDINGS or 'N/A'}
```

### Step 4: Apply /maintain file coverage patch

**Verify patch is needed:**
```bash
grep -c "COMMON_GOTCHAS" "$ROUTER_FILE"
```
If count > 0, skip — already patched.

**Edit — Memory Load Step 2:** After the 3 existing `Read(file_path=".claude/cc10x/...")` lines, insert:

```
old (after progress.md Read line):
```
Read(file_path=".claude/cc10x/progress.md")
```

new:
```
Read(file_path=".claude/cc10x/progress.md")
Read(file_path="docs/reference/COMMON_GOTCHAS.md")  # Project gotchas updated by /maintain — read every session
```

Also add the /maintain file coverage note block immediately after:
```
**`/maintain` file coverage** — these files are written by `/maintain` and contain session learnings:
- `docs/reference/COMMON_GOTCHAS.md` — **always read** (canonical project gotchas, code examples, patterns)
- `CLAUDE.md` — already in session system context; skip explicit read
- `docs/INDEX.md` — read only if feature docs were added this session (check ## References in activeContext.md)
- `docs/architecture/*.md` / `docs/guides/*.md` — read on demand when task touches those domains
```

### Step 5: Fix OPENROUTER_API_KEY → OPENAI_API_KEY_CODE_REVIEW

**Verify patch is needed:**
```bash
grep -c "OPENROUTER_API_KEY" "$ROUTER_FILE"
```
If count = 0, skip — already patched.

**Edit — BUILD Workflow Tasks, codex task description:**
```
old: "Requires OPENROUTER_API_KEY env var."
new: "Requires OPENAI_API_KEY_CODE_REVIEW env var (or key in backend/.env — script auto-loads)."
```

### Step 6: Verify all patches

```bash
grep -c "codex-review" "$ROUTER_FILE"
grep -c "COMMON_GOTCHAS" "$ROUTER_FILE"
grep -c "OPENROUTER_API_KEY" "$ROUTER_FILE"  # must be 0
grep -c "OPENAI_API_KEY_CODE_REVIEW" "$ROUTER_FILE"  # must be 3+
```
Expected: codex-review ≥ 5, COMMON_GOTCHAS ≥ 2, OPENROUTER_API_KEY = 0, OPENAI_API_KEY_CODE_REVIEW ≥ 3.

## Rules

- **Idempotent** — check before applying each patch; don't double-patch
- **Version-aware** — the router structure may change across cc10x versions; if the old_string anchors don't match, read the file and adapt
- **Don't modify other workflows** — only patch BUILD; DEBUG/REVIEW/PLAN stay unchanged
- **Preserve formatting** — match the existing indentation and style in the router file

## Prerequisites

These project files must exist (they are version-controlled and survive plugin updates):
- `.claude/scripts/codex_review.py` — the review script
- `.claude/skills/codex-review/SKILL.md` — the skill definition
- `.claude/commands/codex-review.md` — the slash command

## Definition of Done

- Router file contains all 4-5 edits
- `grep -c "codex-review" "$ROUTER_FILE"` returns 5+
- Next BUILD workflow creates a `CC10X codex-review` task in the hierarchy
