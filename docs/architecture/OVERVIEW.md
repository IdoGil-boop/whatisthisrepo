# Architecture Overview

## Request Flow

```
Client → POST /summarize
  → Validate GitHub URL (models.py)
  → Fetch repo info for current branch SHA (github_fetcher.py)
  → Cache check: SHA unchanged? → return cached response
  → SHA changed or no cache? →
      → Fetch new tree, diff against cached tree
      → Re-fetch only changed/added files (repo_processor.py)
      → Reuse cached content for unchanged files
      → Generate summary via LLM (llm_client.py)
      → Cache result (SHA + tree + file contents + response)
  → First request (no cache) → full fetch as normal
```

## Component Responsibilities

### main.py — FastAPI Application
- Single endpoint: `POST /summarize`
- Orchestrates the fetch → process → summarize pipeline
- Error handling middleware for consistent error responses

### models.py — Data Models
- `SummarizeRequest`: Pydantic model with github_url validation (strict regex)
- `SummarizeResponse`: summary, technologies, structure
- `ErrorResponse`: status + message

### github_fetcher.py — GitHub API Client
- `parse_github_url(url)`: Validates and extracts owner/repo. SSRF prevention: allowlist `github.com` only
- `fetch_repo_info(owner, repo)`: Gets repo metadata (description, language, default branch)
- `fetch_repo_tree(owner, repo)`: Gets full recursive file tree via Git Trees API (`GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1`) — single call for entire directory listing
- `fetch_file_content(owner, repo, path)`: Gets raw file content for selected files only
- Uses a shared httpx async client singleton (lazy-initialized, closed on shutdown) with timeout and transport error handling
- Sends `Authorization: Bearer` header when `GITHUB_TOKEN` is set

### repo_processor.py — Content Selection & Assembly
- Core intelligence. See [REPO_PROCESSING.md](REPO_PROCESSING.md) for full strategy.
- Receives the tree, applies ignore/skip rules, detects binaries by extension
- Prioritizes files by 10-tier ranking, selects which to fetch
- Fetches only selected files (not the whole repo)
- Computes extension counts for primary language detection
- Generates compact directory tree summary (depth=2)
- Applies compaction waterfall if digest exceeds model's context budget
- Raises `EmptyRepoError` if no parseable files remain after filtering

### llm_client.py — Nebius Token Factory Client
- OpenAI SDK with `base_url="https://api.tokenfactory.nebius.com/v1/"` and `api_key` from env
- Auto-selects model tier by digest size (small/medium/large). `NEBIUS_MODEL` overrides. See [LLM_PROMPTING.md](LLM_PROMPTING.md).
- System prompt enforces strict JSON-only output
- Parses and validates LLM output against schema
- One retry with repair instruction on invalid JSON
- Guards against empty response choices from the API
- Wraps OpenAI SDK errors (`APIError`, `APITimeoutError`) into `LLMError`
- Temperature 0.2 for deterministic output

### config.py — Configuration
- `NEBIUS_API_KEY` (required — fail fast at startup if missing)
- `GITHUB_TOKEN` (optional — higher GitHub rate limits)
- `NEBIUS_MODEL` (optional — override default model)
- Content caps and timeout constants

## Error Propagation

Each component raises typed exceptions:
- `GitHubError(status_code, message)` → mapped to 400/403/404/503
- `LLMError(message)` → mapped to 502
- `EmptyRepoError(message)` → mapped to 422 (empty repo or no parseable files after filtering)
- `ProcessingError(message)` → mapped to 500
- Timeouts → mapped to 504

main.py catches these and returns structured `ErrorResponse`.

## Caching & Incremental Updates

Cache key: `owner/repo`. Cached value: branch SHA, file tree, fetched file contents, LLM response.

- **Cache hit (same SHA):** Return cached response immediately. No tree fetch, no file fetches, no LLM call.
- **Cache miss (new SHA):** Diff the cached tree against the new tree. Only re-fetch files that were added or modified (different blob SHA). Reuse cached content for unchanged files. Rebuild digest and re-run LLM. Update cache.
- **No cache entry:** Full fetch — tree, selected files, LLM call. Store in cache.

Storage: in-memory bounded cache (no external dependency). Maximum 50 entries; oldest entry evicted (FIFO) when full. Branch SHA used for invalidation — freshness ensured by checking SHA on every request.

## Security

See [SECURITY.md](SECURITY.md) for SSRF prevention, binary safety, and secret management.
