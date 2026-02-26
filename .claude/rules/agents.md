# Agent Orchestration

## Available Agents

Located in `.claude/agents/`:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **planner** | Implementation planning | Complex features, multi-phase refactoring |
| **architect** | System design | Schema changes, pipeline redesign, new subsystems |
| **python-reviewer** | Python code review | After writing Python code; catches ORM gotchas |
| **database-reviewer** | DB schema & query review | Migrations, new models, query performance |
| **tdd-guide** | Test-driven development | New features, bug fixes, security-critical code |
| **e2e-runner** | Playwright E2E testing | Frontend critical user flows |
| **refactor-cleaner** | Dead code cleanup | Post-migration cleanup, removing competing logic |
| **doc-optimizer** | Documentation quality | Reducing doc inflation, updating indexes |
| **post-session-maintainer** | Session capture | End-of-session: captures learnings |

External agents (not in .claude/agents/ but available via skills):
- **security-reviewer** -- Security analysis
- **code-reviewer** -- General code review

## Immediate Agent Usage (No User Prompt Needed)

Trigger agents automatically in these situations:
1. **Complex feature request** -- Use **planner** to break into phases
2. **Code just written/modified** -- Use **python-reviewer** for Python, **code-reviewer** for frontend
3. **Bug fix or new feature** -- Use **tdd-guide** to enforce write-tests-first
4. **Architectural decision** -- Use **architect** for schema/pipeline changes
5. **New migration** -- Use **database-reviewer** to validate up/down

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: python-reviewer on new logic
2. Agent 2: database-reviewer on migration
3. Agent 3: tdd-guide writing test stubs

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

## Multi-Perspective Analysis

For complex problems, use split-role sub-agents:
- **Factual reviewer** -- Are the computations correct?
- **Senior engineer** -- Is the architecture sound?
- **Security expert** -- Any injection, data leakage, or auth issues?
- **Consistency reviewer** -- Does this align with single-source-of-truth principle?
- **Redundancy checker** -- Are we creating competing logic?
