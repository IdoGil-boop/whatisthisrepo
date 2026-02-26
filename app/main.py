"""FastAPI application — POST /summarize endpoint with caching and SSE streaming."""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import MAX_CACHE_SIZE
from app.github_fetcher import (
    close_client,
    fetch_branch_sha,
    fetch_repo_info,
    fetch_repo_tree,
    parse_github_url,
)
from app.llm_client import select_model, summarize
from app.models import (
    EmptyRepoError,
    ErrorResponse,
    GitHubError,
    LLMError,
    ProcessingError,
    SummarizeRequest,
    SummarizeResponse,
)
from app.repo_processor import discover_files, fetch_and_assemble, select_files

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown lifecycle — closes the shared httpx client on exit."""
    yield
    await close_client()


app = FastAPI(title="GitHub Repo Summarizer", lifespan=lifespan)


@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Return structured JSON for any unhandled exception."""
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(message="Internal server error").model_dump(),
        )


# In-memory cache: key = "owner/repo", value = {sha, tree, contents, response}
_cache: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Surface URL validation as 400 when the URL is present but invalid format.
    # Missing field entirely -> 422 (standard validation).
    for error in exc.errors():
        msg_text = error.get("msg", "")
        err_type = error.get("type", "")
        # value_error = our custom validator fired (URL present but bad format)
        # missing = field absent from body
        if "GitHub URL" in msg_text and err_type == "value_error":
            msg = "Invalid GitHub URL format. Expected: https://github.com/{owner}/{repo}"
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(message=msg).model_dump(),
            )
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(message="Validation error").model_dump(),
    )


@app.exception_handler(GitHubError)
async def github_error_handler(request: Request, exc: GitHubError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=exc.message).model_dump(),
    )


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(message=exc.message).model_dump(),
    )


@app.exception_handler(EmptyRepoError)
async def empty_repo_handler(request: Request, exc: EmptyRepoError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(message=exc.message).model_dump(),
    )


@app.exception_handler(ProcessingError)
async def processing_error_handler(request: Request, exc: ProcessingError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(message=exc.message).model_dump(),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


TOTAL_STEPS = 6


async def _run_pipeline(owner: str, repo: str) -> SummarizeResponse:
    """Execute the summarize pipeline (non-streaming JSON path)."""
    t0 = time.monotonic()
    cache_key = f"{owner}/{repo}"

    repo_info = await fetch_repo_info(owner, repo)
    branch = repo_info["default_branch"]
    sha = await fetch_branch_sha(owner, repo, branch)

    # Cache hit — same SHA
    cached = _cache.get(cache_key)
    if cached and cached["sha"] == sha:
        logger.info("Cache hit for %s (SHA %s)", cache_key, sha[:8])
        elapsed = time.monotonic() - t0
        logger.info("Summarized %s in %.2fs (cached)", cache_key, elapsed)
        return SummarizeResponse(**cached["response"])

    tree = await fetch_repo_tree(owner, repo, sha)

    # Diff against cached tree for incremental fetches
    cached_contents: Dict[str, str] = {}
    if cached and cached.get("tree"):
        old_sha_map = {e["path"]: e["sha"] for e in cached["tree"]}
        for entry in tree:
            if entry["path"] in old_sha_map and entry["sha"] == old_sha_map[entry["path"]]:
                if entry["path"] in cached.get("contents", {}):
                    cached_contents[entry["path"]] = cached["contents"][entry["path"]]

    try:
        included, _skipped = discover_files(tree)
        selected = select_files(included)
        digest, all_contents = await fetch_and_assemble(
            selected, owner, repo, repo_info, tree, ref=sha, cached_contents=cached_contents
        )
    except (GitHubError, EmptyRepoError):
        raise
    except Exception as exc:
        raise ProcessingError(f"Failed to process repository: {exc}") from exc

    result = await summarize(digest)

    # Update cache (bounded)
    if len(_cache) >= MAX_CACHE_SIZE:
        _cache.pop(next(iter(_cache)))  # evict oldest
    _cache[cache_key] = {
        "sha": sha,
        "tree": tree,
        "contents": all_contents,
        "response": result,
    }

    elapsed = time.monotonic() - t0
    logger.info("Summarized %s in %.2fs", cache_key, elapsed)
    return SummarizeResponse(**result)


def _sse_event(event: str, data: dict) -> str:
    """Format a single SSE event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _progress_event(phase: str, step: int) -> str:
    """Format a progress SSE event."""
    data = {"phase": phase, "step": step, "total_steps": TOTAL_STEPS}
    return _sse_event("progress", data)


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_repo(body: SummarizeRequest, request: Request) -> SummarizeResponse:
    """Summarize a GitHub repository.

    Content-negotiated: returns SSE stream when Accept: text/event-stream,
    otherwise returns the standard JSON response.
    """
    owner, repo = parse_github_url(body.github_url)
    accept = request.headers.get("accept", "")

    if "text/event-stream" not in accept:
        return await _run_pipeline(owner, repo)

    # SSE streaming path — inline pipeline so we can yield between steps
    async def _event_stream() -> AsyncIterator[str]:
        try:
            owner_repo = f"{owner}/{repo}"
            cache_key = owner_repo
            t0 = time.monotonic()

            # Step 1
            yield _progress_event("Fetching repository info...", 1)
            repo_info = await fetch_repo_info(owner, repo)
            branch = repo_info["default_branch"]
            sha = await fetch_branch_sha(owner, repo, branch)

            # Cache hit
            cached = _cache.get(cache_key)
            if cached and cached["sha"] == sha:
                logger.info("Cache hit for %s (SHA %s)", cache_key, sha[:8])
                resp = SummarizeResponse(**cached["response"])
                yield _sse_event("complete", resp.model_dump())
                return

            # Step 2
            tree = await fetch_repo_tree(owner, repo, sha)
            yield _progress_event(f"Analyzing repo structure ({len(tree)} files found)", 2)

            # Diff against cached tree
            cached_contents: Dict[str, str] = {}
            if cached and cached.get("tree"):
                old_sha_map = {e["path"]: e["sha"] for e in cached["tree"]}
                for entry in tree:
                    if entry["path"] in old_sha_map and entry["sha"] == old_sha_map[entry["path"]]:
                        if entry["path"] in cached.get("contents", {}):
                            cached_contents[entry["path"]] = cached["contents"][entry["path"]]

            # Steps 3-4
            try:
                included, _skipped = discover_files(tree)
                selected = select_files(included)
                yield _progress_event(f"Fetching file contents ({len(selected)} files)...", 3)
                digest, all_contents = await fetch_and_assemble(
                    selected, owner, repo, repo_info, tree, ref=sha, cached_contents=cached_contents
                )
                yield _progress_event(f"Assembling digest ({len(digest)} chars)", 4)
            except (GitHubError, EmptyRepoError):
                raise
            except Exception as exc:
                raise ProcessingError(f"Failed to process repository: {exc}") from exc

            # Step 5
            model = select_model(len(digest))
            yield _progress_event(f"Generating summary with {model}...", 5)
            result = await summarize(digest)

            # Update cache
            if len(_cache) >= MAX_CACHE_SIZE:
                _cache.pop(next(iter(_cache)))
            _cache[cache_key] = {
                "sha": sha,
                "tree": tree,
                "contents": all_contents,
                "response": result,
            }

            elapsed = time.monotonic() - t0
            logger.info("Summarized %s in %.2fs (SSE)", cache_key, elapsed)

            # Step 6: complete
            yield _sse_event("complete", result)

        except (GitHubError, LLMError, EmptyRepoError, ProcessingError) as exc:
            msg = exc.message if hasattr(exc, "message") else str(exc)
            yield _sse_event("error", {"message": msg})
        except Exception:
            logger.exception("Unhandled error in SSE stream")
            yield _sse_event("error", {"message": "Internal server error"})

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
