---
name: commit-by-feature
description: Groups all unstaged/untracked git changes by logical domain and commits them as separate, well-described commits. Use when a large batch of changes needs to be committed cleanly after a multi-phase session.
---

# Commit by Feature

Splits a large unstaged batch into logical commits -- one per feature/domain -- following the project's conventional commit format.

## When to Use

- After a multi-phase session with many modified/deleted/new files
- When `git status` shows 10+ files across unrelated domains
- Before creating a PR -- clean history makes review easier
- When `git add .` + one commit would mix unrelated concerns

## Workflow

### Step 1 -- Survey

Run `git status --short` and `git diff --stat HEAD` to get the full picture. Also check `git log --oneline -5` for commit message style reference.

### Step 2 -- Group by Domain

Mentally (or explicitly) group files by what they change together:

| Domain | File patterns | Commit type |
|--------|--------------|-------------|
| Backend security | `src/routes/*.py`, `tests/test_*ownership*.py` | `fix:` or `security:` |
| Backend API | `src/routes/*.py`, `src/models*.py` | `feat:` or `fix:` |
| Frontend API client | `frontend/lib/api/*.ts`, `frontend/lib/types/api.ts` | `fix:` or `feat:` |
| Frontend components | `frontend/components/**/*.tsx` | `feat:` or `fix:` |
| Frontend pages | `frontend/app/**/*.tsx` | `feat:` or `fix:` |
| Legacy cleanup (deletions) | Deleted files only | `chore:` |
| Dependencies | `package.json`, `package-lock.json`, `requirements*.txt` | `chore:` |
| Docs/plans | `docs/**`, `*.md` | `docs:` |
| Tests | `**/tests/**`, `*.spec.ts` | `test:` |
| CI/Infra | `.github/**`, `scripts/**`, `Dockerfile*` | `ci:` or `chore:` |

### Step 3 -- Stage and Commit Each Group

For each group, use explicit file paths (never `git add .`):

```bash
git add <file1> <file2> <file3>
git commit -m "$(cat <<'EOF'
fix: short description of what changed and why

Longer body if needed -- explain the problem solved,
not just what files were modified.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

### Step 4 -- Verify Clean State

```bash
git status --short   # Should only show unintentional untracked files
git log --oneline -10  # Review the commit sequence makes sense
```

## Rules

- **Never use `git add .` or `git add -A`** -- risks committing `.env`, secrets, or build artifacts
- **Never commit**: `playwright-report/`, `tsconfig.tsbuildinfo`, `.next/`, `__pycache__/`, `.env*`
- **One logical change per commit** -- if you can't write a one-line summary, split it further
- **Deletions deserve their own commit** -- cleaner than mixing with feature work
- **Dependency bumps alone** -- separate from the feature that uses them

## Conventional Commit Types

| Type | When |
|------|------|
| `feat:` | New feature or endpoint |
| `fix:` | Bug fix or correcting wrong behavior |
| `refactor:` | Restructuring without behavior change |
| `chore:` | Deletions, dependency bumps, config |
| `docs:` | Documentation only |
| `test:` | Tests only |
| `ci:` | CI/CD pipeline changes |
| `perf:` | Performance improvement |
| `security:` | Security fix (use for high-severity) |
