# Git Workflow

## Commit Message Format

```
<type>: <description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

Examples:
- `feat: add batch email scheduler for account-level sends`
- `fix: correct data mutation persistence bug`
- `refactor: extract decision logic into single function`
- `test: add TDD coverage for token endpoints`

## Pull Request Workflow

When creating PRs:
1. Analyze FULL commit history (not just latest commit)
2. Use `git diff main...HEAD` to see all changes from branch point
3. Draft comprehensive PR summary covering all commits
4. Include test plan with specific verification steps
5. Push with `-u` flag if new branch

## Feature Implementation Workflow

### 1. Plan First
- Use **planner** agent to create implementation plan
- Identify single source of truth (check project docs)
- If logic already exists elsewhere, delegate to it -- do not create competing implementations
- Break down into phases with clear milestones

### 2. TDD Approach
- Use **tdd-guide** agent
- Write tests first (RED)
- Implement to pass tests (GREEN)
- Refactor (IMPROVE)
- Verify 80%+ coverage

### 3. Code Review
- Use **code-reviewer** or **python-reviewer** agent after writing code
- Address CRITICAL and HIGH issues immediately
- Fix MEDIUM issues when possible
- Run linters

### 4. Commit & Push
- Detailed commit messages following conventional format
- One logical change per commit
- Verify migrations are included with model changes

## Branch Naming

- `feat/short-description` -- New features
- `fix/short-description` -- Bug fixes
- `refactor/short-description` -- Code restructuring
- `chore/short-description` -- Maintenance tasks
