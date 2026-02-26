---
name: coding-standards
description: Python coding standards. PEP 8, type hints, ORM conventions, linter configuration, and universal quality principles.
---

# Coding Standards & Best Practices

## Code Quality Principles

### 1. Readability First
- Code is read more than written
- Clear variable and function names
- Self-documenting code preferred over comments
- Consistent formatting (enforced by linters)

### 2. KISS (Keep It Simple, Stupid)
- Simplest solution that works
- Avoid over-engineering
- No premature optimization
- Easy to understand > clever code

### 3. DRY (Don't Repeat Yourself)
- Extract common logic into functions
- Delegate to single source of truth
- Share utilities across modules
- Avoid copy-paste programming

### 4. YAGNI (You Aren't Gonna Need It)
- Do not build features before they are needed
- Avoid speculative generality
- Add complexity only when required
- Start simple, refactor when needed

## Python Naming Conventions (PEP 8)

```python
# Variables and functions: snake_case
search_query = "example"
is_authenticated = True

def fetch_data(item_id: str) -> dict: ...
def calculate_score(item: Item) -> float: ...
def is_valid(scope: Scope) -> bool: ...

# Classes: PascalCase
class DataProcessor: ...
class ItemConfig: ...

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
DEBOUNCE_DELAY_MS = 500

# Private: leading underscore
def _build_prompt(context: dict) -> str: ...
_internal_cache: dict[str, Any] = {}

# Module-level dunder: double underscores
__all__ = ["DataProcessor", "ItemConfig"]
```

## Type Hints

```python
# ALWAYS annotate function signatures
def select_item(
    items: list[Item],
    exclude_ids: set[int] | None = None,
) -> Item | None:
    """Select an item from the list."""
    ...

# Use modern syntax (Python 3.10+)
def process(items: list[str]) -> dict[str, int]: ...
value: int | None = None

# Frozen dataclasses for immutable value objects
from dataclasses import dataclass

@dataclass(frozen=True)
class ScoringResult:
    item_id: int
    score: float
    confidence: float
```

## Error Handling

```python
# GOOD: Specific exceptions with chaining
def load_config(config_id: int, db: Session) -> Config:
    try:
        config = db.query(Config).filter_by(id=config_id).one()
        return config
    except NoResultFound as e:
        raise ValueError(f"No config for id {config_id}") from e

# GOOD: Early returns to reduce nesting
def decide_action(scope, items, config) -> Action:
    if not items:
        return Action.NOOP
    if has_capacity(items):
        return Action.ADD
    if quota_available(scope, config):
        return Action.REPLACE
    return Action.NOOP

# BAD: Bare except
try:
    risky_operation()
except:  # Never do this
    pass
```

## Comments & Documentation

```python
# GOOD: Explain WHY, not WHAT
# Use exponential backoff to avoid overwhelming the API during outages
delay = min(1000 * (2 ** retry_count), 30000)

# BAD: Stating the obvious
count += 1  # Increment counter

# Docstrings for public APIs
def select_item(
    items: list[Item],
    exclude_ids: set[int] | None = None,
) -> Item | None:
    """Select an item based on scoring criteria.

    Args:
        items: Pre-computed item scores.
        exclude_ids: Item IDs to skip.

    Returns:
        The selected item, or None if no candidates.
    """
```

## Tooling Configuration

```bash
# Linting and formatting
# ruff check src/
# ruff format src/

# Type checking
# mypy src/

# Testing
# pytest tests/ --cov=src --cov-report=term-missing

# Security
# bandit -r src/
# pip-audit
```

## Anti-Patterns to Avoid

```python
# BAD: Mutable default arguments
def process(items=[]):  # Shared across calls!
    items.append("x")

# GOOD: Use None sentinel
def process(items: list[str] | None = None):
    if items is None:
        items = []
    items.append("x")

# BAD: from module import *
from os.path import *

# GOOD: Explicit imports
from os.path import join, exists

# BAD: Magic numbers
if retry_count > 3: ...

# GOOD: Named constants
MAX_RETRIES = 3
if retry_count > MAX_RETRIES: ...
```

---

**Remember**: Code quality is not negotiable. Clear, maintainable code enables rapid development and confident refactoring.
