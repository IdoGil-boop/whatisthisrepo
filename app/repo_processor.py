"""Repo content processor — file discovery, selection, assembly, and compaction."""

from __future__ import annotations

import fnmatch
import logging
import os
from typing import Dict, List, Optional, Tuple

from app.config import (
    BINARY_EXTENSIONS,
    IGNORED_DIRS,
    LOCKFILES,
    MAX_CHARS,
    MAX_DIGEST_CHARS,
    MAX_FILE_SIZE,
    MAX_FILES,
    MAX_LINES,
)
from app.models import EmptyRepoError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Priority rules: (pattern, rank) — lower rank = higher priority
# ---------------------------------------------------------------------------
PRIORITY_RULES: List[Tuple[str, int]] = [
    ("README.md", 1),
    ("README.rst", 1),
    ("README.txt", 1),
    ("README", 1),
    ("CLAUDE.md", 2),
    (".cursorrules", 2),
    (".cursorules", 2),
    ("AGENTS.md", 2),
    ("CONVENTIONS.md", 2),
    ("copilot-instructions.md", 2),
    ("pyproject.toml", 3),
    ("package.json", 3),
    ("Cargo.toml", 3),
    ("go.mod", 3),
    ("Gemfile", 3),
    ("pom.xml", 3),
    ("build.gradle", 3),
    ("Dockerfile", 4),
    ("docker-compose.yml", 4),
    ("Makefile", 4),
    (".gitignore", 4),
    (".github/workflows/*.yml", 5),
    (".github/workflows/*.yaml", 5),
    ("main.py", 6),
    ("app.py", 6),
    ("src/index.*", 6),
    ("server.*", 6),
    ("cmd/*/main.go", 6),
    ("routes/*", 7),
    ("api/*", 7),
    ("endpoints/*", 7),
    ("urls.py", 7),
    ("openapi.*", 7),
    ("src/*", 8),
    ("lib/*", 8),
    ("types.ts", 9),
    ("models.py", 9),
    ("schema.*", 9),
    ("config.*", 9),
]

# Patterns that should be skipped (binary-like)
_SKIP_PATTERNS = ["*.min.js", "*.min.css", "*.pb.go", "generated.*", "*.snap"]

# Extension to language mapping
_EXT_LANG: Dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
}


def _path_depth(path: str) -> int:
    return path.count("/")


def _get_extension(path: str) -> str:
    _, ext = os.path.splitext(path)
    return ext.lower()


def _match_priority(path: str) -> int:
    """Return the priority rank for a file path. Default rank 10 (lowest)."""
    filename = os.path.basename(path)
    for pattern, rank in PRIORITY_RULES:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(filename, pattern):
            return rank
    return 10


def _in_ignored_dir(path: str) -> bool:
    parts = path.split("/")
    return any(part in IGNORED_DIRS for part in parts[:-1])


def _is_skip_pattern(path: str) -> bool:
    filename = os.path.basename(path)
    return any(fnmatch.fnmatch(filename, pat) for pat in _SKIP_PATTERNS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def discover_files(tree: List[dict]) -> Tuple[List[dict], List[dict]]:
    """Filter tree entries into included/skipped, assigning rank and skip reason."""
    included: List[dict] = []
    skipped: List[dict] = []

    for entry in tree:
        path = entry["path"]
        size = entry.get("size", 0)
        filename = os.path.basename(path)

        if _in_ignored_dir(path):
            skipped.append({**entry, "reason": "ignored-dir"})
            continue

        if filename in LOCKFILES:
            skipped.append({**entry, "reason": "lockfile"})
            continue

        ext = _get_extension(path)
        if ext in BINARY_EXTENSIONS or _is_skip_pattern(path):
            skipped.append({**entry, "reason": "binary-extension"})
            continue

        if size > MAX_FILE_SIZE:
            skipped.append({**entry, "reason": "too-large"})
            continue

        rank = _match_priority(path)
        included.append({**entry, "rank": rank})

    logger.info("discover_files: %d included, %d skipped", len(included), len(skipped))
    return included, skipped


def detect_binary_content(raw: bytes) -> bool:
    """Check first 8192 bytes for NUL byte or invalid UTF-8."""
    chunk = raw[:8192]
    if b"\x00" in chunk:
        return True
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def select_files(filtered: List[dict]) -> List[dict]:
    """Sort by rank then depth, cap workflows, cap total. Raise on empty."""
    if not filtered:
        raise EmptyRepoError("Repository has no summarizable content")

    sorted_files = sorted(filtered, key=lambda f: (f["rank"], _path_depth(f["path"])))

    # Cap CI workflows to first only
    result: List[dict] = []
    workflow_count = 0
    for f in sorted_files:
        if fnmatch.fnmatch(f["path"], ".github/workflows/*"):
            workflow_count += 1
            if workflow_count > 1:
                continue
        result.append(f)
        if len(result) >= MAX_FILES:
            break

    return result


def build_tree_summary(tree: List[dict], depth: int = 2) -> str:
    """Build a compact directory listing up to `depth` levels."""
    dirs: set = set()
    files_at_root: List[str] = []
    total = len(tree)
    shown = 0

    for entry in tree:
        path = entry["path"]
        parts = path.split("/")
        if len(parts) == 1:
            files_at_root.append(path)
            shown += 1
        elif len(parts) - 1 <= depth:
            parent = "/".join(parts[:-1]) + "/"
            dirs.add(parent)
            shown += 1
        else:
            parent = "/".join(parts[:depth]) + "/"
            dirs.add(parent)

    lines = sorted(files_at_root) + sorted(dirs)
    remaining = total - shown
    if remaining > 0:
        lines.append(f"... {remaining} more files")
    return "\n".join(lines)


def count_extensions(tree: List[dict]) -> str:
    """Count file extensions and map the most frequent to a language name."""
    counts: Dict[str, int] = {}
    for entry in tree:
        ext = _get_extension(entry["path"])
        if ext:
            counts[ext] = counts.get(ext, 0) + 1
    if not counts:
        return "Unknown"
    top_ext = max(counts, key=lambda e: counts[e])
    return _EXT_LANG.get(top_ext, top_ext)


async def fetch_and_assemble(
    selected: List[dict],
    owner: str,
    repo: str,
    repo_info: dict,
    full_tree: List[dict],
    ref: str,
    cached_contents: Optional[Dict[str, str]] = None,
) -> Tuple[str, Dict[str, str]]:
    """Fetch selected files and assemble into REPO DIGEST format."""
    from app.github_fetcher import fetch_file_content

    cached_contents = cached_contents or {}
    all_contents: Dict[str, str] = dict(cached_contents)
    primary_lang = count_extensions(full_tree)
    tree_summary = build_tree_summary(full_tree)

    sections: Dict[str, str] = {}

    # Metadata section
    desc = repo_info.get("description", "Not provided")
    stars = repo_info.get("stargazers_count", 0)
    forks = repo_info.get("forks_count", 0)
    sections["metadata"] = (
        f"=== Repository: {owner}/{repo} ===\n"
        f"Description: {desc}\n"
        f"Primary Language: {primary_lang}\n"
        f"Stars: {stars} | Forks: {forks}\n"
    )

    readme_parts: List[str] = []
    agent_parts: List[str] = []
    config_parts: List[str] = []
    source_parts: List[str] = []

    for f in selected:
        path = f["path"]
        rank = f["rank"]

        if path in cached_contents:
            text = cached_contents[path]
        else:
            raw = await fetch_file_content(owner, repo, path, ref)
            if detect_binary_content(raw):
                logger.info("Skipping binary content: %s", path)
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                logger.info("Skipping non-UTF-8 file: %s", path)
                continue
            all_contents[path] = text

        text = _truncate(text, MAX_LINES, MAX_CHARS)

        if rank == 1:
            readme_parts.append(f"--- {path} ---\n{text}")
        elif rank == 2:
            agent_parts.append(f"--- {path} ---\n{text}")
        elif rank <= 5:
            config_parts.append(f"--- {path} ---\n{text}")
        else:
            source_parts.append(f"--- {path} ---\n{text}")

    if readme_parts:
        sections["readme"] = "=== README ===\n" + "\n\n".join(readme_parts)
    if agent_parts:
        sections["agent_docs"] = "=== Agent Docs ===\n" + "\n\n".join(agent_parts)
    if config_parts:
        sections["config"] = "=== Project Configuration ===\n" + "\n\n".join(config_parts)
    sections["tree"] = f"=== Directory Structure ===\n{tree_summary}"
    if source_parts:
        sections["source"] = "=== Key Source Files ===\n" + "\n\n".join(source_parts)

    digest = _assemble(sections)

    if len(digest) > MAX_DIGEST_CHARS:
        digest = _apply_compaction(sections, MAX_DIGEST_CHARS)

    return digest, all_contents


# ---------------------------------------------------------------------------
# Truncation and compaction
# ---------------------------------------------------------------------------


def _truncate(content: str, max_lines: int, max_chars: int) -> str:
    """Truncate content by line count or char count, appending marker."""
    lines = content.split("\n")
    if len(lines) > max_lines:
        content = "\n".join(lines[:max_lines]) + "\n... [truncated]"
    if len(content) > max_chars:
        content = content[:max_chars] + "\n... [truncated]"
    return content


def _extract_signatures(content: str) -> str:
    """Keep only import/def/class/export/function lines and decorators."""
    sig_prefixes = ("import ", "from ", "def ", "class ", "export ", "function ", "@")
    lines = content.split("\n")
    kept = [line for line in lines if line.lstrip().startswith(sig_prefixes)]
    return "\n".join(kept) if kept else content[:500]


def _assemble(sections: Dict[str, str]) -> str:
    """Join sections into a single digest string."""
    order = ["metadata", "readme", "agent_docs", "config", "tree", "source"]
    parts = [sections[k] for k in order if k in sections]
    return "\n\n".join(parts)


def _apply_compaction(sections: Dict[str, str], budget: int) -> str:
    """7-step compaction waterfall. Reassemble and re-measure after each step."""
    # Step 1: Truncate oversized files (already done in fetch_and_assemble)
    digest = _assemble(sections)
    if len(digest) <= budget:
        return digest

    # Step 2: Reduce tree depth
    if "tree" in sections:
        lines = sections["tree"].split("\n")
        sections["tree"] = "\n".join(lines[:20]) + "\n... [truncated]"
    digest = _assemble(sections)
    if len(digest) <= budget:
        return digest

    # Step 3: Halve source excerpts
    if "source" in sections:
        half_lines = MAX_LINES // 2
        half_chars = MAX_CHARS // 2
        parts = sections["source"].split("\n--- ")
        new_parts = []
        for part in parts:
            new_parts.append(_truncate(part, half_lines, half_chars))
        sections["source"] = "\n--- ".join(new_parts)
    digest = _assemble(sections)
    if len(digest) <= budget:
        return digest

    # Step 4: Signatures only for source
    if "source" in sections:
        parts = sections["source"].split("\n--- ")
        new_parts = []
        for part in parts:
            header_end = part.find("\n")
            if header_end > 0:
                header = part[:header_end]
                body = part[header_end + 1 :]
                new_parts.append(header + "\n" + _extract_signatures(body))
            else:
                new_parts.append(_extract_signatures(part))
        sections["source"] = "\n--- ".join(new_parts)
    digest = _assemble(sections)
    if len(digest) <= budget:
        return digest

    # Step 5: Drop source files entirely
    sections.pop("source", None)
    digest = _assemble(sections)
    if len(digest) <= budget:
        return digest

    # Step 6: Compact agent docs
    if "agent_docs" in sections:
        sections["agent_docs"] = _truncate(sections["agent_docs"], MAX_LINES, MAX_CHARS)
    digest = _assemble(sections)
    if len(digest) <= budget:
        return digest

    # Step 7: Compact README
    if "readme" in sections:
        sections["readme"] = _truncate(sections["readme"], MAX_LINES, MAX_CHARS)
    digest = _assemble(sections)
    if len(digest) > budget:
        logger.warning(
            "Digest %d chars exceeds budget %d after all compaction steps",
            len(digest),
            budget,
        )
    return digest
