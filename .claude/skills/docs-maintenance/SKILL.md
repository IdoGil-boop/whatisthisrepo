# Docs Maintenance (Session-Aware)

Update project documentation in `docs/` to reflect what changed during this session — new features, changed behavior, updated architecture, deprecated flows.

## Context

This skill runs **after a working session**. Its job is to make sure `docs/` accurately reflects the current state of the codebase, given what was just built, changed, or removed.

## Workflow

1. **Understand what changed this session:**
   - Run `git diff --name-only HEAD` and `git log --oneline -5` to see recent changes
   - Review the session transcript/context for decisions and changes made
2. **For each significant change, check if docs need updating:**
   - Did a feature's behavior change? → Update the relevant architecture or guide doc
   - Was a new API endpoint added? → Update API docs
   - Was a module removed or renamed? → Remove/update references in docs
   - Was a new pattern established? → Add to architecture docs if significant
3. **Feature docs — create or update dedicated docs for features:**
   - **New feature** (API endpoint, pipeline stage, infra component, non-trivial script): Create a doc in `docs/architecture/` or `docs/guides/`. Name it after the feature (e.g., `CELERY_WORKER_HEALTHCHECK.md`), not the session.
   - **Modified feature**: Find the existing doc and update it. If no doc exists and the change is non-trivial, create one.
   - **Skip**: Bug fixes, config tweaks, minor refactors, style changes.
   - Add to `docs/INDEX.md` and reference from `CLAUDE.md` if architecturally significant.
4. **Update affected docs** (edit in place; prefer updating over creating new files)
5. **Fix any collateral damage:**
   - Broken links caused by file renames/moves
   - Contradictions between updated code and stale doc descriptions
6. **Update `docs/INDEX.md`** if any docs were added or removed

## Rules

- **All docs live in `docs/`** — don't create doc files elsewhere
- **Prefer updating existing docs** over creating new ones
- **Focus on session changes** — don't do a full audit; only update what this session's work made stale
- **`docs/INDEX.md` must stay accurate** — update it if docs were added/removed
- **CLAUDE.md is an intro+index** — never inline detailed content. Move details to `docs/reference/` or `docs/architecture/` and add a reference in CLAUDE.md. Key detail docs:
  - `docs/reference/COMMON_GOTCHAS.md` — gotchas, naming conventions, infrastructure pitfalls
  - `docs/reference/PRODUCTION_DEPLOYMENT.md` — domains, Docker, nginx, SSL, scripts
  - `docs/reference/ORM_MODELS.md` — model attributes, relationships

## Definition of Done

- Docs affected by this session's changes are updated
- No contradictions between changed code and existing docs
- `docs/INDEX.md` is accurate
- CLAUDE.md remains a concise index (under ~120 lines), no new inline detail added
