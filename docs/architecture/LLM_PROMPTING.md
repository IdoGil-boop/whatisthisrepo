# LLM Prompting Strategy

## Provider

Nebius Token Factory (OpenAI-compatible):
- Base URL: `https://api.tokenfactory.nebius.com/v1/`
- SDK: OpenAI Python SDK with custom `base_url` and `api_key`

## Model Selection

**Auto-select by default.** After building the digest, measure its size and pick the cheapest model that fits:

| Digest size    | Tier   | Default model                        |
|----------------|--------|--------------------------------------|
| < 20k chars    | Small  | `Meta/Llama-3.1-8B-Instruct`        |
| < 90k chars    | Medium | `Qwen3-32B`                          |
| < 140k chars   | Large  | `Meta/Llama-3.3-70B-Instruct`       |
| > 140k chars   | —      | Compact to 140k, use Large           |

Model tiers and their context windows are defined in config. Thresholds account for overhead: system prompt (~2k tokens) + response budget (~2k tokens).

**`NEBIUS_MODEL` override:** If set, skip auto-selection and always use that model. Truncate the digest to fit the model's context window if needed.

**Hard cap: 140k chars.** If the digest exceeds this after selection, apply the compaction waterfall (see REPO_PROCESSING.md) — progressively reduce detail while preserving breadth.

## Prompt Structure

Build a single prompt with structured "REPO DIGEST" sections:

```
=== Repository: {owner}/{repo} ===
Description: {repo description or "Not provided"}
Primary Language: {language guessed by extension counts}
Stars: {count} | Forks: {count}

=== README ===
{readme content}

=== Project Configuration ===
--- pyproject.toml ---
{content}
--- Dockerfile ---
{content}

=== Directory Structure ===
{compact tree, depth=2}

=== Key Source Files ===
--- app/main.py ---
{content}
```

## System Prompt

Key instructions to the LLM:
- Output ONLY valid JSON matching the exact schema: `{"summary": "...", "technologies": [...], "structure": "..."}`
- Use only the provided repo digest — if uncertain, say "Unknown" rather than guessing
- No markdown fences, no extra keys, no commentary outside the JSON

## Parameters

- Temperature: 0.2 (low — deterministic, structured output)
- Max tokens: sufficient for response (~2,000)

## Output Validation & Retry

1. Parse the LLM response as JSON
2. Verify all required keys exist and have correct types:
   - `summary`: string
   - `technologies`: list of strings
   - `structure`: string
3. If parsing fails or keys are missing/wrong type: **one retry**
4. Retry prompt: "Your previous response was not valid JSON matching the required schema. Return ONLY valid JSON with keys: summary (string), technologies (array of strings), structure (string). No markdown, no extra keys."
5. If retry also fails: return HTTP 502 with structured error

## Primary Language Detection

Detected by `repo_processor.py` via extension counting (see [REPO_PROCESSING.md](REPO_PROCESSING.md)). Included in the prompt metadata as `Primary Language`. Supplements GitHub's own language metadata when available.
