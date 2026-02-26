# Stash Recovery

Safely recover a git stash that was created before a merge or branch change. Prevents the common mistake of treating merge-added files as "intentional deletions" in the stash diff.

## When to Use

- User says "restore my stash", "recover stash", "pop my stash"
- A stash predates a merge commit on the current branch
- After `git stash pop` produces conflicts or unexpected file state

## The Problem

When a stash was created *before* a merge commit, `git diff HEAD stash@{N}` shows files added by the merge as "deletions" in the stash. These are NOT intentional deletions — the stash simply doesn't contain files that didn't exist when it was created.

**Mistake to avoid**: Deleting files that appear as "removed" in the stash diff when they were actually Added (A) by the merge.

## Recovery Checklist

### 1. Inventory the stash and recent history

```bash
# What's in the stash?
git stash list
git stash show -p stash@{0} --stat

# What happened between stash creation and HEAD?
git log --oneline --all --graph -10
```

### 2. Identify files added by intervening merges

```bash
# For each merge commit between stash creation and HEAD:
git diff-tree --no-commit-id -r --name-status <merge-commit>
```

Files with status `A` (Added) were introduced by the merge. These MUST NOT be deleted during stash recovery.

### 3. Classify stash diff entries

For every file that appears "deleted" in `git diff HEAD stash@{0}`:

| Scenario | Action |
|----------|--------|
| File existed BEFORE the merge and stash removes it | Genuine deletion — apply it |
| File was Added (A) by the merge commit | NOT a deletion — keep the file |
| File was modified by both stash and merge | Merge conflict — resolve manually |

### 4. Apply the stash safely

```bash
# Option A: Pop with conflict resolution
git stash pop
# Resolve any conflicts, then verify

# Option B: Apply without dropping (safer)
git stash apply stash@{0}
# Verify everything is correct, THEN drop
git stash drop stash@{0}
```

### 5. Verify after recovery

```bash
# Run tests immediately
pytest backend/tests/ -x --timeout=60 -q

# Check for import errors (files that shouldn't have been deleted)
python -c "import backend.app.worker"  # or key modules
```

## Key Command Reference

| Command | Purpose |
|---------|---------|
| `git diff-tree --no-commit-id -r --name-status <commit>` | Show Added/Modified/Deleted files in a commit |
| `git stash show -p stash@{N}` | Show full diff of stash contents |
| `git log --oneline stash@{N}..HEAD` | Commits between stash creation and HEAD |
| `git show <commit>:<path>` | Recover a file from a specific commit |

## Related

- **Post-merge test runner hook**: `.claude/hooks/post-merge-test-runner.py` — automatically reminds to run tests after merge operations
- **Two Scope Tables gotcha**: See `CLAUDE.md` — common source of FK errors after merges that add new models
