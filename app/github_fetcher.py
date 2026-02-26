"""GitHub API client — fetches repo metadata, tree, and file contents."""

from __future__ import annotations

import logging
import re

import httpx

from app.config import GITHUB_TIMEOUT, GITHUB_TOKEN
from app.models import GitHubError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared httpx client (lazy singleton)
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Return a shared httpx client, creating one if needed."""
    global _client  # noqa: PLW0603
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=GITHUB_TIMEOUT)
    return _client


async def close_client() -> None:
    """Close the shared httpx client (called on app shutdown)."""
    global _client  # noqa: PLW0603
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


_GITHUB_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.\-]+)/(?P<repo>[A-Za-z0-9_.\-]+?)(?:\.git|/)?$"
)

_API_BASE = "https://api.github.com"
_RAW_BASE = "https://raw.githubusercontent.com"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL.

    Rejects non-github.com domains and embedded credentials.
    """
    if "@" in url.split("//", 1)[-1].split("/", 1)[0]:
        raise GitHubError(400, "Invalid GitHub URL: embedded credentials not allowed")
    m = _GITHUB_URL_RE.match(url)
    if not m:
        raise GitHubError(
            400, "Invalid GitHub URL format. Expected: https://github.com/{owner}/{repo}"
        )
    return m.group("owner"), m.group("repo")


async def fetch_repo_info(owner: str, repo: str) -> dict:
    """GET /repos/{owner}/{repo} — returns description, language, default_branch, stars, forks."""
    url = f"{_API_BASE}/repos/{owner}/{repo}"
    client = await get_client()
    try:
        resp = await client.get(url, headers=_make_headers())
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise GitHubError(503, f"GitHub API unavailable: {exc}") from exc
    if resp.status_code != 200:
        raise _map_github_error(resp.status_code, owner, repo)
    data = resp.json()
    return {
        "description": data.get("description") or "Not provided",
        "language": data.get("language") or "Unknown",
        "default_branch": data.get("default_branch", "main"),
        "stargazers_count": data.get("stargazers_count", 0),
        "forks_count": data.get("forks_count", 0),
    }


async def fetch_branch_sha(owner: str, repo: str, branch: str) -> str:
    """GET /repos/{owner}/{repo}/commits/{branch} — returns commit SHA."""
    url = f"{_API_BASE}/repos/{owner}/{repo}/commits/{branch}"
    client = await get_client()
    try:
        resp = await client.get(url, headers=_make_headers())
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise GitHubError(503, f"GitHub API unavailable: {exc}") from exc
    if resp.status_code != 200:
        raise _map_github_error(resp.status_code, owner, repo)
    return resp.json()["sha"]


async def fetch_repo_tree(owner: str, repo: str, sha: str) -> list[dict]:
    """GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1 — returns blob entries only."""
    url = f"{_API_BASE}/repos/{owner}/{repo}/git/trees/{sha}?recursive=1"
    client = await get_client()
    try:
        resp = await client.get(url, headers=_make_headers())
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise GitHubError(503, f"GitHub API unavailable: {exc}") from exc
    if resp.status_code != 200:
        raise _map_github_error(resp.status_code, owner, repo)
    data = resp.json()
    if data.get("truncated"):
        logger.warning("Tree for %s/%s is truncated — some files may be missing", owner, repo)
    return [entry for entry in data.get("tree", []) if entry.get("type") == "blob"]


async def fetch_file_content(owner: str, repo: str, path: str, ref: str) -> bytes:
    """GET raw file content from raw.githubusercontent.com. Returns bytes for binary detection."""
    url = f"{_RAW_BASE}/{owner}/{repo}/{ref}/{path}"
    client = await get_client()
    try:
        resp = await client.get(url, headers=_make_headers())
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise GitHubError(503, f"GitHub API unavailable: {exc}") from exc
    if resp.status_code != 200:
        raise _map_github_error(resp.status_code, owner, repo)
    return resp.content


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _make_headers() -> dict[str, str]:
    """Build request headers, including auth if GITHUB_TOKEN is set."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _map_github_error(status_code: int, owner: str, repo: str) -> GitHubError:
    """Map HTTP status to a descriptive GitHubError."""
    if status_code == 404:
        return GitHubError(404, f"Repository not found: {owner}/{repo}")
    if status_code == 403:
        return GitHubError(
            403,
            "GitHub rate limit exceeded. Set GITHUB_TOKEN env var for higher limits.",
        )
    if status_code in {502, 503, 504}:
        return GitHubError(503, "GitHub API is currently unavailable. Try again later.")
    return GitHubError(status_code, f"GitHub API returned status {status_code}")
