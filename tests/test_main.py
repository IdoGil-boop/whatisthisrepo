"""Tests for app.main — endpoint integration tests."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    from app.main import app

    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    """Request validation tests."""

    async def test_invalid_url_returns_400(self, client) -> None:
        resp = await client.post("/summarize", json={"github_url": "https://evil.com/x/y"})
        assert resp.status_code == 400

    async def test_missing_field_returns_422(self, client) -> None:
        resp = await client.post("/summarize", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Error scenarios (mocked externals)
# ---------------------------------------------------------------------------


class TestErrorScenarios:
    """Error propagation from components to HTTP responses."""

    async def test_repo_not_found_returns_404(self, client) -> None:
        from app.models import GitHubError

        with patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock:
            mock.side_effect = GitHubError(404, "Repository not found: no/exist")
            resp = await client.post(
                "/summarize", json={"github_url": "https://github.com/no/exist"}
            )
        assert resp.status_code == 404
        assert "not found" in resp.json()["message"].lower()

    async def test_rate_limited_returns_403(self, client) -> None:
        from app.models import GitHubError

        with patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock:
            mock.side_effect = GitHubError(
                403, "GitHub rate limit exceeded. Set GITHUB_TOKEN env var for higher limits."
            )
            resp = await client.post(
                "/summarize", json={"github_url": "https://github.com/priv/repo"}
            )
        assert resp.status_code == 403
        assert "GITHUB_TOKEN" in resp.json()["message"]

    async def test_empty_repo_returns_422(self, client) -> None:
        from app.models import EmptyRepoError

        with (
            patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock_info,
            patch("app.main.fetch_branch_sha", new_callable=AsyncMock) as mock_sha,
            patch("app.main.fetch_repo_tree", new_callable=AsyncMock) as mock_tree,
            patch("app.main.discover_files") as mock_disc,
        ):
            mock_info.return_value = {
                "description": "x",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 0,
                "forks_count": 0,
            }
            mock_sha.return_value = "abc123"
            mock_tree.return_value = []
            mock_disc.return_value = ([], [])
            with patch("app.main.select_files") as mock_sel:
                mock_sel.side_effect = EmptyRepoError("Repository has no summarizable content")
                resp = await client.post(
                    "/summarize", json={"github_url": "https://github.com/empty/repo"}
                )
        assert resp.status_code == 422

    async def test_llm_failure_returns_502(self, client) -> None:
        from app.models import LLMError

        with (
            patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock_info,
            patch("app.main.fetch_branch_sha", new_callable=AsyncMock) as mock_sha,
            patch("app.main.fetch_repo_tree", new_callable=AsyncMock) as mock_tree,
            patch("app.main.discover_files") as mock_disc,
            patch("app.main.select_files") as mock_sel,
            patch("app.main.fetch_and_assemble", new_callable=AsyncMock) as mock_asm,
            patch("app.main.summarize", new_callable=AsyncMock) as mock_llm,
        ):
            mock_info.return_value = {
                "description": "x",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 0,
                "forks_count": 0,
            }
            mock_sha.return_value = "abc123"
            mock_tree.return_value = [
                {"path": "README.md", "type": "blob", "size": 10, "sha": "r1"}
            ]
            mock_disc.return_value = (
                [{"path": "README.md", "rank": 1, "size": 10, "sha": "r1"}],
                [],
            )
            mock_sel.return_value = [{"path": "README.md", "rank": 1, "size": 10, "sha": "r1"}]
            mock_asm.return_value = ("digest", {})
            mock_llm.side_effect = LLMError("LLM failed")
            resp = await client.post(
                "/summarize", json={"github_url": "https://github.com/any/repo"}
            )
        assert resp.status_code == 502

    async def test_unhandled_exception_returns_500(self, client) -> None:
        """Unexpected exceptions should return structured 500."""
        with patch("app.main.parse_github_url", side_effect=RuntimeError("boom")):
            resp = await client.post(
                "/summarize", json={"github_url": "https://github.com/any/repo"}
            )
        assert resp.status_code == 500
        body = resp.json()
        assert body["status"] == "error"
        assert "Internal server error" in body["message"]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    """Full success path with all externals mocked."""

    async def test_success_returns_200(self, client) -> None:
        with (
            patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock_info,
            patch("app.main.fetch_branch_sha", new_callable=AsyncMock) as mock_sha,
            patch("app.main.fetch_repo_tree", new_callable=AsyncMock) as mock_tree,
            patch("app.main.discover_files") as mock_disc,
            patch("app.main.select_files") as mock_sel,
            patch("app.main.fetch_and_assemble", new_callable=AsyncMock) as mock_asm,
            patch("app.main.summarize", new_callable=AsyncMock) as mock_llm,
        ):
            mock_info.return_value = {
                "description": "Lib",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 100,
                "forks_count": 10,
            }
            mock_sha.return_value = "sha1"
            mock_tree.return_value = [
                {"path": "README.md", "type": "blob", "size": 50, "sha": "r1"}
            ]
            mock_disc.return_value = (
                [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}],
                [],
            )
            mock_sel.return_value = [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}]
            mock_asm.return_value = ("digest text", {})
            mock_llm.return_value = {
                "summary": "A library",
                "technologies": ["Python"],
                "structure": "flat",
            }
            resp = await client.post(
                "/summarize", json={"github_url": "https://github.com/psf/requests"}
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"] == "A library"
        assert body["technologies"] == ["Python"]
        assert body["structure"] == "flat"

    async def test_cache_hit_skips_llm(self, client) -> None:
        """Second request with same SHA should skip LLM."""
        with (
            patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock_info,
            patch("app.main.fetch_branch_sha", new_callable=AsyncMock) as mock_sha,
            patch("app.main.fetch_repo_tree", new_callable=AsyncMock) as mock_tree,
            patch("app.main.discover_files") as mock_disc,
            patch("app.main.select_files") as mock_sel,
            patch("app.main.fetch_and_assemble", new_callable=AsyncMock) as mock_asm,
            patch("app.main.summarize", new_callable=AsyncMock) as mock_llm,
        ):
            mock_info.return_value = {
                "description": "Lib",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 100,
                "forks_count": 10,
            }
            mock_sha.return_value = "sha-cached"
            mock_tree.return_value = [
                {"path": "README.md", "type": "blob", "size": 50, "sha": "r1"}
            ]
            mock_disc.return_value = (
                [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}],
                [],
            )
            mock_sel.return_value = [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}]
            mock_asm.return_value = ("digest", {})
            mock_llm.return_value = {
                "summary": "Cached",
                "technologies": ["Go"],
                "structure": "mono",
            }

            # First request
            resp1 = await client.post(
                "/summarize", json={"github_url": "https://github.com/cache/test"}
            )
            assert resp1.status_code == 200

            # Second request — same SHA, should use cache
            resp2 = await client.post(
                "/summarize", json={"github_url": "https://github.com/cache/test"}
            )
            assert resp2.status_code == 200
            assert resp2.json()["summary"] == "Cached"
            # LLM should only be called once
            assert mock_llm.call_count == 1


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------


def _parse_sse(text: str) -> list[dict]:
    """Parse SSE text into a list of {event, data} dicts."""
    events = []
    current_event = None
    current_data = None
    for line in text.splitlines():
        if line.startswith("event: "):
            current_event = line[len("event: ") :]
        elif line.startswith("data: "):
            current_data = json.loads(line[len("data: ") :])
        elif line == "" and current_event is not None:
            events.append({"event": current_event, "data": current_data})
            current_event = None
            current_data = None
    # Handle trailing event without final blank line
    if current_event is not None and current_data is not None:
        events.append({"event": current_event, "data": current_data})
    return events


SSE_HEADERS = {"accept": "text/event-stream"}


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear the in-memory cache between tests to prevent leakage."""
    from app.main import _cache

    _cache.clear()
    yield
    _cache.clear()


class TestSSEStreaming:
    """SSE progress streaming tests."""

    async def test_sse_success_emits_progress_and_complete(self, client) -> None:
        """Successful SSE stream should have progress events then a complete event."""
        with (
            patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock_info,
            patch("app.main.fetch_branch_sha", new_callable=AsyncMock) as mock_sha,
            patch("app.main.fetch_repo_tree", new_callable=AsyncMock) as mock_tree,
            patch("app.main.discover_files") as mock_disc,
            patch("app.main.select_files") as mock_sel,
            patch("app.main.fetch_and_assemble", new_callable=AsyncMock) as mock_asm,
            patch("app.main.summarize", new_callable=AsyncMock) as mock_llm,
            patch("app.main.select_model") as mock_model,
        ):
            mock_info.return_value = {
                "description": "Lib",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 100,
                "forks_count": 10,
            }
            mock_sha.return_value = "sha1"
            mock_tree.return_value = [
                {"path": "README.md", "type": "blob", "size": 50, "sha": "r1"}
            ]
            mock_disc.return_value = (
                [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}],
                [],
            )
            mock_sel.return_value = [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}]
            mock_asm.return_value = ("digest text", {"README.md": "# Hello"})
            mock_model.return_value = "Qwen/Qwen3-32B"
            mock_llm.return_value = {
                "summary": "A library",
                "technologies": ["Python"],
                "structure": "flat",
            }
            resp = await client.post(
                "/summarize",
                json={"github_url": "https://github.com/psf/requests"},
                headers=SSE_HEADERS,
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        events = _parse_sse(resp.text)

        # Should have progress events (steps 1-5) + complete
        progress_events = [e for e in events if e["event"] == "progress"]
        complete_events = [e for e in events if e["event"] == "complete"]
        assert len(progress_events) == 5
        assert len(complete_events) == 1

        # Verify step numbers are sequential 1-5
        steps = [e["data"]["step"] for e in progress_events]
        assert steps == [1, 2, 3, 4, 5]

        # All progress events should have total_steps
        for e in progress_events:
            assert e["data"]["total_steps"] == 6

        # Complete event should contain the summary
        complete_data = complete_events[0]["data"]
        assert complete_data["summary"] == "A library"
        assert complete_data["technologies"] == ["Python"]

    async def test_sse_error_emits_error_event(self, client) -> None:
        """Errors during SSE streaming should emit an error event."""
        from app.models import GitHubError

        with patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock:
            mock.side_effect = GitHubError(404, "Repository not found: no/exist")
            resp = await client.post(
                "/summarize",
                json={"github_url": "https://github.com/no/exist"},
                headers=SSE_HEADERS,
            )

        # SSE always returns 200 (streaming started), error is in the event
        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        error_events = [e for e in events if e["event"] == "error"]
        assert len(error_events) == 1
        assert "not found" in error_events[0]["data"]["message"].lower()

    async def test_sse_llm_error_emits_error_event(self, client) -> None:
        """LLM errors during SSE streaming should emit an error event."""
        from app.models import LLMError

        with (
            patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock_info,
            patch("app.main.fetch_branch_sha", new_callable=AsyncMock) as mock_sha,
            patch("app.main.fetch_repo_tree", new_callable=AsyncMock) as mock_tree,
            patch("app.main.discover_files") as mock_disc,
            patch("app.main.select_files") as mock_sel,
            patch("app.main.fetch_and_assemble", new_callable=AsyncMock) as mock_asm,
            patch("app.main.summarize", new_callable=AsyncMock) as mock_llm,
            patch("app.main.select_model") as mock_model,
        ):
            mock_info.return_value = {
                "description": "x",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 0,
                "forks_count": 0,
            }
            mock_sha.return_value = "abc123"
            mock_tree.return_value = [
                {"path": "README.md", "type": "blob", "size": 10, "sha": "r1"}
            ]
            mock_disc.return_value = (
                [{"path": "README.md", "rank": 1, "size": 10, "sha": "r1"}],
                [],
            )
            mock_sel.return_value = [{"path": "README.md", "rank": 1, "size": 10, "sha": "r1"}]
            mock_asm.return_value = ("digest", {})
            mock_model.return_value = "Qwen/Qwen3-32B"
            mock_llm.side_effect = LLMError("LLM failed")
            resp = await client.post(
                "/summarize",
                json={"github_url": "https://github.com/any/repo"},
                headers=SSE_HEADERS,
            )

        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        # Should have some progress events before the error
        progress_events = [e for e in events if e["event"] == "progress"]
        assert len(progress_events) >= 1
        error_events = [e for e in events if e["event"] == "error"]
        assert len(error_events) == 1
        assert "LLM failed" in error_events[0]["data"]["message"]

    async def test_no_accept_header_returns_json(self, client) -> None:
        """Without Accept: text/event-stream, should return normal JSON."""
        with (
            patch("app.main.fetch_repo_info", new_callable=AsyncMock) as mock_info,
            patch("app.main.fetch_branch_sha", new_callable=AsyncMock) as mock_sha,
            patch("app.main.fetch_repo_tree", new_callable=AsyncMock) as mock_tree,
            patch("app.main.discover_files") as mock_disc,
            patch("app.main.select_files") as mock_sel,
            patch("app.main.fetch_and_assemble", new_callable=AsyncMock) as mock_asm,
            patch("app.main.summarize", new_callable=AsyncMock) as mock_llm,
        ):
            mock_info.return_value = {
                "description": "Lib",
                "language": "Python",
                "default_branch": "main",
                "stargazers_count": 100,
                "forks_count": 10,
            }
            mock_sha.return_value = "sha1"
            mock_tree.return_value = [
                {"path": "README.md", "type": "blob", "size": 50, "sha": "r1"}
            ]
            mock_disc.return_value = (
                [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}],
                [],
            )
            mock_sel.return_value = [{"path": "README.md", "rank": 1, "size": 50, "sha": "r1"}]
            mock_asm.return_value = ("digest text", {})
            mock_llm.return_value = {
                "summary": "A library",
                "technologies": ["Python"],
                "structure": "flat",
            }
            resp = await client.post(
                "/summarize",
                json={"github_url": "https://github.com/psf/requests"},
            )

        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        body = resp.json()
        assert body["summary"] == "A library"
