---
name: security-review
description: Security checklist and patterns for Python/SQLAlchemy/Celery backend. Covers OWASP top risks, task security, JSONB mutation safety, and dependency auditing.
---

# Security Review Skill

Ensures all code follows security best practices for Python/SQLAlchemy/Celery stacks.

## When to Activate

- Implementing authentication or authorization
- Handling user input in API endpoints
- Creating new API routes
- Working with secrets, tokens, or credentials
- Modifying task definitions
- Storing or transmitting sensitive data
- Mutating JSONB columns

## Security Checklist

### 1. Secrets Management

```python
# NEVER hardcode secrets
api_key = "sk-proj-xxxxx"  # BAD

# ALWAYS use config/environment
from app.config import settings
api_key = settings.API_KEY  # GOOD
```

#### Verification Steps
- [ ] No hardcoded API keys, tokens, or passwords in source
- [ ] All secrets loaded via config or env vars
- [ ] `.env` / `.env.local` in `.gitignore`
- [ ] No secrets in git history

### 2. Input Validation

```python
from pydantic import BaseModel, Field, EmailStr

class CreateItemRequest(BaseModel):
    account_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
```

### 3. SQL Injection Prevention

```python
# NEVER concatenate user input into queries
query = f"SELECT * FROM users WHERE email = '{user_email}'"  # BAD

# ALWAYS use ORM or parameterized queries
user = db.query(User).filter(User.email == user_email).first()  # GOOD

from sqlalchemy import text
result = db.execute(text("SELECT * FROM users WHERE email = :email"),
                    {"email": user_email})  # GOOD
```

### 4. JSONB Mutation Safety

```python
from sqlalchemy.orm.attributes import flag_modified

# CRITICAL: SQLAlchemy does not detect in-place JSONB mutations
record.history.append({"status": "APPROVED"})
flag_modified(record, "history")  # REQUIRED
db.commit()
```

### 5. Task Security

```python
# ALWAYS use JSON serializer (not pickle)
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]

# ALWAYS set task timeouts
@celery_app.task(soft_time_limit=300, time_limit=600)
def process(item_id: int):
    ...
```

### 6. Authentication & Authorization

```python
@router.post("/actions/{token}")
def handle_action(token: str, db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    rec = db.query(Model).filter_by(id=payload["id"]).with_for_update().first()
    ...
```

### 7. Sensitive Data Exposure

```python
# NEVER log sensitive data
logger.info("OAuth token: %s", token)  # BAD
logger.info("User authenticated: account_id=%s", account_id)  # GOOD
```

### 8. Dependency Security

```bash
# Check for vulnerabilities
pip-audit
bandit -r src/
pip list --outdated
```

## Pre-Deployment Security Checklist

- [ ] **Secrets**: All in env vars / config, none hardcoded
- [ ] **Input Validation**: All endpoints use validation models
- [ ] **SQL Injection**: All queries parameterized / ORM-based
- [ ] **JSONB Safety**: All mutations use `flag_modified()`
- [ ] **Tasks**: JSON serializer only, timeouts set
- [ ] **Authentication**: Tokens validated, single-use enforced
- [ ] **Rate Limiting**: Enabled on public endpoints
- [ ] **Logging**: No sensitive data in logs
- [ ] **Dependencies**: Audit tools clean
- [ ] **HTTPS**: Enforced in production
- [ ] **CORS**: Properly configured
- [ ] **Error Handling**: Generic messages to users, detailed in server logs

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/sessions.html)
- [Celery Security](https://docs.celeryq.dev/en/stable/userguide/security.html)
- [Bandit Documentation](https://bandit.readthedocs.io/)

---

**Remember**: Security is not optional. When in doubt, err on the side of caution.
