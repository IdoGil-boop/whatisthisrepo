# Repo Processing Strategy

## Goal

Select the most informative files from a repository to fit within the LLM's context window, giving the model the best possible understanding of the project.

## Caps

- **Total digest cap:** determined by selected model's context window (see [LLM_PROMPTING.md](LLM_PROMPTING.md) for model selection tiers). Hard maximum: 140k chars.
- **Per-file excerpt cap:** 250 lines OR 12,000 chars (whichever smaller)
- **Per-file size hard cap:** 200 KB (skip files larger than this)
- **Max included files:** 12–18 total (including configs)

## Ignored Directories

Always skip entirely:
`.git`, `node_modules`, `dist`, `build`, `.venv`, `venv`, `__pycache__`, `.tox`, `.mypy_cache`, `.pytest_cache`, `.idea`, `.vscode`, `coverage`, `target`, `.next`, `vendor`, `__snapshots__`, `fixtures`

## Skipped Files

### Lockfiles (noisy, low signal)
`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`, `Cargo.lock`

### Binary detection (two-step, Repomix-style)

**Step 1 — Extension check (before fetching content):**
Skip immediately if extension matches a known binary type. Skip reason: `binary-extension`.
`png`, `jpg`, `jpeg`, `gif`, `webp`, `svg`, `ico`, `pdf`, `zip`, `gz`, `tar`, `7z`, `mp4`, `mov`, `avi`, `exe`, `dll`, `so`, `dylib`, `jar`, `class`, `wasm`, `ttf`, `woff`, `woff2`, `eot`, `min.js`, `min.css`, `pb.go`, `generated.*`, `snap`

**Step 2 — Content inspection (after fetching):**
Read file into buffer and inspect. Skip reason: `binary-content`.
- Contains NUL byte (`\x00`) → binary
- Fails UTF-8 decode → binary

Binary files are still included in the directory tree summary (paths visible, contents excluded).

## Priority Order (first to drop → last to drop)

Single ranked list. Compaction and dropping work from the top down.

| Rank | Category | Files |
|------|----------|-------|
| 10 (lowest) | Extra source files | Small representative files from src/lib |
| 9 | Config/types | `types.ts`, `models.py`, `schema.*`, `config.*` |
| 8 | Core modules | Files in `src/` or `lib/` root (not deeply nested) |
| 7 | API definitions | `routes/`, `api/`, `endpoints/`, `urls.py`, `openapi.*` |
| 6 | Entry points | `main.py`, `app.py`, `src/index.*`, `server.*`, `cmd/*/main.go` |
| 5 | CI configs | `.github/workflows/*.yml` (cap at first workflow, excerpted) |
| 4 | Secondary configs | `Dockerfile`, `docker-compose.yml`, `Makefile`, `.gitignore` |
| 3 | Primary manifest | `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, etc. |
| 2 | Agent docs | `CLAUDE.md`, `.cursorrules`, `.cursorules`, `AGENTS.md`, `CONVENTIONS.md`, `copilot-instructions.md` |
| 1 (highest) | README | `README.md`, `README.rst`, `README.txt`, `README` |

Within source files (ranks 6–10): prefer shortest path depth (`src/app.py` over `src/utils/helpers/format.py`). Max 2–4 entrypoint files, fill remaining budget with small representative files.

Agent docs often contain the richest project documentation — architecture, conventions, and design decisions that may not appear in the README.

## Compaction Waterfall

Applied progressively until digest fits the model's context budget. Favors breadth over depth.

1. **Truncate oversized files** — per-file cap (250 lines / 12k chars), append `\n... [truncated]`
2. **Reduce tree depth** — show top 2 levels only, append count of remaining
3. **Halve source excerpts** — cut per-file cap to 125 lines / 6k chars (ranks 6–10 only)
4. **Signatures only** — for source files, keep imports + function/class signatures, drop bodies
5. **Drop files by rank** — remove from rank 10 upward
6. **Compact agent docs** (rank 2) — truncate to per-file cap
7. **Compact README** (rank 1) — last resort, truncate to per-file cap

## Primary Language Detection

Count file extensions across the discovered tree:
- `.py` → Python, `.js`/`.ts` → JavaScript/TypeScript, `.go` → Go, `.rs` → Rust, `.java` → Java, `.rb` → Ruby
- Report the most frequent as primary language in the digest metadata

**Note:** Use `fnmatch` or `pathlib` for glob matching — never `str.endswith()` with wildcard patterns like `"*.md"`.
