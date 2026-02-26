"""FastAPI application — POST /summarize endpoint with caching."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import MAX_CACHE_SIZE
from app.github_fetcher import (
    close_client,
    fetch_branch_sha,
    fetch_repo_info,
    fetch_repo_tree,
    parse_github_url,
)
from app.llm_client import summarize
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


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_repo(body: SummarizeRequest) -> SummarizeResponse:
    """Summarize a GitHub repository."""
    t0 = time.monotonic()

    owner, repo = parse_github_url(body.github_url)
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

    # Fetch tree
    tree = await fetch_repo_tree(owner, repo, sha)

    # Diff against cached tree for incremental fetches
    cached_contents: Dict[str, str] = {}
    if cached and cached.get("tree"):
        old_sha_map = {e["path"]: e["sha"] for e in cached["tree"]}
        for entry in tree:
            if entry["path"] in old_sha_map and entry["sha"] == old_sha_map[entry["path"]]:
                if entry["path"] in cached.get("contents", {}):
                    cached_contents[entry["path"]] = cached["contents"][entry["path"]]

    # Process
    try:
        included, skipped = discover_files(tree)
        selected = select_files(included)
        digest, all_contents = await fetch_and_assemble(
            selected, owner, repo, repo_info, tree, ref=sha, cached_contents=cached_contents
        )
    except (GitHubError, EmptyRepoError):
        raise
    except Exception as exc:
        raise ProcessingError(f"Failed to process repository: {exc}") from exc

    # LLM
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
