import pytest


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required env vars before any app module is imported."""
    monkeypatch.setenv("NEBIUS_API_KEY", "test-key")
    # Clear optional overrides so tests start clean
    monkeypatch.delenv("NEBIUS_MODEL", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
