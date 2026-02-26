---
name: instinct-learning
description: Instinct-based learning system that observes sessions, creates atomic instincts with confidence scoring, and evolves them into skills/commands/agents.
version: 2.0.0
---

# Instinct Learning System

A learning system that turns Claude Code sessions into reusable knowledge through atomic
"instincts" -- small learned behaviors with confidence scoring that accumulate over time
and can evolve into higher-level skills, commands, and agents.

## Core Concept

An **instinct** is the smallest unit of learned behavior:

- **Atomic**: one trigger, one action
- **Confidence-weighted**: 0.3 (tentative) through 0.9 (near-certain)
- **Domain-tagged**: code-style, testing, git, debugging, workflow, architecture, etc.
- **Evidence-backed**: tracks observations that created/reinforced it

Instincts are stored as YAML files in `.claude/instincts/`.

## Instinct YAML Format

Each instinct is a single file with YAML frontmatter and a markdown body:

```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
source: "session-observation"
created: "2026-02-12"
last_reinforced: "2026-02-12"
observations: 5
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.
Favor pure functions, avoid mutable state.

## Evidence
- Observed 5 instances of functional pattern preference
- User corrected class-based approach to functional (2026-02-12)
- Consistent across backend and script code
```

### Required Fields
- `id`: kebab-case unique identifier
- `trigger`: when this instinct applies
- `confidence`: float between 0.1 and 0.9
- `domain`: category tag

### Optional Fields
- `source`: how it was learned (session-observation, imported, repo-analysis)
- `created`: ISO date when first observed
- `last_reinforced`: ISO date of last supporting observation
- `observations`: count of supporting observations
- `imported_from`: source file/URL if inherited
- `imported_at`: ISO timestamp if inherited

## Confidence Scoring

### Tiers

| Score | Label        | Behavior                             |
|-------|--------------|--------------------------------------|
| 0.3   | Tentative    | Suggested but not enforced           |
| 0.5   | Moderate     | Applied when clearly relevant        |
| 0.7   | Strong       | Auto-approved, applied by default    |
| 0.9   | Near-certain | Core behavior, always applied        |

### Confidence Increases When
- The same pattern is observed again in a session (+ 0.1, capped at 0.9)
- User does not correct the applied behavior (+ 0.05 passive reinforcement)
- An imported instinct from another source agrees (+ 0.05)

### Confidence Decreases When
- User explicitly corrects the behavior (- 0.2)
- Contradicting evidence appears (- 0.1)
- Not observed for a long period (- 0.05 per month, floor at 0.1)

### Update Rules
- Never exceed 0.9 (always leave room for user override)
- Never drop below 0.1 (keep record even if rarely used)
- On contradiction: create competing instinct rather than deleting
- On reinforcement: update `last_reinforced` and `observations` count

## Directory Structure

```
.claude/instincts/
  personal/           # Auto-discovered from sessions
  inherited/          # Imported from teammates or other sources
  evolved/            # Higher-level artifacts generated from clusters
    agents/           # Multi-step process agents
    skills/           # Auto-triggered behavior skills
    commands/         # User-invoked action commands
```

## How Instincts Are Created

### During Sessions (Primary Method)

The `/maintain` command (post-session maintenance) analyzes the session for patterns:

1. **User corrections**: User tells Claude to do X differently -> instinct
2. **Error resolutions**: A specific approach fixed a recurring error -> instinct
3. **Repeated workflows**: Same sequence of actions taken 3+ times -> instinct
4. **Tool preferences**: User consistently prefers one tool/approach -> instinct

### Via Import

Teammates can share instincts through `/instinct-import`. Imported instincts:
- Land in `inherited/` (separate from personal discoveries)
- Carry source tracking metadata
- Start at the imported confidence level

### Via Hook Observation (Advanced)

PostToolUse hooks can log patterns to an observations file. A background observer
analyzes these logs and creates instincts from repeated patterns:

```
Session Activity -> hooks capture tool use -> observations.jsonl
  -> pattern detection -> create/update instinct files
```

## Evolution Process

When 3+ related instincts accumulate, `/instinct-evolve` can cluster them into:

- **Commands**: repeatable user-invoked sequences (e.g., "new-table" workflow)
- **Skills**: auto-triggered behavioral patterns (e.g., "functional-patterns" style)
- **Agents**: complex multi-step processes (e.g., "debugger" workflow)

Evolved artifacts live in `.claude/instincts/evolved/` and link back to source instincts
via the `evolved_from` field in their YAML frontmatter.

## Integration with /maintain

The `/maintain` command should check for learnable patterns at session end:

1. Review what corrections the user made during the session
2. Check if any existing instincts were reinforced or contradicted
3. Create new instincts for novel patterns (start at confidence 0.3)
4. Bump confidence on reinforced instincts (+ 0.1)
5. Decrease confidence on contradicted instincts (- 0.2)

## Commands Reference

| Command             | Purpose                                            |
|---------------------|----------------------------------------------------|
| `/instinct-status`  | Show all instincts grouped by domain + confidence  |
| `/instinct-import`  | Import instincts from YAML files or URLs           |
| `/instinct-export`  | Export instincts as shareable YAML                  |
| `/instinct-evolve`  | Cluster 3+ related instincts into skills/commands  |

## Applying Instincts During Work

When working on a task, check relevant instincts:

1. Identify the current domain (code-style, testing, git, etc.)
2. Load instincts matching that domain with confidence >= 0.5
3. Apply strong/near-certain instincts (>= 0.7) automatically
4. Suggest moderate instincts (0.5-0.6) when clearly relevant
5. Ignore tentative instincts (< 0.5) unless specifically asked

## Privacy

- Instinct files stay local to the project or user's machine
- Only abstract patterns are stored, never raw code or conversations
- `/instinct-export` strips file paths, project names, and session data
- Users control what gets shared via export filters
