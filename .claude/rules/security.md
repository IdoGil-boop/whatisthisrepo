# Security Guidelines

## Mandatory Security Checks

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (ORM only, no raw SQL without parameterized queries)
- [ ] XSS prevention (frontend frameworks escape by default; never inject raw HTML)
- [ ] CSRF protection enabled on all state-changing endpoints
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all public endpoints
- [ ] Error messages don't leak sensitive data (no tracebacks in API responses)

## Secret Management

```python
# NEVER: Hardcoded secrets
api_key = "sk-proj-xxxxx"

# ALWAYS: Environment variables via config
from app.config import settings
api_key = settings.API_KEY  # Validated at startup
```

## ORM-Specific Security

### JSONB Mutation Safety (CRITICAL)

```python
from sqlalchemy.orm.attributes import flag_modified

# After ANY in-place JSONB mutation, you MUST call flag_modified()
record.metadata.append({"status": "APPROVED"})
flag_modified(record, "metadata")  # Without this, change never writes to DB
db.commit()
```

### Row-Level Locking

```python
# Prevent race conditions on concurrent updates
row = db.query(Model).filter_by(id=row_id).with_for_update().one()
```

### Boolean/None Comparisons

```python
# CORRECT: Use .is_() / .isnot()
query.filter(Model.enabled.is_(True))
query.filter(Model.deleted_at.is_(None))

# WRONG: Ruff E712/E711 violations
query.filter(Model.enabled == True)
query.filter(Model.deleted_at != None)
```

## Task/Worker Security

- Use JSON serializer only (never pickle -- arbitrary code execution risk)
- Validate all task arguments at the start of the task function
- Never pass secrets as task arguments (fetch from config/DB inside the task)

## Security Scanning

Run before merging (adapt to your project's tooling):
- Linting -- catches unsafe patterns
- Security-specific static analysis (e.g., bandit)
- Dependency vulnerability scanner (e.g., pip-audit)
- Type checking -- type errors that hide security bugs

## Security Response Protocol

If security issue found:
1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
