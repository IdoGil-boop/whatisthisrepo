---
name: tdd-workflow
description: Use this skill when writing new features, fixing bugs, or refactoring code. Enforces test-driven development with 80%+ coverage including unit, integration, and E2E tests.
---

# Test-Driven Development Workflow

This skill ensures all code development follows TDD principles with comprehensive test coverage.

## When to Activate

- Writing new features or functionality
- Fixing bugs or issues
- Refactoring existing code
- Adding API endpoints
- Creating new components

## Core Principles

### 1. Tests BEFORE Code
ALWAYS write tests first, then implement code to make tests pass.

### 2. Coverage Requirements
- Minimum 80% coverage (unit + integration + E2E)
- All edge cases covered
- Error scenarios tested
- Boundary conditions verified

### 3. Test Types

#### Unit Tests
- Individual functions and utilities
- Service methods
- Pure functions
- Helpers and validators

#### Integration Tests
- API endpoints
- Database operations (SQLAlchemy sessions)
- Celery task execution
- External API calls

#### E2E Tests (Playwright)
- Critical user flows in admin-frontend
- Complete workflows
- Browser automation

## TDD Workflow Steps

### Step 1: Write User Stories
```
As a [role], I want to [action], so that [benefit]

Example:
As an optimizer, I want to score assets by ad group,
so that I can identify the worst-performing asset to replace.
```

### Step 2: Generate Test Cases
```python
class TestAssetScoring:
    def test_scores_asset_with_strong_metrics(self, db_session, sample_asset):
        """High CTR + conversions should yield high score."""
        score = calculate_score(sample_asset)
        assert score > 0.8

    def test_scores_zero_impressions_as_zero(self, db_session):
        """Assets with no impressions get score 0."""
        asset = make_asset(impressions=0)
        assert calculate_score(asset) == 0.0

    def test_handles_missing_metrics_gracefully(self, db_session):
        """Assets with NULL metrics don't crash."""
        asset = make_asset(clicks=None)
        score = calculate_score(asset)
        assert 0.0 <= score <= 1.0
```

### Step 3: Run Tests (They Should Fail)
```bash
pytest tests/test_scoring.py -v
# Tests should fail - we haven't implemented yet
```

### Step 4: Implement Code
Write minimal code to make tests pass.

### Step 5: Run Tests Again
```bash
pytest tests/test_scoring.py -v
# Tests should now pass
```

### Step 6: Refactor
Improve code quality while keeping tests green.

### Step 7: Verify Coverage
```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

## Testing Patterns

### Unit Test Pattern (pytest)
```python
import pytest
from app.analysis.scoring import calculate_score

class TestCalculateScore:
    def test_high_performance(self):
        score = calculate_score(clicks=1000, impressions=50000, conversions=50)
        assert score > 0.8

    def test_zero_impressions(self):
        score = calculate_score(clicks=0, impressions=0, conversions=0)
        assert score == 0.0

    def test_negative_values_raise(self):
        with pytest.raises(ValueError, match="negative"):
            calculate_score(clicks=-1, impressions=100, conversions=0)
```

### Integration Test Pattern (SQLAlchemy)
```python
def test_create_recommendation(db_session, sample_scope):
    rec = create_recommendation(db_session, scope=sample_scope, action="ADD")
    db_session.flush()

    assert rec.id is not None
    assert rec.status == "PENDING"
    assert len(rec.status_history) == 1

def test_approve_recommendation_updates_history(db_session, pending_recommendation):
    approve_recommendation(db_session, pending_recommendation)
    db_session.flush()

    assert pending_recommendation.status == "APPROVED"
    assert pending_recommendation.status_history[-1]["status"] == "APPROVED"
```

### E2E Test Pattern (Playwright)
```python
from playwright.sync_api import Page, expect

def test_user_can_view_recommendations(page: Page):
    page.goto("/recommendations")
    expect(page.locator("h1")).to_contain_text("Recommendations")

    # Check table has rows
    rows = page.locator("table tbody tr")
    expect(rows).to_have_count(5, timeout=5000)
```

## Test File Organization

```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_scoring.py          # Unit tests
│   ├── test_worker.py           # Worker/pipeline tests
│   ├── test_email_actions.py    # Token-based action tests
│   └── integration/
│       ├── test_pipeline_e2e.py # Full pipeline tests
│       └── test_api.py          # API endpoint tests
admin-frontend/
├── tests/
│   └── e2e/
│       ├── recommendations.spec.ts  # E2E tests
│       └── scopes.spec.ts
```

## Mocking External Services

### Mock SQLAlchemy Session
```python
from unittest.mock import MagicMock, patch

@patch("app.worker.get_db")
def test_pipeline_with_mock_db(mock_get_db, db_session):
    mock_get_db.return_value = db_session
    result = run_pipeline(scope_id=1)
    assert result.status == "SUCCESS"
```

### Mock Celery Tasks
```python
@patch("app.worker.send_email_task.delay")
def test_batch_scheduler(mock_send, db_session):
    schedule_batch(account_id=1)
    mock_send.assert_called_once()
```

### Mock LLM Provider
```python
@patch("app.generation.llm_provider.LLMProvider.generate")
def test_generation_fallback(mock_generate):
    mock_generate.side_effect = TimeoutError("LLM timeout")
    result = generate_asset_text(context)
    assert result.fallback_used is True
```

## Coverage Verification

```bash
# Run with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Coverage Thresholds (pyproject.toml)
```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"
```

## Best Practices

1. **Write Tests First** - Always TDD
2. **One Assert Per Test** - Focus on single behavior
3. **Descriptive Test Names** - `test_approve_with_expired_token_returns_410`
4. **Arrange-Act-Assert** - Clear test structure
5. **Mock External Dependencies** - Isolate unit tests
6. **Test Edge Cases** - None, empty, negative, large
7. **Test Error Paths** - Not just happy paths
8. **Keep Tests Fast** - Unit tests < 50ms each
9. **Use conftest.py** - Share fixtures across test modules
10. **flag_modified() tests** - Always test JSONB mutations write to DB

## Success Metrics

- 80%+ code coverage achieved
- All tests passing (green)
- No skipped or disabled tests
- Fast test execution (< 30s for unit tests)
- E2E tests cover critical user flows
- Tests catch bugs before production

---

**Remember**: Tests are not optional. They are the safety net that enables confident refactoring, rapid development, and production reliability.
