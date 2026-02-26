# API Specification

## POST /summarize

### Request

```json
{
  "github_url": "https://github.com/psf/requests"
}
```

| Field      | Type   | Required | Description                        |
|------------|--------|----------|------------------------------------|
| github_url | string | yes      | URL of a public GitHub repository  |

Accepted URL formats:
- `https://github.com/{owner}/{repo}`
- `https://github.com/{owner}/{repo}/`
- `https://github.com/{owner}/{repo}.git`

Any other domain or format is rejected (SSRF prevention).

### Success Response (200)

```json
{
  "summary": "**Requests** is a popular Python library for making HTTP requests...",
  "technologies": ["Python", "urllib3", "certifi"],
  "structure": "The project follows a standard Python package layout with src/requests/, tests/, docs/."
}
```

| Field        | Type     | Description                                        |
|--------------|----------|----------------------------------------------------|
| summary      | string   | Human-readable description of what the project does |
| technologies | string[] | Main technologies, languages, and frameworks used   |
| structure    | string   | Brief description of the project structure          |

### Error Responses

All errors return:
```json
{
  "status": "error",
  "message": "Description of what went wrong"
}
```

| Status | When | Example message |
|--------|------|-----------------|
| 400    | Invalid/missing github_url, non-github.com domain | `"Invalid GitHub URL format. Expected: https://github.com/{owner}/{repo}"` |
| 403    | Private repo or GitHub rate limit exceeded | `"GitHub rate limit exceeded. Set GITHUB_TOKEN env var for higher limits."` |
| 404    | Repository not found | `"Repository not found: {owner}/{repo}"` |
| 422    | Request body validation (FastAPI auto) or empty/unparseable repo | `"Repository has no summarizable content"` |
| 500    | Unexpected server error | `"Internal server error"` (no tracebacks leaked) |
| 502    | LLM API error, or invalid LLM output after retry | `"LLM failed to produce a valid summary after retry"` |
| 503    | GitHub API unavailable | `"GitHub API is currently unavailable. Try again later."` |
| 504    | Timeout fetching repo or calling LLM | `"Request timed out while fetching repository"` |

### Rate Limits

- GitHub unauthenticated: 60 requests/hour per IP
- With `GITHUB_TOKEN`: 5,000 requests/hour
- When rate-limited, error message should suggest setting `GITHUB_TOKEN`

### Timeouts

- GitHub API calls (tree + file fetches): 30s
- LLM API call: 60s
- Overall request: 90s
