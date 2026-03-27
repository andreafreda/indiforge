"""
config_loader.py — Loads prompts and keywords/patterns from the config/ directory.

Config directory is resolved in this order:
  1. <repo_root>/config/   (editable install, running from source)
  2. <cwd>/config/         (fallback when cwd is the repo root)
"""

import os
import glob
from typing import List, Dict

import yaml


def _find_config_dir() -> str:
    """
    Locate the config/ directory.
    Priority: package-relative path → cwd-relative path.
    """
    # src/indyforge/config_loader.py → ../../config
    pkg_relative = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "config")
    )
    if os.path.isdir(pkg_relative):
        return pkg_relative

    cwd_relative = os.path.join(os.getcwd(), "config")
    if os.path.isdir(cwd_relative):
        return cwd_relative

    raise FileNotFoundError(
        f"IndyForge config/ directory not found. "
        f"Expected at: {pkg_relative} or {cwd_relative}"
    )

# Resolve once at module import time — avoids repeated filesystem I/O on every call
_CONFIG_DIR_CACHE: str = _find_config_dir()


# ── Prompts ───────────────────────────────────────────────────────────────────

def load_prompt(name: str, **kwargs) -> str:
    """
    Load config/prompts/<name>.txt and format it with the given kwargs.

    Example:
        load_prompt("api_worker", stack_context="Java", file_contents="...", LANGUAGE="Italian")
    """
    config_dir = _CONFIG_DIR_CACHE
    path = os.path.join(config_dir, "prompts", f"{name}.txt")

    try:
        with open(path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Prompt template not found: {path}\n"
            f"Available prompts: {_list_prompts(config_dir)}"
        )

    try:
        return template.format_map(kwargs)
    except KeyError as e:
        raise KeyError(
            f"Missing variable {e} when rendering prompt '{name}'. "
            f"Provided keys: {list(kwargs.keys())}"
        )


def _list_prompts(config_dir: str) -> List[str]:
    prompts_dir = os.path.join(config_dir, "prompts")
    if not os.path.isdir(prompts_dir):
        return []
    return [os.path.splitext(f)[0] for f in os.listdir(prompts_dir) if f.endswith(".txt")]


# ── Keywords & Patterns ───────────────────────────────────────────────────────

def _load_yaml(path: str) -> Dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        import warnings
        warnings.warn(f"Could not load keyword file {path}: {e}")
        return {}


def _load_language_files(config_dir: str) -> List[Dict]:
    """Load all per-language YAML files from config/keywords/ (excluding common.yaml)."""
    kw_dir = os.path.join(config_dir, "keywords")
    result = []
    for path in sorted(glob.glob(os.path.join(kw_dir, "*.yaml"))):
        if os.path.basename(path) == "common.yaml":
            continue
        result.append(_load_yaml(path))
    return result


def _load_common(config_dir: str) -> Dict:
    """Load config/keywords/common.yaml which contains glob patterns."""
    path = os.path.join(config_dir, "keywords", "common.yaml")
    return _load_yaml(path)


def load_keywords(analysis_type: str) -> List[str]:
    """
    Merge keyword lists for a given analysis type across all language files.

    Args:
        analysis_type: one of 'api_keywords', 'event_keywords',
                       'security_keywords', 'sequence_keywords'

    Returns:
        Deduplicated list of keywords in insertion order.
    """
    config_dir = _CONFIG_DIR_CACHE
    merged: List[str] = []
    seen: set = set()
    for lang_data in _load_language_files(config_dir):
        for kw in lang_data.get(analysis_type, []):
            if kw not in seen:
                seen.add(kw)
                merged.append(kw)
    return merged


def load_patterns(analysis_type: str) -> List[str]:
    """
    Load glob patterns for a given analysis type from common.yaml.

    Args:
        analysis_type: one of 'deps_patterns', 'api_patterns', 'event_patterns',
                       'sequence_patterns', 'security_patterns'

    Returns:
        List of glob pattern strings.
    """
    config_dir = _CONFIG_DIR_CACHE
    return _load_common(config_dir).get(analysis_type, [])
