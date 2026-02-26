---
name: iterative-retrieval
description: Pattern for progressively refining context retrieval in sub-agent and multi-step workflows
version: 1.0.0
---

# Iterative Retrieval Pattern

Solves the "context problem" in multi-agent and multi-step workflows where the agent
does not know what context it needs until it starts working.

## The Problem

When a sub-agent (or the main agent tackling a broad task) is spawned with limited
context, it faces a dilemma:

- **Send everything**: exceeds context limits, drowns signal in noise
- **Send nothing**: agent lacks critical information, produces wrong output
- **Guess what's needed**: often wrong, misses non-obvious dependencies

## The Solution: 4-Phase Iterative Loop

A progressive refinement loop that narrows context over at most 3 cycles:

```
  DISPATCH ----> EVALUATE
     ^               |
     |               v
    LOOP <------ REFINE

  Max 3 cycles, then proceed with best available context
```

### Phase 1: DISPATCH

Start with a broad initial query based on high-level intent:

- Use glob patterns to find candidate files (e.g., `src/**/*.py`, `app/**/*.ts`)
- Search for keywords related to the task
- Exclude obvious non-matches (tests, generated files, vendor)

Goal: cast a wide net, gather candidate files.

### Phase 2: EVALUATE

Score each retrieved file for relevance to the task:

- **High (0.8-1.0)**: Directly implements target functionality
- **Medium (0.5-0.7)**: Contains related patterns, types, or interfaces
- **Low (0.2-0.4)**: Tangentially related
- **None (0-0.2)**: Not relevant, exclude from future cycles

For each file, also identify:
- What context it provides
- What context is still missing (gaps)
- What new search terms it reveals (e.g., codebase-specific naming)

### Phase 3: REFINE

Update search criteria based on evaluation:

- **Add** new patterns and keywords discovered in high-relevance files
- **Adopt** codebase terminology (the first cycle often reveals naming conventions)
- **Exclude** confirmed irrelevant paths
- **Target** specific gaps identified in evaluation

### Phase 4: LOOP

Check termination conditions:
- Have 3+ high-relevance files AND no critical gaps? -> **Stop, return context**
- Reached cycle 3? -> **Stop, return best available**
- Otherwise -> **Go back to DISPATCH with refined query**

## Practical Example

```
Task: "Fix the authentication token expiry bug"

Cycle 1:
  DISPATCH: Search for "token", "auth", "expiry" in backend/
  EVALUATE: Found auth.py (0.9), tokens.py (0.8), user.py (0.3)
  REFINE:   Add "refresh", "jwt"; exclude user.py

Cycle 2:
  DISPATCH: Search refined terms
  EVALUATE: Found session_manager.py (0.95), jwt_utils.py (0.85)
  REFINE:   Sufficient context (4 high-relevance files)

Result: auth.py, tokens.py, session_manager.py, jwt_utils.py
```

## Integration with Agents

When an orchestrator delegates to a sub-agent:

1. Orchestrator provides the task description and initial hints
2. Sub-agent runs iterative retrieval to gather its own context
3. Orchestrator evaluates what the sub-agent found:
   - If insufficient: provide additional hints, ask sub-agent to refine
   - If sufficient: accept and let sub-agent proceed
4. Sub-agent completes the task with validated context

This creates a **context negotiation** between orchestrator and sub-agent:

```
Orchestrator:  "Fix the auth bug. Start with backend/app/auth/"
Sub-agent:     [Cycle 1] "Found auth.py, tokens.py. Missing: session handling"
Orchestrator:  "Check backend/app/sessions/ as well"
Sub-agent:     [Cycle 2] "Found session_manager.py. Context sufficient."
Orchestrator:  "Proceed."
```

## When to Use This Pattern

- **Bug investigations**: narrowing from symptom to root cause
- **Feature implementation**: understanding existing patterns before adding new code
- **Refactoring**: mapping all call sites and dependencies
- **Code review**: understanding the full context of a change

## Best Practices

1. **Start broad, narrow progressively** -- do not over-specify initial queries
2. **Learn codebase terminology** -- the first cycle often reveals naming conventions
   that differ from the task description
3. **Track what's missing explicitly** -- gap identification drives refinement
4. **Stop at "good enough"** -- 3 high-relevance files beats 10 mediocre ones
5. **Exclude confidently** -- low-relevance files in cycle 1 rarely become relevant
6. **Respect the 3-cycle limit** -- if context is still unclear after 3 cycles,
   proceed with what you have and note assumptions

## Anti-Patterns

- **Infinite refinement**: going beyond 3 cycles looking for perfection
- **Keyword stuffing**: adding too many search terms makes queries less precise
- **Ignoring gaps**: proceeding without noting what context is missing
- **Over-reading**: reading every file fully instead of scanning for relevance first
- **Skipping evaluation**: jumping from dispatch to action without scoring relevance

## Related

- `instinct-learning` skill -- instincts can encode which retrieval patterns work
  for this specific codebase
- Agent definitions in `.claude/agents/` -- agents that benefit from this pattern
- `/instinct-evolve` -- repeated retrieval patterns can evolve into codebase-specific
  retrieval skills
