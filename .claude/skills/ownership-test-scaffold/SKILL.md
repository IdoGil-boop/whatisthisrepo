---
name: ownership-test-scaffold
description: Scaffold the 4 standard TDD ownership test cases for any new JWT-authenticated FastAPI endpoint. Use immediately after adding get_current_user to an endpoint to ensure cross-tenant access is blocked.
---

# Ownership Test Scaffold

Generates the four standard ownership/authorization test cases for a FastAPI endpoint that uses `get_current_user`. Enforces the pattern established in `test_scope_settings_ownership.py`.

## When to Use

- After adding `Depends(get_current_user)` to any new or existing endpoint
- When a PR review flags a missing ownership check (IDOR vulnerability)
- Before merging any endpoint that touches user-owned data

## The 4 Standard Test Cases

Every authenticated endpoint needs exactly these four cases:

| # | Name | Setup | Expected |
|---|------|-------|----------|
| 1 | **Own data — success** | User A requests User A's resource | `200 OK`, data returned |
| 2 | **Other user's data — forbidden** | User A requests User B's resource | `403 Forbidden` |
| 3 | **Non-existent resource** | Any user requests ID that doesn't exist | `404 Not Found` |
| 4 | **Unauthenticated** | No `Authorization` header | `401 Unauthorized` |

## Workflow

### Step 1 — Identify the Endpoint

Note the route, method, and the model being accessed:
- Route: `POST /recommendations/{recommendation_id}/approve`
- Model: `Recommendation` (has `user_id` FK to `users`)
- Ownership chain: `Recommendation.user_id == current_user.id`

### Step 2 — Find or Create the Test File

Check if a test file for the router already exists:
```bash
ls backend/tests/test_<router_name>*.py
```

If one exists (e.g., `test_scope_settings_ownership.py`), append to it.
If not, create `backend/tests/test_<router_name>_ownership.py`.

### Step 3 — Write the Fixture Block

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, <Model>


@pytest.fixture
async def user_a(db: AsyncSession) -> User:
    user = User(email="user_a@test.com", auth_provider="email", email_verified=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def user_b(db: AsyncSession) -> User:
    user = User(email="user_b@test.com", auth_provider="email", email_verified=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def resource_owned_by_a(db: AsyncSession, user_a: User) -> <Model>:
    """A resource that belongs to user_a."""
    item = <Model>(user_id=user_a.id, ...)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


def auth_headers(user: User) -> dict:
    """Generate a valid Bearer token header for the given user."""
    from app.routes.auth import _create_tokens
    tokens = _create_tokens(user.id, user.email)
    return {"Authorization": f"Bearer {tokens.access_token}"}
```

### Step 4 — Write the 4 Test Cases

```python
class TestEndpointOwnership:
    """Ownership checks for <METHOD> <route>."""

    async def test_own_resource_succeeds(
        self, async_client: AsyncClient, user_a: User, resource_owned_by_a: <Model>
    ):
        """User A can access their own resource."""
        resp = await async_client.post(
            f"/<route>/{resource_owned_by_a.id}/<action>",
            headers=auth_headers(user_a),
        )
        assert resp.status_code == 200

    async def test_other_users_resource_forbidden(
        self, async_client: AsyncClient, user_b: User, resource_owned_by_a: <Model>
    ):
        """User B cannot access User A's resource — must return 403, not 404."""
        resp = await async_client.post(
            f"/<route>/{resource_owned_by_a.id}/<action>",
            headers=auth_headers(user_b),
        )
        assert resp.status_code == 403

    async def test_nonexistent_resource_not_found(
        self, async_client: AsyncClient, user_a: User
    ):
        """Non-existent resource ID returns 404."""
        resp = await async_client.post(
            "/<route>/nonexistent-id-99999/<action>",
            headers=auth_headers(user_a),
        )
        assert resp.status_code == 404

    async def test_unauthenticated_request_rejected(
        self, async_client: AsyncClient, resource_owned_by_a: <Model>
    ):
        """Missing Authorization header returns 401."""
        resp = await async_client.post(
            f"/<route>/{resource_owned_by_a.id}/<action>",
        )
        assert resp.status_code == 401
```

### Step 5 — Run in RED Phase First

```bash
cd backend && pytest tests/test_<router_name>_ownership.py -v
```

All 4 tests should FAIL if the implementation is missing the ownership check. If they pass already, the endpoint was already correct.

### Step 6 — Implement the Fix

Add ownership check to the route handler:

```python
result = await db.execute(select(Model).filter(Model.id == resource_id))
item = result.scalar_one_or_none()

if not item:
    raise HTTPException(status_code=404, detail="Not found")

if item.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")
```

**Important**: 403 must come AFTER the 404 check. Returning 403 for a non-existent ID would leak existence information.

### Step 7 — Run in GREEN Phase

```bash
cd backend && pytest tests/test_<router_name>_ownership.py -v
# Expect: 4 passed
```

### Step 8 — Verify Coverage

```bash
cd backend && pytest tests/test_<router_name>_ownership.py \
  --cov=app/routes/<router_name> --cov-report=term-missing
```

## Ownership Chain Patterns

Not all models have a direct `user_id`. Some require multi-hop ownership:

**Direct ownership** (most common):
```python
if item.user_id != current_user.id:
    raise HTTPException(status_code=403)
```

**Via account** (e.g., `ConnectedAccount`):
```python
account = await db.get(ConnectedAccount, item.account_id)
if account.user_id != current_user.id:
    raise HTTPException(status_code=403)
```

**Via scope → account** (used in `scope_settings.py`):
```python
scope = await db.get(OptimizationScope, item.linked_scope_id)
account = await db.get(ConnectedAccount, scope.account_id)
if account.user_id != current_user.id:
    raise HTTPException(status_code=403)
```

## Project Reference

- **Existing example**: `backend/tests/test_scope_settings_ownership.py` — 8 tests for context-item and guardrail-rule DELETE endpoints. Template for the above pattern.
- **Gotcha doc**: `docs/reference/COMMON_GOTCHAS.md` — "JWT Endpoint Ownership" section
- **Auth dependency**: `backend/app/deps.py:get_current_user`
