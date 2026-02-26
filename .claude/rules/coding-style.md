# Coding Style

## Naming Conventions (PEP 8)

```python
# snake_case: functions, variables, module names
def calculate_score(item_id: int) -> float: ...
total_count = 0

# PascalCase: classes, exceptions
class ItemConfig: ...
class InvalidItemError(Exception): ...

# UPPER_SNAKE_CASE: constants, settings
MAX_RETRIES = 5
DEFAULT_TIMEOUT_SECONDS = 30
```

## File Organization

MANY SMALL MODULES > FEW LARGE MODULES:
- Target 200-400 lines per module
- Hard maximum: 800 lines (extract before exceeding)
- Organize by feature/domain, not by type
- One class per file for complex models; group related small classes

## Immutability Patterns

Prefer creating new objects over in-place mutation:

```python
# GOOD: Frozen dataclass
from dataclasses import dataclass

@dataclass(frozen=True)
class ScoreResult:
    item_id: int
    score: float
    confidence: float

# GOOD: NamedTuple for lightweight records
from typing import NamedTuple

class ItemCandidate(NamedTuple):
    text: str
    source_id: int
    score: float
```

## Error Handling

```python
# GOOD: Specific exceptions with context
raise ValueError(f"Item {item_id} not found in group {group_id}")

# GOOD: Catch specific exceptions
try:
    result = client.query(query)
except ClientError as exc:
    logger.error("API error", exc_info=exc, extra={"account_id": account_id})
    raise

# BAD: Bare except
try:
    something()
except:
    pass
```

## Logging (No print Statements)

```python
import logging

logger = logging.getLogger(__name__)

# GOOD: Structured logging with context
logger.info("Processing complete", extra={"account_id": account_id, "items_processed": count})

# BAD: print() -- never in production code
print(f"Processing complete for {account_id}")
```

## Type Hints

All public functions MUST have type hints:

```python
def select_item(
    db: Session,
    scope_id: int,
    *,
    exclude_ids: set[int] | None = None,
) -> Item | None:
```

## Code Quality Checklist

Before marking work complete:
- [ ] Code is readable and well-named (PEP 8)
- [ ] Functions are small (<50 lines, single responsibility)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels -- extract helper functions)
- [ ] Proper error handling (no bare except, no silent swallowing)
- [ ] No print statements (use `logging`)
- [ ] No hardcoded values (use config or constants)
- [ ] Type hints on all public functions
- [ ] Linters pass
