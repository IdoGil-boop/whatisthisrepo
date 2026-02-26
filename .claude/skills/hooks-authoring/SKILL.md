# Hooks Authoring

Write and maintain Claude Code hooks in `.claude/settings.json` using the correct matcher-based format.

## Format (Current)

Hooks have three levels: **event** → **matcher group** → **hooks array**.

```json
{
  "hooks": {
    "<Event>": [
      {
        "matcher": "<regex or omit for all>",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/my-script.py"
          }
        ]
      }
    ]
  }
}
```

The `matcher` field is optional — omit it to fire on every occurrence of the event.

## Common Events

| Event | Matcher filters on | Example matchers |
|-------|-------------------|-----------------|
| `SessionStart` | how session started | `startup`, `resume`, `clear`, `compact` |
| `SessionEnd` | exit reason | `clear`, `logout`, `prompt_input_exit`, `other` |
| `PreToolUse` | tool name | `Bash`, `Edit\|Write`, `mcp__.*` |
| `PostToolUse` | tool name | `Write`, `Edit\|Write` |
| `Stop` | (no matcher) | always fires |
| `UserPromptSubmit` | (no matcher) | always fires |

## Hook Types

- **`command`** — run a shell script. Receives JSON on stdin, returns via exit code + stdout.
- **`prompt`** — single-turn LLM evaluation. Returns `{ "ok": true/false, "reason": "..." }`.
- **`agent`** — multi-turn subagent with tool access. Same return format as prompt.

## Script Conventions

- Use `$CLAUDE_PROJECT_DIR` for project-relative paths (works regardless of cwd)
- Scripts read hook JSON from stdin: `json.load(sys.stdin)` or `jq`
- Exit 0 = success (proceed), Exit 2 = block (with stderr as reason)
- Only Python stdlib or bash — no external dependencies
- Create scripts in `.claude/hooks/`

## Common Patterns

### SessionEnd reminder
```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/my-reminder.py"
          }
        ]
      }
    ]
  }
}
```

### Lint after file writes
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/lint-check.sh"
          }
        ]
      }
    ]
  }
}
```

### Block dangerous commands
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh"
          }
        ]
      }
    ]
  }
}
```

## Gotchas

- **Old format won't load**: `{ "type": "command", "command": "..." }` directly under the event array is invalid. Must be nested inside `{ "hooks": [...] }`.
- **Disabling**: set `"disableAllHooks": true` in settings.json. No per-hook disable.
- **Changes require restart**: hooks are snapshotted at session start.

## Reference

Full docs: https://code.claude.com/docs/en/hooks
