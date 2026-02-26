# Workflow Recommender (Session-Aware)

Based on this session's work, recommend new skills, agents, hooks, or commands that would reduce friction in future sessions.

## Context

This skill runs **after a working session**. Its job is to notice what was painful, repetitive, or manual during the session and suggest automations for next time.

## When to Recommend

- **Repeated manual steps** — did the session involve doing the same thing multiple times?
- **Friction points** — was there a task that took too long or required too many steps?
- **Missing automation** — did you wish a hook or command existed?
- **Pattern emergence** — did a new repeatable workflow crystallize?
- **Toolbox gaps** — was there knowledge that should have been a skill but wasn't?

## Workflow

1. **Review the session:**
   - What tasks were performed?
   - What was repeated or tedious?
   - What commands were run frequently?
   - What decisions required looking things up that could be codified?
2. **For each candidate, decide where it should live:**
   - **Skill** — repeatable knowledge/checklist (`.claude/skills/<name>/SKILL.md`)
   - **Agent** — multi-step workflow needing tool access (`.claude/agents/<name>.md`)
   - **Hook** — automatic trigger on events (`.claude/settings.json`)
   - **Command** — shortcut for common action (`.claude/commands/<name>.md`)
3. **Output recommendations** (don't auto-create — present for user approval)

## Recommendation Format

```
### Recommendation: <short title>

**Type:** skill | agent | hook | command
**Why:** <what happened this session that motivates this>
**Where:** <file path where it would live>
**Effort:** low | medium | high
```

## Rules

- Only recommend if the pattern is likely to recur
- Don't duplicate existing skills/agents/hooks
- Present recommendations, don't auto-create
- Ensure anything created would be discoverable via indexes

## Definition of Done

- Session reviewed for automation opportunities
- Recommendations are specific and actionable
- No recommendation duplicates existing toolbox items
