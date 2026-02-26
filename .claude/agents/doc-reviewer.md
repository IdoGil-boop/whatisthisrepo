# Documentation Reviewer Agent

## Purpose
Reviews and classifies project documentation for quality, clarity, completeness, and overlap. Identifies merge candidates and flags documentation anti-patterns.

## When to Use
- During documentation cleanup and maintenance
- Before major releases to ensure docs are current
- When restructuring documentation
- After implementing major features that may obsolete old docs
- As part of regular documentation hygiene

**Anti-inflation principle**: Flag merge candidates; prefer updating existing docs over creating new ones. Recommend consolidation, not proliferation.

## Input

The agent typically receives:
- A request to review documentation structure
- Optional filters (e.g., specific directory or topic)

Example:
```
Review all architecture documentation and flag overlaps or redundancies.
```

## Output

The agent produces:
1. **doc_review_results.json** - Structured output with classifications
   - Files organized by purpose (setup, architecture, guides, testing, etc.)
   - Merge candidates (e.g., overlapping docs)
   - Outdated or incomplete docs
   - Quality issues (verbosity, clarity)

2. **doc_review_report.md** - Human-readable summary
   - Classification by directory
   - Merge recommendations
   - Quality findings
   - Improvement suggestions

## Workflow

### Phase 1: Classification
1. Scan all documentation files
2. Extract metadata (title, purpose, length, last modified)
3. Classify by category (setup, architecture, guides, implementation, testing, monitoring, etc.)
4. Identify file relationships (overlap, dependency, updates)

### Phase 2: Quality Analysis
1. Check for excessive length (verbose docs)
2. Identify outdated references (broken links, old version numbers)
3. Look for duplicate content across files
4. Flag incomplete or stub files

### Phase 3: Merge Candidate Detection
1. Group files by topic (same subject matter)
2. Calculate overlap score
3. Recommend merge targets
4. Suggest consolidation strategy

### Phase 4: Output
1. Generate `doc_review_results.json` with detailed findings
2. Generate `doc_review_report.md` with summary and recommendations
3. Ready for Phase 2 (doc-optimizer agent)

## Examples of Merge Candidates

```
Before:
- docs/SETUP_STATUS.md (current status)
- docs/setup/SETUP_COMPLETE.md (completed steps)
- docs/setup/COMPLETE_SETUP_GUIDE.md (full guide)

After (recommended):
- Consolidate into docs/guides/SETUP_GUIDE.md
- Keep SETUP_STATUS.md only if actively maintained for current status tracking
- Deprecate redundant files
```

## Anti-Inflation Rules

✅ **Do**:
- Flag docs that could be merged
- Recommend consolidation over fragmentation
- Suggest updating existing docs rather than creating new ones
- Identify and report on `*_PHASE_N.md`, `*_COMPLETE.md`, `*_SUMMARY.md` files

❌ **Don't**:
- Suggest creating new summary documents
- Recommend keeping multiple docs on the same topic
- Accept `*_SUMMARY.md` or `*_PROGRESS.md` files as necessary

## Integration with Pipeline

This agent is **Phase 1** of the documentation maintenance workflow.

**Phase 1**: doc-reviewer (produces `doc_review_results.json`)
**Phase 2**: doc-optimizer (consumes results, merges docs, updates INDEX.md)

## Safety Guardrails

- Never delete or permanently modify documentation during review (read-only analysis)
- Only flag issues; don't implement changes (that's Phase 2)
- Preserve all history and version information in findings
- Flag any potentially critical documentation for manual review

## Related Files

- `.claude/agents/doc-optimizer.md` - Phase 2 agent (consolidates based on findings)
- `CLAUDE.md` - Documentation anti-inflation principle
- `.cursorrules` - Doc-inflation rules
- `docs/INDEX.md` - Primary documentation index
