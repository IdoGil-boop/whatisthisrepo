# Skills Maintenance (Session-Aware)

Update Claude Code skills in `.claude/skills/` based on what was learned or built during this session.

## Context

This skill runs **after a working session**. Its job is to capture new knowledge into skills — if the session established a pattern, solved a tricky problem, or created a repeatable workflow, it should become (or update) a skill.

## Workflow

1. **Review what happened this session:**
   - What patterns or conventions were established?
   - Were any existing skills used? Did they need adjustment?
   - Did the session involve a repeatable multi-step process that isn't captured as a skill yet?
2. **Update existing skills if needed:**
   - If a skill's rules or workflow changed based on session learnings, edit it
   - If a skill's examples are now outdated, update them
3. **Propose new skills if warranted:**
   - Only if a clear, repeatable pattern emerged (not a one-off task)
   - Present the recommendation — don't auto-create without user approval
4. **Update `.claude/skills/INDEX.md`** if any skills were added or modified

## Rules

- **Skills live in `.claude/skills/<skill-name>/SKILL.md`**
- **Prefer updating existing skills** over creating new ones
- **One purpose per skill** — if a skill outgrew its scope, split it
- **Keep SKILL.md concise** (<100 lines) — use sibling files for detail
- **Don't create a skill for a one-off task** — skills capture repeatable patterns

## Skill Template

```
.claude/skills/<skill-name>/
  SKILL.md        # Purpose, rules, workflow, definition of done
  examples.md     # Optional: usage examples
  reference.md    # Optional: detailed reference
```

## Definition of Done

- Existing skills affected by session changes are updated
- `.claude/skills/INDEX.md` reflects current state
- Any new skill proposals are presented (not auto-created)
