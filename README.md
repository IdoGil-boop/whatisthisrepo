# GitHub Repo Summarizer

An API service that takes a GitHub repository URL and returns an AI-generated summary of the project — what it does, its technologies, and structure.

## Setup

```bash
# Clone and enter directory
git clone <repo-url> && cd <repo-dir>

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

| Variable         | Required | Description                                      |
|------------------|----------|--------------------------------------------------|
| `NEBIUS_API_KEY` | Yes      | Nebius AI Studio API key                         |
| `GITHUB_TOKEN`   | No       | GitHub personal access token (raises rate limit from 60 to 5,000 req/hr) |
| `NEBIUS_MODEL`   | No       | Override LLM model name (default: auto-selected by digest size; see tiers below) |

## Run

```bash
export NEBIUS_API_KEY=<your-real-key>  # get one at https://studio.nebius.com/
uvicorn app.main:app --reload --port 8000
```

## Example Request

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

### Success Response

```json
{
  "summary": "Requests is a popular Python HTTP library...",
  "technologies": ["Python", "urllib3", "certifi"],
  "structure": "Standard Python package layout with src/requests/, tests/, docs/."
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Repository not found: psf/nonexistent"
}
```

## Test

```bash
pytest                        # all tests
pytest tests/ -k "test_name"  # single test
pytest tests/ -v              # verbose
```

## Lint

```bash
ruff check . && ruff format --check .
```

## Design Decisions

### 1. Fetching — only download what we need

We use GitHub's Git Trees API to get the full file listing in a single call, then fetch only the files we've selected. This avoids downloading the entire repo (which could be hundreds of MB for large projects) and means we never transfer binaries, vendored code, or build artifacts.

### 2. File selection — a 10-tier priority system

Not all files are equally useful for understanding a project. We rank files into 10 priority tiers: README is highest (it's the author's own description), followed by AI agent docs (CLAUDE.md, .cursorrules — often the best-documented part of modern repos), then manifests (package.json, pyproject.toml), and finally source files (entry points first, then API definitions, then core modules). Binary files are detected in two steps: first by extension (before fetching), then by content inspection (after fetching). We cap at 12–18 files total.

### 3. Context management — fit the model to the repo, not the other way around

Instead of cramming every repo into one model's context window, we auto-select the cheapest model that fits: Llama-3.1-8B for small repos (< 20k chars), Qwen3-32B for medium (< 90k), Llama-3.3-70B for large (< 140k). For repos that exceed 140k chars even after selection, a compaction waterfall progressively reduces detail while keeping breadth: first halve source excerpts, then keep only function signatures, then drop lowest-ranked files. README and agent docs are never dropped.

### 4. Caching — SHA-based with incremental updates

Every Git commit has a unique SHA hash. We cache results keyed by repo + branch SHA — if the SHA hasn't changed, the repo hasn't changed, so we return the cached response instantly (no tree fetch, no file fetches, no LLM call). When the SHA does change, we diff the old and new trees and only re-fetch files whose content actually changed, reusing cached content for everything else.

### 5. LLM output — strict JSON with retry

We use Nebius AI Studio (`https://api.studio.nebius.com/v1/`) with low temperature (0.2) for deterministic output. The prompt enforces a strict JSON-only contract matching our response schema. If the LLM returns invalid JSON, we retry once with a repair instruction. If that also fails, we return a 502 error rather than passing bad data to the user.

### 6. Error handling — no silent failures

Every failure mode returns a structured JSON error with an appropriate HTTP status code: invalid URL (400), private repo or rate limit (403, with a message suggesting `GITHUB_TOKEN`), repo not found (404), empty repo with no parseable files (422), GitHub API down (503), timeouts (504). URLs are validated against a strict github.com allowlist to prevent SSRF.

## Tech Stack

- Python 3.10+, FastAPI, Uvicorn
- httpx (async HTTP), OpenAI SDK (Nebius-compatible)
- pytest + pytest-asyncio, ruff
