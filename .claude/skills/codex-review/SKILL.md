# Codex Review (Second-Opinion Code Review)

Get an independent second opinion from OpenAI's GPT-5.2-Codex / GPT-5.3-Codex on code changes via OpenRouter. Designed for large and/or architecturally important changes where a fresh perspective catches issues that internal review might miss.

## Context

This skill runs **during or after a code review cycle** — typically between the internal code-reviewer (Task 6) and silent-failure-hunter (Task 7) in a BUILD workflow. It can also be invoked standalone via `/codex-review`.

**When to trigger automatically** (any of):
- Diff exceeds 200 lines
- Changes touch core architecture files (models, pipeline, config, auth, guardrails, scoring, worker)
- Changes modify security-sensitive code (auth, tokens, middleware, validators)
- Changes span 5+ files across subsystems

**When to skip**:
- Diff is small (<200 lines) and doesn't touch important files
- Changes are purely docs/tests/comments
- User explicitly opts out

## Prerequisites

- `OPENAI_API_KEY_CODE_REVIEW` environment variable set (or in backend/.env)
- `httpx` Python package installed (`pip install httpx`)
- Optional: `CODEX_MODEL` env var to override model (default: `openai/gpt-5.2-codex`)
- Optional: `CODEX_EFFORT` env var for reasoning effort (default: `high`)

## Workflow

1. **Assess the change:**
   ```bash
   python3 "$CLAUDE_PROJECT_DIR"/.claude/scripts/codex_review.py --assess-only
   ```
   Check if the change qualifies for Codex review (large or important).

2. **If qualified, run the review:**
   ```bash
   python3 "$CLAUDE_PROJECT_DIR"/.claude/scripts/codex_review.py --base HEAD
   ```
   The script automatically:
   - Extracts the git diff
   - Sanitizes secrets and sensitive data (API keys, tokens, .env files)
   - Truncates if >4000 lines
   - Sends to Codex via OpenRouter
   - Returns structured findings

3. **Parse the response** and integrate findings into the review workflow:
   - CRITICAL/HIGH findings → add to code-reviewer handoff as blocking issues
   - MEDIUM findings → add as suggestions
   - APPROVE verdict → note as "Codex second-opinion: approved"

4. **Present findings to user** in the standard review format:
   ```
   CODEX SECOND-OPINION REVIEW
   ============================
   Model: openai/gpt-5.2-codex
   Verdict: APPROVE | NEEDS_WORK | BLOCK

   [CRITICAL] ...
   [HIGH] ...
   [MEDIUM] ...

   Key insight: <one-sentence takeaway>
   ```

## Options

| Flag | Description |
|------|-------------|
| `--base <ref>` | Git ref to diff against (default: HEAD) |
| `--model <id>` | Override model (e.g., `openai/gpt-5.3-codex`) |
| `--effort <level>` | Reasoning effort: low, medium, high, xhigh |
| `--force` | Skip threshold check, always send for review |
| `--assess-only` | Only check if change qualifies, don't call API |
| `--json` | Output assessment as JSON (for programmatic use) |

## Rules

- **Never send secrets externally** — the script sanitizes, but verify .env diffs are stripped
- **Never auto-accept Codex findings** — present to user, let them decide
- **Codex findings are additive** — they supplement, never replace, the internal code-reviewer
- **Cost awareness** — GPT-5.2-Codex costs ~$1.75/M input + $14/M output tokens. Large diffs can be $0.50-2.00 per review
- **Respect the threshold** — don't send trivial changes to Codex unless `--force` is used
- **Data security** — follows the same principle as PromptDistiller: sensitive data never leaves the local environment

## Integration with cc10x Workflows

### BUILD Workflow
Insert between code-reviewer and silent-failure-hunter:
```
Task 5: component-builder →
Task 6: code-reviewer →
Task 6.5: codex-review (if qualified) →   ← NEW
Task 7: silent-failure-hunter →
Task 8: integration-verifier →
Task 9: memory update
```

### Orchestrate Command
Added to `feature` and `refactor` workflow chains when changes are large:
```
feature:  planner -> tdd-guide -> code-reviewer -> codex-review -> security-reviewer
refactor: architect -> code-reviewer -> codex-review -> tdd-guide
```

### Standalone
```
/codex-review           # Review current uncommitted changes
/codex-review --force   # Force review even for small changes
```

## Definition of Done

- Codex review response received and parsed
- Findings categorized by severity (CRITICAL/HIGH/MEDIUM)
- Results presented to user with clear verdict
- Any blocking findings flagged in the workflow handoff
- No sensitive data leaked in the API call
