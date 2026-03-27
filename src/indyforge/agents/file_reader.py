
import os
import glob
from typing import List, Dict, Optional

from indyforge.config_loader import load_keywords, load_patterns

# ── Directories to always skip ─────────────────────────────
SKIP_DIRS = [
    "node_modules", ".git", "__pycache__", "build", "target",
    "dist", "bin", "obj", ".gradle", ".mvn", ".idea", ".vscode",
    "venv", ".venv", "env", ".indyforge_cache",
]

# ── File patterns and keywords — loaded from config/ ─────────────────────────
# Edit config/keywords/*.yaml and config/keywords/common.yaml to customise.

DEPS_PATTERNS     = load_patterns("deps_patterns")
API_PATTERNS      = load_patterns("api_patterns")
EVENT_PATTERNS    = load_patterns("event_patterns")
SEQUENCE_PATTERNS = load_patterns("sequence_patterns")
SECURITY_PATTERNS = load_patterns("security_patterns")

API_KEYWORDS      = load_keywords("api_keywords")
EVENT_KEYWORDS    = load_keywords("event_keywords")
SEQUENCE_KEYWORDS = load_keywords("sequence_keywords")
SECURITY_KEYWORDS = load_keywords("security_keywords")


def _should_skip(path: str, repo_path: str) -> bool:
    """Check if a path contains any directory we want to skip (relative to repo to avoid skipping parent dirs)."""
    rel = os.path.relpath(path, repo_path)
    parts = rel.replace("\\", "/").split("/")
    return any(skip in parts for skip in SKIP_DIRS)


def _find_matching_files(
    repo_path: str,
    patterns: List[str],
    keywords: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Find files matching patterns, optionally filtered by keywords."""
    found_files: Dict[str, str] = {}

    for pattern in patterns:
        full_pattern = f"{repo_path}/{pattern}"
        matches = glob.glob(full_pattern, recursive=True)
        for path in matches:
            if _should_skip(path, repo_path):
                continue
            if path in found_files:
                continue
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            if keywords:
                content_lower = content.lower()
                if not any(kw.lower() in content_lower for kw in keywords):
                    continue

            found_files[path] = content

    return found_files


def _build_content_string(
    repo_path: str,
    found_files: Dict[str, str],
    max_chars_per_file: int = 3000,
    max_total_chars: int = 15000,
) -> str:
    """Format file contents for LLM consumption."""
    if not found_files:
        return "_No relevant files found._"

    output_parts = []
    total_chars = 0

    for path, content in found_files.items():
        rel_path = os.path.relpath(path, repo_path)
        truncated = content[:max_chars_per_file]
        if len(content) > max_chars_per_file:
            truncated += f"\n... [truncated, {len(content)} chars total]"

        entry = f"### {rel_path}\n```\n{truncated}\n```\n"

        if total_chars + len(entry) > max_total_chars:
            output_parts.append(
                f"\n⚠️ Truncated: {len(found_files) - len(output_parts)} more files not shown "
                f"(total char limit {max_total_chars} reached)."
            )
            break

        output_parts.append(entry)
        total_chars += len(entry)

    return "\n".join(output_parts)


def _build_manifest(
    worker_name: str,
    repo_path: str,
    found_files: Dict[str, str],
    keywords: Optional[List[str]] = None,
) -> str:
    """
    Build a compact evidence manifest listing which files were found,
    their sizes, and which keywords matched. Used by the verifier
    to cross-check the LLM output against reality.
    """
    if not found_files:
        return f"[{worker_name}] No relevant files found."

    lines = [f"[{worker_name}] {len(found_files)} file(s) found:"]

    for path, content in found_files.items():
        rel_path = os.path.relpath(path, repo_path)
        size = len(content)

        # Find which keywords actually matched in this file
        matched_kw = []
        if keywords:
            content_lower = content.lower()
            matched_kw = [kw for kw in keywords if kw.lower() in content_lower]

        kw_str = f" | keywords: {', '.join(matched_kw[:10])}" if matched_kw else ""
        lines.append(f"  - {rel_path} ({size} chars){kw_str}")

    return "\n".join(lines)



def read_files_with_manifest(
    worker_name: str,
    repo_path: str,
    patterns: List[str],
    keywords: Optional[List[str]] = None,
    max_chars_per_file: int = 3000,
    max_total_chars: int = 15000,
) -> tuple:
    """
    Find and read files, returning BOTH the content for the LLM prompt
    AND a compact evidence manifest for the verifier.

    Returns:
        (content_str, manifest_str) — content for LLM, manifest for verifier
    """
    found_files = _find_matching_files(repo_path, patterns, keywords)
    content = _build_content_string(repo_path, found_files, max_chars_per_file, max_total_chars)
    manifest = _build_manifest(worker_name, repo_path, found_files, keywords)
    return content, manifest

