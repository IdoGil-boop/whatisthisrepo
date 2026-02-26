"""Application configuration — env vars, constants, and model tiers."""

import logging
import os
import signal
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Logging (called once at import time; other modules use getLogger(__name__))
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
NEBIUS_API_KEY: str = os.environ["NEBIUS_API_KEY"]  # fail-fast if missing
_PLACEHOLDER_KEYS = {"your-key", "your-api-key", "test-key", "changeme", "xxx", "CHANGE_ME"}
if not NEBIUS_API_KEY or NEBIUS_API_KEY in _PLACEHOLDER_KEYS or len(NEBIUS_API_KEY) < 20:
    print(
        "\n  ERROR: NEBIUS_API_KEY is not set to a real API key.\n"
        "  Get one at https://studio.nebius.com/ and run:\n\n"
        "    export NEBIUS_API_KEY=<your-real-key>\n",
        file=sys.stderr,
    )
    # In uvicorn --reload mode, also kill the parent reloader process
    # so the terminal gets control back instead of the reloader hanging.
    try:
        import subprocess as _sp

        ppid = os.getppid()
        _r = _sp.run(["ps", "-p", str(ppid), "-o", "command="], capture_output=True, text=True)
        if "--reload" in _r.stdout and "uvicorn" in _r.stdout:
            os.kill(ppid, signal.SIGTERM)
    except Exception:
        pass
    os._exit(1)
GITHUB_TOKEN: Optional[str] = os.environ.get("GITHUB_TOKEN")
NEBIUS_MODEL: Optional[str] = os.environ.get("NEBIUS_MODEL")

# ---------------------------------------------------------------------------
# Timeouts & caps
# ---------------------------------------------------------------------------
GITHUB_TIMEOUT: int = 30
LLM_TIMEOUT: int = 60
MAX_LINES: int = 250
MAX_CHARS: int = 12_000
MAX_FILE_SIZE: int = 200 * 1024  # 200 KB
MAX_DIGEST_CHARS: int = 140_000
MAX_FILES: int = 18
MAX_CACHE_SIZE: int = 50

# ---------------------------------------------------------------------------
# Model selection tiers: (char_threshold, model_name)
# ---------------------------------------------------------------------------
MODEL_TIERS: list[tuple[int, str]] = [
    (20_000, "Meta/Llama-3.1-8B-Instruct"),
    (90_000, "Qwen3-32B"),
    (140_000, "Meta/Llama-3.3-70B-Instruct"),
]

# ---------------------------------------------------------------------------
# Ignore / skip sets
# ---------------------------------------------------------------------------
IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
        "__pycache__",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".idea",
        ".vscode",
        "coverage",
        "target",
        ".next",
        "vendor",
        "__snapshots__",
        "fixtures",
    }
)

LOCKFILES: frozenset[str] = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Pipfile.lock",
        "Cargo.lock",
    }
)

BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".pdf",
        ".zip",
        ".gz",
        ".tar",
        ".7z",
        ".mp4",
        ".mov",
        ".avi",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".jar",
        ".class",
        ".wasm",
        ".ttf",
        ".woff",
        ".woff2",
        ".eot",
        # extras from plan
        ".pyc",
        ".pyo",
        ".whl",
        ".egg",
        ".db",
        ".sqlite",
        ".mdb",
        ".pem",
        ".key",
        ".pub",
        ".log",
        ".lockb",
        ".DS_Store",
        ".map",
    }
)
