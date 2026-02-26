# repo-explorer

Generates or refreshes the `CODE_CONTEXT` knowledge map inside `docs/tools/architecture-map.html` by reading real source files and extracting entry points, call chains, gotchas, and git activity.

## Quick commands

| Command | What it does |
|---|---|
| `/architecture-map` | Open the map as-is (fast) |
| `/update-architecture-map` | Refresh git badges from last 21 days → open |
| `bash docs/tools/update-architecture-map.sh` | Same as above, from terminal |

## When to use this skill (full refresh)

- After adding a new module, route, or Celery task that should appear as a node in the architecture map
- When the playground's code context feels stale (function signatures changed, files moved)
- When git badges only need refreshing, use `/update-architecture-map` instead (faster — no Claude needed)

## What it produces

An updated `CODE_CONTEXT` block in `docs/tools/architecture-map.html` containing, per node:

```js
'node-id': {
  entry: 'path/to/file.py:FunctionName()',
  callchain: `// pseudo-code showing real execution path
entryFn(args)
  → dependency1.fn()   # file.py
  → dependency2.fn()   # other.py`,
  gotchas: 'JSONB needs flag_modified(); ID is SHA-256 not int; etc.',
},
```

## Steps

### 1. Identify stale nodes

```bash
# Find files changed since last map refresh
git log --since=30days --name-only --pretty=format:"" | sort -u
```

Compare against existing `CODE_CONTEXT` node subtitles — find which file paths no longer match reality.

### 2. Read source for each stale node

For each node that needs updating, read the relevant files:

```
Read backend/app/<module>/<file>.py   (entry function + key callees)
Grep for function signatures (def <entry_fn>, class <ClassName>)
Read imports to map the call graph
```

Key patterns to extract:
- **Entry**: the public function/class that the node represents
- **Call chain**: follow 2-3 levels deep, note which file each callee lives in
- **Gotchas**: SQLAlchemy patterns (flag_modified, with_for_update), enum types, ID types (str vs int), security checks

### 3. Refresh git activity

```bash
git log --since=21days --name-only --pretty=format:"" | sort | uniq -c | sort -rn
```

Map file paths to node IDs using this lookup:

| File pattern | Node ID(s) |
|---|---|
| `worker.py` | task-sync, task-digest, task-apply |
| `recommendations/pipeline.py` | eng-guard |
| `analysis/bayesian*.py` | eng-score |
| `analysis/worst_asset*.py` | eng-select |
| `analysis/best_asset*.py` | eng-select |
| `generation/` | eng-gen |
| `recommendations/applier.py` | task-apply |
| `recommendations/promoter.py` | task-apply, db-recs |
| `models_scope_layers.py` | db-scopes |
| `models.py` | db-users, db-ads, db-recs |
| `routes/assets.py` `routes/asset_suggestions.py` | api-assets |
| `routes/scopes_api.py` `routes/scope_settings.py` | api-scopes |
| `routes/email_actions.py` `digests/sender.py` | api-digests, task-digest |
| `routes/auth*.py` `deps.py` | api-auth |
| `google_ads/` | ext-google, task-sync |
| `generation/llm_provider.py` `generation/prompt_distiller.py` | ext-llm |
| `email/service.py` | ext-email |
| `admin-frontend/app/` | fe-* nodes |

### 4. Update the HTML file

Open `docs/tools/architecture-map.html` and update:

1. `GIT_ACTIVITY` constant (top of `<script>`) — new commit counts, update generated date comment
2. `CODE_CONTEXT` entries for changed nodes — new entry, callchain, gotchas
3. If a node's file path changed: update its `subtitle` in `NODES` array

### 5. Add new nodes (if needed)

When a new module/route/task is added:

1. Add to `NODES` array with correct `layer`, `x`/`y` position, `subtitle`, `desc`
2. Add connections to `CONNECTIONS` array
3. Add to `CODE_CONTEXT` map
4. Add to `GIT_ACTIVITY` if relevant files exist

Node layers:
- `frontend` — Next.js pages/components in `admin-frontend/`
- `api` — FastAPI routes in `backend/app/routes/`
- `logic` — Celery tasks and analysis pipeline in `backend/app/`
- `data` — SQLAlchemy models and Redis
- `external` — Google Ads API, OpenAI, Email

### 6. Open and verify

```bash
open docs/tools/architecture-map.html
```

Check: new nodes visible, git badges appear on hot components, CODE_CONTEXT prompt includes correct function signatures.

## Gotchas

- `GIT_ACTIVITY` values are raw commit counts — several files can map to the same node (add them together)
- `Recommendation.id` is a 64-char hex SHA-256 string, not int — `db-recs` node subtitle says this
- `Scope.config` is JSONB — always mention `flag_modified()` in the gotchas for any data node touching scopes
- Node positions (`x`, `y`) are in the SVG coordinate space (0–1450 × 0–640) — keep within band Y ranges to stay in the correct layer
