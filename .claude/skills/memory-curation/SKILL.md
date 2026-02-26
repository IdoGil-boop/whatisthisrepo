# Memory Curation (Session-Aware)

Capture durable knowledge from this session into `CLAUDE.md` and project memory — decisions made, conventions established, gotchas discovered.

## Context

This skill runs **after a working session**. Its job is to distill what was learned into persistent memory so future sessions (by you or other agents) benefit from it. Think: "what do I wish I'd known at the start of this session?"

## Workflow

1. **Review the session for durable learnings:**
   - **Decisions**: "We chose X over Y because Z" → capture rationale
   - **Conventions**: "From now on, we always do X" → add to conventions
   - **Sources of truth**: "This function is the single authority for X" → update sources list
   - **Gotchas**: "This broke because of X, watch out for Y" → add to gotchas
   - **Architecture changes**: "We moved from X to Y pattern" → update architecture section
2. **Classify each learning:**
   - Belongs in `CLAUDE.md`? → Update the appropriate section
   - Belongs in a `docs/` file? → Update the doc, link from `CLAUDE.md`
   - Belongs in `.claude/cc10x/patterns.md`? → Update there (session-level gotchas)
   - Transient (won't matter next session)? → Skip
3. **Prune stale entries** if session work invalidated existing memory
4. **Keep `CLAUDE.md` short** — under 250 lines; extract detail into docs

## What Belongs in CLAUDE.md

- Source-of-truth declarations (new or changed this session)
- Coding conventions and anti-patterns discovered
- Architecture decision summaries
- "How we do things here" rules

## What Does NOT Belong

- What was done this session (that's a session log, not memory)
- Temporary workarounds
- Implementation details (link to docs)

## Definition of Done

- Session learnings that will matter in future sessions are captured
- `CLAUDE.md` is under 250 lines with no stale references
- No duplication between `CLAUDE.md` and `docs/`
