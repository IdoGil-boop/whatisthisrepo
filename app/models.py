"""Pydantic request/response models and typed exceptions."""

from __future__ import annotations

import re

from pydantic import BaseModel, model_validator

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

_GITHUB_URL_RE = re.compile(r"^https://github\.com/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+(\.git|/)?$")


class GitHubError(Exception):
    """Error originating from the GitHub API."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class LLMError(Exception):
    """Error from the LLM provider."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EmptyRepoError(Exception):
    """No summarizable content in the repository."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ProcessingError(Exception):
    """Unexpected processing failure."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SummarizeRequest(BaseModel):
    """Incoming request body for POST /summarize."""

    github_url: str

    @model_validator(mode="before")
    @classmethod
    def validate_github_url(cls, values: dict) -> dict:  # type: ignore[override]
        url = values.get("github_url")
        if url is None:
            # Let Pydantic handle missing-field as 422
            return values
        if not isinstance(url, str) or not _GITHUB_URL_RE.match(url):
            raise ValueError(
                "Invalid GitHub URL format. Expected: https://github.com/{owner}/{repo}"
            )
        return values


class SummarizeResponse(BaseModel):
    """Successful summary response."""

    summary: str
    technologies: list[str]
    structure: str


class ErrorResponse(BaseModel):
    """Structured error returned for all failure cases."""

    status: str = "error"
    message: str
