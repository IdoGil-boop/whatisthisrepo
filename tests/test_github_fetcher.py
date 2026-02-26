"""Tests for app.github_fetcher — URL parsing, SSRF rejection, mocked API calls."""

from __future__ import annotations

import logging

import httpx
import pytest

from app.models import GitHubError

# ---------------------------------------------------------------------------
# parse_github_url
# ---------------------------------------------------------------------------


class TestParseGithubUrl:
    """URL parsing and SSRF prevention."""

    def test_valid_plain(self) -> None:
        from app.github_fetcher import parse_github_url

        assert parse_github_url("https://github.com/psf/requests") == ("psf", "requests")

    def test_valid_trailing_slash(self) -> None:
        from app.github_fetcher import parse_github_url

        assert parse_github_url("https://github.com/psf/requests/") == ("psf", "requests")

    def test_valid_dot_git(self) -> None:
        from app.github_fetcher import parse_github_url

        assert parse_github_url("https://github.com/psf/requests.git") == ("psf", "requests")

    def test_rejects_other_domain(self) -> None:
        from app.github_fetcher import parse_github_url

        with pytest.raises(GitHubError, match="Invalid GitHub URL"):
            parse_github_url("https://gitlab.com/user/repo")

    def test_rejects_embedded_creds(self) -> None:
        from app.github_fetcher import parse_github_url

        with pytest.raises(GitHubError, match="Invalid GitHub URL"):
            parse_github_url("https://token@github.com/user/repo")

    def test_rejects_http_scheme(self) -> None:
        from app.github_fetcher import parse_github_url

        with pytest.raises(GitHubError, match="Invalid GitHub URL"):
            parse_github_url("http://github.com/user/repo")

    def test_rejects_missing_repo(self) -> None:
        from app.github_fetcher import parse_github_url

        with pytest.raises(GitHubError, match="Invalid GitHub URL"):
            parse_github_url("https://github.com/user")

    def test_rejects_empty(self) -> None:
        from app.github_fetcher import parse_github_url

        with pytest.raises(GitHubError, match="Invalid GitHub URL"):
            parse_github_url("")


# ---------------------------------------------------------------------------
# fetch_repo_info
# ---------------------------------------------------------------------------


class TestFetchRepoInfo:
    """Mocked GitHub API calls for repo info."""

    async def test_success(self, httpx_mock) -> None:
        from app.github_fetcher import fetch_repo_info

        httpx_mock.add_response(
            url="https://api.github.com/repos/psf/requests",
            json={
                "description": "A simple HTTP library",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 50000,
                "forks_count": 9000,
            },
        )
        info = await fetch_repo_info("psf", "requests")
        assert info["description"] == "A simple HTTP library"
        assert info["default_branch"] == "main"

    async def test_404_raises(self, httpx_mock) -> None:
        from app.github_fetcher import fetch_repo_info

        httpx_mock.add_response(
            url="https://api.github.com/repos/no/exist",
            status_code=404,
        )
        with pytest.raises(GitHubError) as exc_info:
            await fetch_repo_info("no", "exist")
        assert exc_info.value.status_code == 404

    async def test_403_raises(self, httpx_mock) -> None:
        from app.github_fetcher import fetch_repo_info

        httpx_mock.add_response(
            url="https://api.github.com/repos/priv/repo",
            status_code=403,
        )
        with pytest.raises(GitHubError) as exc_info:
            await fetch_repo_info("priv", "repo")
        assert exc_info.value.status_code == 403
        assert "GITHUB_TOKEN" in exc_info.value.message


# ---------------------------------------------------------------------------
# fetch_repo_tree
# ---------------------------------------------------------------------------


class TestFetchRepoTree:
    """Tree API tests."""

    async def test_returns_blobs_only(self, httpx_mock) -> None:
        from app.github_fetcher import fetch_repo_tree

        httpx_mock.add_response(
            url="https://api.github.com/repos/o/r/git/trees/abc123?recursive=1",
            json={
                "sha": "abc123",
                "tree": [
                    {"path": "README.md", "type": "blob", "size": 100, "sha": "a1"},
                    {"path": "src", "type": "tree", "sha": "a2"},
                    {"path": "src/main.py", "type": "blob", "size": 200, "sha": "a3"},
                ],
                "truncated": False,
            },
        )
        blobs = await fetch_repo_tree("o", "r", "abc123")
        assert len(blobs) == 2
        assert all(b["type"] == "blob" for b in blobs)

    async def test_timeout_raises_503(self, httpx_mock) -> None:
        from app.github_fetcher import fetch_repo_info

        httpx_mock.add_exception(
            httpx.TimeoutException("timed out"),
            url="https://api.github.com/repos/slow/repo",
        )
        with pytest.raises(GitHubError) as exc_info:
            await fetch_repo_info("slow", "repo")
        assert exc_info.value.status_code == 503
        assert "unavailable" in exc_info.value.message.lower()

    async def test_warns_on_truncated(self, httpx_mock, caplog) -> None:
        from app.github_fetcher import fetch_repo_tree

        httpx_mock.add_response(
            url="https://api.github.com/repos/o/r/git/trees/abc?recursive=1",
            json={"sha": "abc", "tree": [], "truncated": True},
        )
        with caplog.at_level(logging.WARNING):
            await fetch_repo_tree("o", "r", "abc")
        assert "truncated" in caplog.text.lower()
