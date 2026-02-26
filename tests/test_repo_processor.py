"""Tests for app.repo_processor — file discovery, binary detection, selection, tree summary."""

from __future__ import annotations

import pytest

from app.models import EmptyRepoError

# ---------------------------------------------------------------------------
# discover_files
# ---------------------------------------------------------------------------


class TestDiscoverFiles:
    """File filtering and skip-reason assignment."""

    def test_ignores_node_modules(self) -> None:
        from app.repo_processor import discover_files

        tree = [
            {"path": "node_modules/express/index.js", "type": "blob", "size": 100, "sha": "a1"},
            {"path": "README.md", "type": "blob", "size": 50, "sha": "a2"},
        ]
        included, skipped = discover_files(tree)
        assert len(included) == 1
        assert included[0]["path"] == "README.md"
        assert skipped[0]["reason"] == "ignored-dir"

    def test_skips_lockfiles(self) -> None:
        from app.repo_processor import discover_files

        tree = [
            {"path": "package-lock.json", "type": "blob", "size": 100, "sha": "a1"},
        ]
        included, skipped = discover_files(tree)
        assert len(included) == 0
        assert skipped[0]["reason"] == "lockfile"

    def test_skips_binary_extensions(self) -> None:
        from app.repo_processor import discover_files

        tree = [
            {"path": "logo.png", "type": "blob", "size": 100, "sha": "a1"},
        ]
        included, skipped = discover_files(tree)
        assert len(included) == 0
        assert skipped[0]["reason"] == "binary-extension"

    def test_skips_oversized(self) -> None:
        from app.repo_processor import discover_files

        tree = [
            {"path": "big.py", "type": "blob", "size": 300_000, "sha": "a1"},
        ]
        included, skipped = discover_files(tree)
        assert len(included) == 0
        assert skipped[0]["reason"] == "too-large"

    def test_assigns_readme_rank_1(self) -> None:
        from app.repo_processor import discover_files

        tree = [{"path": "README.md", "type": "blob", "size": 100, "sha": "a1"}]
        included, _ = discover_files(tree)
        assert included[0]["rank"] == 1

    def test_assigns_claude_md_rank_2(self) -> None:
        from app.repo_processor import discover_files

        tree = [{"path": "CLAUDE.md", "type": "blob", "size": 100, "sha": "a1"}]
        included, _ = discover_files(tree)
        assert included[0]["rank"] == 2

    def test_assigns_pyproject_rank_3(self) -> None:
        from app.repo_processor import discover_files

        tree = [{"path": "pyproject.toml", "type": "blob", "size": 100, "sha": "a1"}]
        included, _ = discover_files(tree)
        assert included[0]["rank"] == 3

    def test_assigns_workflow_rank_5(self) -> None:
        from app.repo_processor import discover_files

        tree = [{"path": ".github/workflows/ci.yml", "type": "blob", "size": 100, "sha": "a1"}]
        included, _ = discover_files(tree)
        assert included[0]["rank"] == 5

    def test_skips_min_js(self) -> None:
        from app.repo_processor import discover_files

        tree = [{"path": "bundle.min.js", "type": "blob", "size": 100, "sha": "a1"}]
        included, skipped = discover_files(tree)
        assert len(included) == 0
        assert skipped[0]["reason"] == "binary-extension"


# ---------------------------------------------------------------------------
# detect_binary_content
# ---------------------------------------------------------------------------


class TestDetectBinaryContent:
    """Binary content detection on raw bytes."""

    def test_nul_byte(self) -> None:
        from app.repo_processor import detect_binary_content

        assert detect_binary_content(b"hello\x00world") is True

    def test_invalid_utf8(self) -> None:
        from app.repo_processor import detect_binary_content

        assert detect_binary_content(b"\xff\xfe") is True

    def test_valid_text(self) -> None:
        from app.repo_processor import detect_binary_content

        assert detect_binary_content(b"def hello():\n    pass\n") is False


# ---------------------------------------------------------------------------
# select_files
# ---------------------------------------------------------------------------


class TestSelectFiles:
    """File selection, ordering, and capping."""

    def test_empty_raises(self) -> None:
        from app.repo_processor import select_files

        with pytest.raises(EmptyRepoError):
            select_files([])

    def test_caps_at_max_files(self) -> None:
        from app.repo_processor import select_files

        files = [
            {"path": f"src/file{i}.py", "rank": 10, "size": 100, "sha": f"s{i}"} for i in range(30)
        ]
        selected = select_files(files)
        assert len(selected) <= 18

    def test_caps_workflow_to_one(self) -> None:
        from app.repo_processor import select_files

        files = [
            {"path": ".github/workflows/ci.yml", "rank": 5, "size": 100, "sha": "w1"},
            {"path": ".github/workflows/release.yml", "rank": 5, "size": 100, "sha": "w2"},
            {"path": "README.md", "rank": 1, "size": 100, "sha": "r1"},
        ]
        selected = select_files(files)
        workflows = [f for f in selected if ".github/workflows" in f["path"]]
        assert len(workflows) == 1

    def test_sorts_by_rank_then_depth(self) -> None:
        from app.repo_processor import select_files

        files = [
            {"path": "src/utils/deep.py", "rank": 10, "size": 100, "sha": "d1"},
            {"path": "README.md", "rank": 1, "size": 100, "sha": "r1"},
            {"path": "src/app.py", "rank": 6, "size": 100, "sha": "a1"},
        ]
        selected = select_files(files)
        assert selected[0]["path"] == "README.md"
        assert selected[1]["path"] == "src/app.py"


# ---------------------------------------------------------------------------
# build_tree_summary & count_extensions
# ---------------------------------------------------------------------------


class TestTreeSummary:
    """Tree summary and extension counting."""

    def test_depth_cap(self) -> None:
        from app.repo_processor import build_tree_summary

        tree = [
            {"path": "src/main.py", "type": "blob"},
            {"path": "src/utils/helpers/format.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
        ]
        summary = build_tree_summary(tree, depth=2)
        assert "README.md" in summary
        assert "src/" in summary

    def test_count_extensions_detects_python(self) -> None:
        from app.repo_processor import count_extensions

        tree = [
            {"path": "app.py", "type": "blob"},
            {"path": "utils.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
        ]
        result = count_extensions(tree)
        assert "Python" in result


# ---------------------------------------------------------------------------
# _truncate
# ---------------------------------------------------------------------------


class TestTruncate:
    """Per-file truncation."""

    def test_truncate_by_lines(self) -> None:
        from app.repo_processor import _truncate

        content = "\n".join(f"line {i}" for i in range(500))
        truncated = _truncate(content, max_lines=10, max_chars=999_999)
        assert truncated.endswith("... [truncated]")
        assert truncated.count("\n") <= 11  # 10 lines + truncation marker

    def test_truncate_by_chars(self) -> None:
        from app.repo_processor import _truncate

        content = "x" * 20_000
        truncated = _truncate(content, max_lines=999_999, max_chars=100)
        assert len(truncated) < 200
        assert "truncated" in truncated
