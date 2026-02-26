# Testing Requirements

## Minimum Test Coverage: 80%

Test types (ALL required for new features):
1. **Unit Tests** -- Individual functions, utilities, model methods
2. **Integration Tests** -- API endpoints, DB operations
3. **E2E Tests** -- Critical user flows (Playwright)

## Test-Driven Development

MANDATORY workflow for new features and bug fixes:
1. Write test first (RED)
2. Run test -- it should FAIL
3. Write minimal implementation (GREEN)
4. Run test -- it should PASS
5. Refactor (IMPROVE)
6. Verify coverage

## pytest Patterns

### Fixtures & conftest.py

```python
# tests/conftest.py -- shared fixtures
@pytest.fixture
def db_session():
    """Provide a transactional DB session that rolls back after each test."""

@pytest.fixture
def sample_account(db_session):
    """Create a test account with default config."""

@pytest.fixture
def authenticated_client(client, sample_account):
    """Client with valid auth headers."""
```

### Test Organization

```
tests/
  conftest.py              # Shared fixtures, DB session, factories
  test_*.py                # Unit tests (parallel to source modules)
  integration/             # Multi-component integration tests
tests/e2e/                 # Playwright E2E tests (Page Object Model)
```

## Troubleshooting Test Failures

1. Use **tdd-guide** agent for structured debugging
2. Check test isolation (shared DB state leaking between tests)
3. Verify fixtures provide clean state (rollback, not truncate)
4. Fix implementation, not tests (unless tests are wrong)
5. For flaky tests: check for ordering dependencies, missing flushes

## Agent Support

- **tdd-guide** -- Use PROACTIVELY for new features; enforces write-tests-first
- **e2e-runner** -- Playwright E2E testing specialist
- **python-reviewer** -- Catches untested edge cases during review
