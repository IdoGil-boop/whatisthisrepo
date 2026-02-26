# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GitHub Repo Summarizer** — A Python API service that takes a GitHub repository URL and returns a human-readable summary of what the project does, its technologies, and structure. Uses an LLM (Nebius Token Factory) to generate the summary from intelligently selected repo contents.

## Quick Reference

See [README.md](README.md) for setup, environment variables, and usage examples.

```bash
# Run
NEBIUS_API_KEY=your-key uvicorn app.main:app --reload --port 8000

# Test
pytest

# Lint
ruff check . && ruff format --check .
```

## Architecture

See [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md) for full architecture.

```
app/
├── main.py              # FastAPI app, /summarize endpoint
├── models.py            # Pydantic request/response models
├── github_fetcher.py    # GitHub API client — fetches repo tree + file contents
├── repo_processor.py    # Filters, prioritizes, and assembles repo content for LLM
├── llm_client.py        # Nebius Token Factory client + prompt + JSON validation
└── config.py            # Settings (env vars, constants)
tests/
├── test_main.py         # Endpoint integration tests
├── test_github_fetcher.py
├── test_repo_processor.py
└── test_llm_client.py
```

## Documentation Index

- [README.md](README.md) — setup, env vars, usage, design decisions
- [Architecture Overview](docs/architecture/OVERVIEW.md) — request flow, component responsibilities
- [Repo Processing Strategy](docs/architecture/REPO_PROCESSING.md) — file selection, priority ranking, compaction
- [LLM Prompting Strategy](docs/architecture/LLM_PROMPTING.md) — prompt structure, validation, retry
- [Security](docs/architecture/SECURITY.md) — SSRF prevention, binary safety, secrets
- [API Specification](docs/spec/API_SPEC.md) — endpoint contract, error codes, timeouts

## Key Design Decisions

1. **Fetching strategy:** Git Trees API for file listing + selective raw content fetches. Only downloads files we actually need. See [OVERVIEW.md](docs/architecture/OVERVIEW.md).

2. **File selection:** Priority-based with budget caps. See [REPO_PROCESSING.md](docs/architecture/REPO_PROCESSING.md).

3. **Model selection:** Auto-select cheapest model that fits the digest. Small repos get a fast model, large repos get a large-context model. `NEBIUS_MODEL` overrides with truncation. See [LLM_PROMPTING.md](docs/architecture/LLM_PROMPTING.md).

4. **Caching:** In-memory cache keyed by `owner/repo`. Branch SHA used for invalidation — if SHA unchanged, return cached response. On change, diff trees and re-fetch only modified files. See [OVERVIEW.md](docs/architecture/OVERVIEW.md).

5. **Error handling:** All errors return structured JSON. See [API_SPEC.md](docs/spec/API_SPEC.md).

## Conventions

- Async everywhere (FastAPI async endpoints, httpx async client)
- Pydantic models for all request/response schemas
- Structured logging (no print statements)
- Type hints on all functions
- Keep files under 200 lines; split if larger
- Use `fnmatch`/`pathlib` for glob matching, never `str.endswith()` with wildcards
