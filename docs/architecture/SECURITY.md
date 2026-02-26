# Security

## SSRF Prevention

Only allow requests to `github.com`. The URL parser must:
- Validate scheme is `https`
- Validate host is exactly `github.com`
- Reject any other domains, IP addresses, or redirect targets
- Reject URLs with embedded credentials (`user:pass@host`)

## Secret Management

```python
# NEVER hardcode
api_key = "sk-xxxxx"  # BAD

# ALWAYS from environment
api_key = os.environ["NEBIUS_API_KEY"]  # GOOD — fail fast if missing
```

Environment variables:
- `NEBIUS_API_KEY` — required, validated at startup (rejects placeholders like `"your-key"` and keys shorter than 20 chars; prints clean error and exits immediately)
- `GITHUB_TOKEN` — optional, sent as `Authorization: Bearer` header when present
- `NEBIUS_MODEL` — optional, overrides default model

## Binary File Safety

Two-step detection (Repomix-style). See [REPO_PROCESSING.md](REPO_PROCESSING.md) for full details.
- Skip files exceeding 200 KB hard cap
- Step 1: extension blocklist — skip before fetching (images, archives, executables, compiled)
- Step 2: content inspection — NUL byte or UTF-8 decode failure after fetching

## Input Validation

- GitHub URL must match strict regex: `https://github.com/{owner}/{repo}` (with optional `.git` or trailing `/`)
- Request body validated via Pydantic model
- Error responses never leak tracebacks or internal paths

## Rate Limiting Awareness

- GitHub unauthenticated: 60 req/hr per IP
- With `GITHUB_TOKEN`: 5,000 req/hr
- Surface clear error messages when rate-limited (403), suggest setting `GITHUB_TOKEN`
