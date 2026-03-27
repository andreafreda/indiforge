
from typing import TypedDict, List, Annotated, Optional
from langgraph.graph import StateGraph, END
import concurrent.futures
import operator
import os
import re
import click
import hashlib
import json
import time
import threading

from indyforge.config import CODE_MODEL, WRITER_MODEL, SECURITY_MODEL, VERIFIER_MODEL, make_llm, LANGUAGE, MAX_CONCURRENCY
from indyforge.lang import t
from indyforge.config_loader import load_prompt
from indyforge.agents.config_worker import config_worker as _config_worker
from indyforge.agents.file_reader import (
    read_files_with_manifest,
    DEPS_PATTERNS, API_PATTERNS, API_KEYWORDS,
    EVENT_PATTERNS, EVENT_KEYWORDS,
    SEQUENCE_PATTERNS, SEQUENCE_KEYWORDS,
    SECURITY_PATTERNS, SECURITY_KEYWORDS,
)

def detect_stack(repo_path: str) -> str:
    import re
    stack = []
    try:
        files = os.listdir(repo_path)

        # ── Java / Kotlin ────────────────────────────────────────
        if "pom.xml" in files:
            version = "?"
            try:
                content = open(os.path.join(repo_path, "pom.xml"), encoding="utf-8", errors="ignore").read()
                m = re.search(r"<java\.version>([^<]+)<", content) or \
                    re.search(r"<source>([\d.]+)<", content) or \
                    re.search(r"<release>([\d.]+)<", content)
                if m: version = m.group(1)
            except Exception: pass
            stack.append(f"Java {version} / Spring (Maven)")
        if "build.gradle" in files or "build.gradle.kts" in files:
            fname = "build.gradle.kts" if "build.gradle.kts" in files else "build.gradle"
            version = "?"
            try:
                content = open(os.path.join(repo_path, fname), encoding="utf-8", errors="ignore").read()
                m = re.search(r'sourceCompatibility\s*=\s*["\']?([\d.]+)', content) or \
                    re.search(r'jvmTarget\s*=\s*["\']([\d.]+)', content)
                if m: version = m.group(1)
            except Exception: pass
            stack.append(f"Java/Kotlin {version} / Spring (Gradle)")

        # ── .NET ─────────────────────────────────────────────────
        csproj_files = [f for f in files if f.endswith(".csproj")]
        sln_files    = [f for f in files if f.endswith(".sln")]
        if csproj_files or sln_files:
            version = "?"
            try:
                fname = csproj_files[0] if csproj_files else sln_files[0]
                content = open(os.path.join(repo_path, fname), encoding="utf-8", errors="ignore").read()
                m = re.search(r"<TargetFramework>([^<]+)<", content)
                if m: version = m.group(1)         # e.g. net10.0, net8.0
            except Exception: pass
            # Walk subdirs if not found at root
            if version == "?":
                for root, dirs, fs in os.walk(repo_path):
                    for f in fs:
                        if f.endswith(".csproj"):
                            try:
                                content = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
                                m = re.search(r"<TargetFramework>([^<]+)<", content)
                                if m: version = m.group(1); break
                            except Exception: pass
                    if version != "?": break
            stack.append(f".NET C# ({version})")

        # ── Node.js / TypeScript ─────────────────────────────────
        if "package.json" in files:
            version = "?"
            try:
                import json
                data = json.load(open(os.path.join(repo_path, "package.json"), encoding="utf-8", errors="ignore"))
                engines = data.get("engines", {}).get("node", "")
                if engines: version = engines
                elif "typescript" in data.get("devDependencies", {}):
                    version = data["devDependencies"]["typescript"]
            except Exception: pass
            label = "Node.js/TypeScript" if os.path.exists(os.path.join(repo_path, "tsconfig.json")) else "Node.js"
            stack.append(f"{label} ({version})" if version != "?" else label)

        # ── Python ───────────────────────────────────────────────
        if "pyproject.toml" in files:
            version = "?"
            try:
                content = open(os.path.join(repo_path, "pyproject.toml"), encoding="utf-8", errors="ignore").read()
                m = re.search(r'python_requires\s*=\s*["\']([^"\']+)', content)
                if m: version = m.group(1)
            except Exception: pass
            stack.append(f"Python ({version})" if version != "?" else "Python")
        elif "requirements.txt" in files:
            stack.append("Python")

        # ── Go ───────────────────────────────────────────────────
        if "go.mod" in files:
            version = "?"
            try:
                content = open(os.path.join(repo_path, "go.mod"), encoding="utf-8", errors="ignore").read()
                m = re.search(r"^go ([\d.]+)", content, re.MULTILINE)
                if m: version = m.group(1)
            except Exception: pass
            stack.append(f"Go ({version})" if version != "?" else "Go")

        # ── Rust ─────────────────────────────────────────────────
        if "Cargo.toml" in files:
            stack.append("Rust")

        # ── Dockerfile fallback ───────────────────────────────────
        if not stack and "Dockerfile" in files:
            try:
                content = open(os.path.join(repo_path, "Dockerfile"), encoding="utf-8", errors="ignore").read()
                m = re.search(r"^FROM\s+(\S+)", content, re.MULTILINE)
                if m: stack.append(f"Docker ({m.group(1)})")
            except Exception: pass

    except Exception:
        pass
    return " + ".join(stack) if stack else "Unknown stack"

# ── Tree builder constants ──────────────────────────────────
MAX_TREE_DEPTH = 6
MAX_TREE_FILES = 300
SOURCE_EXTENSIONS = frozenset([
    '.cs', '.java', '.kt', '.py', '.ts', '.tsx', '.js', '.jsx', '.go', '.rs',
    '.proto', '.yaml', '.yml', '.json', '.xml', '.toml', '.gradle',
    '.properties', '.md', '.txt', '.config', '.csproj', '.sln', '.env',
])

def _build_tree_structure(repo_path: str) -> tuple:
    """
    Walk the repo directory tree (respecting SKIP_DIRS) and return:
      - tree_str    : ASCII+emoji tree of all non-skipped files
      - samples_str : first ~150 chars of each source file for LLM context
    """
    from indyforge.agents.file_reader import SKIP_DIRS

    tree_lines = []
    file_samples = {}   # rel_path -> snippet
    file_count = [0]    # mutable counter for closure

    def _walk(dir_path: str, prefix: str, depth: int):
        if depth > MAX_TREE_DEPTH or file_count[0] >= MAX_TREE_FILES:
            return
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return

        dirs  = [e for e in entries
                 if os.path.isdir(os.path.join(dir_path, e)) and e not in SKIP_DIRS]
        files = [e for e in entries
                 if os.path.isfile(os.path.join(dir_path, e))]
        all_entries = dirs + files

        for i, entry in enumerate(all_entries):
            entry_path = os.path.join(dir_path, entry)
            is_last    = (i == len(all_entries) - 1)
            connector  = "└── " if is_last else "├── "
            extension  = "    " if is_last else "│   "

            if os.path.isdir(entry_path):
                tree_lines.append(f"{prefix}{connector}📁 {entry}/")
                _walk(entry_path, prefix + extension, depth + 1)
            else:
                tree_lines.append(f"{prefix}{connector}📄 {entry}")
                file_count[0] += 1
                ext = os.path.splitext(entry)[1].lower()
                if ext in SOURCE_EXTENSIONS and len(file_samples) < 60:
                    try:
                        with open(entry_path, "r", errors="ignore") as f:
                            snippet = f.read(200).strip().replace("\n", " ")[:150]
                        file_samples[os.path.relpath(entry_path, repo_path)] = snippet
                    except Exception:
                        pass
                if file_count[0] >= MAX_TREE_FILES:
                    tree_lines.append(f"{prefix}    ... [limit of {MAX_TREE_FILES} files reached]")
                    return

    repo_name = os.path.basename(os.path.abspath(repo_path))
    tree_lines.append(f"📁 {repo_name}/")
    _walk(repo_path, "", 0)

    tree_str     = "\n".join(tree_lines)
    samples_str  = "\n".join(f"- {rel}: `{snip}`" for rel, snip in file_samples.items())
    return tree_str, samples_str

# ── Progress tracking ─────────────────────────────────────────
TOTAL_PARALLEL_WORKERS = 7  # deps, api, event, security, sequence, config, tree

class _AtomicCounter:
    """Thread-safe counter — tracks how many parallel workers have finished."""
    def __init__(self, total: int):
        self._n = 0
        self._total = total
        self._lock = threading.Lock()

    def increment(self) -> str:
        with self._lock:
            self._n += 1
            return f"[{self._n}/{self._total}]"

_COUNTERS_BY_REPO = {}

def _format_elapsed(seconds: float) -> str:
    """Convert seconds to a human-readable string: '3.2s' or '1m 23s'."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"

CACHE_DIR_NAME = ".indyforge_cache"

def get_repo_hash(repo_path: str) -> str:
    from indyforge.agents.file_reader import SKIP_DIRS
    hasher = hashlib.md5()
    for root, dirs, files in os.walk(repo_path):
        rel_root = os.path.relpath(root, repo_path)
        parts = rel_root.replace("\\", "/").split("/")
        if any(skip in parts for skip in SKIP_DIRS):
            continue
        for name in sorted(files):
            filepath = os.path.join(root, name)
            try:
                hasher.update(filepath.encode())
                hasher.update(str(os.path.getmtime(filepath)).encode())
            except Exception:
                pass
    return hasher.hexdigest()

def run_worker_with_cache(state, worker_name: str, worker_fn):
    # Cache is stored inside the repo being scanned, not the process cwd
    cache_dir = os.path.join(state["repo_path"], CACHE_DIR_NAME)
    os.makedirs(cache_dir, exist_ok=True)
    repo_name = os.path.basename(os.path.abspath(state["repo_path"]))
    repo_hash = state.get("repo_hash", "nohash")

    cache_file = os.path.join(cache_dir, f"{repo_name}_{worker_name}_{repo_hash}.json")
    
    counter = _COUNTERS_BY_REPO.get(state["repo_path"])
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            progress = counter.increment() if counter else ""
            click.echo(t("cache_hit", worker=worker_name, progress=progress))
            return cached_data
        except Exception:
            pass

    t_start = time.time()
    result = worker_fn(state)
    elapsed = _format_elapsed(time.time() - t_start)

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f)
    except Exception:
        pass

    progress = counter.increment() if counter else ""
    click.echo(t("worker_done_timed", worker=worker_name, elapsed=elapsed, progress=progress))
    return result

# ── Per-agent LLMs ─────────────────────────────────────────
code_llm     = make_llm(CODE_MODEL)
writer_llm   = make_llm(WRITER_MODEL)
security_llm = make_llm(SECURITY_MODEL)
verifier_llm = make_llm(VERIFIER_MODEL)

# ── State ──────────────────────────────────────────────────
class RepoState(TypedDict):
    repo_path: str
    stack_context: str
    repo_hash: str
    file_list: List[str]
    deps_result: str
    api_result: str
    event_result: str
    security_result: str
    sequence_result: str
    config_result: str
    tree_result: str
    source_evidence: Annotated[List[str], operator.add]  # manifests from each worker
    overview_md: str
    iteration: int
    check_valid: bool

class SystemState(TypedDict):
    repo_paths: List[str]
    repo_docs: Annotated[List[dict], operator.add]
    system_overview: str

# ── L2 Workers ─────────────────────────────────────────────
def deps_worker(state: RepoState) -> RepoState:
    click.echo(t("deps_extract"))
    file_contents, manifest = read_files_with_manifest(
        "deps_worker", state["repo_path"], DEPS_PATTERNS, keywords=None, max_total_chars=20000
    )
    result = code_llm.invoke(load_prompt(
        "deps_worker",
        stack_context=state.get("stack_context", "Unknown"),
        file_contents=file_contents,
        LANGUAGE=LANGUAGE,
    ))

    return {"deps_result": result, "source_evidence": [manifest]}

def api_worker(state: RepoState) -> RepoState:
    click.echo(t("api_extract"))
    file_contents, manifest = read_files_with_manifest(
        "api_worker", state["repo_path"], API_PATTERNS, keywords=API_KEYWORDS, max_total_chars=20000
    )
    result = code_llm.invoke(load_prompt(
        "api_worker",
        stack_context=state.get("stack_context", "Unknown"),
        file_contents=file_contents,
        LANGUAGE=LANGUAGE,
    ))

    return {"api_result": result, "source_evidence": [manifest]}

def event_worker(state: RepoState) -> RepoState:
    click.echo(t("event_extract"))
    file_contents, manifest = read_files_with_manifest(
        "event_worker", state["repo_path"], EVENT_PATTERNS, keywords=EVENT_KEYWORDS, max_total_chars=20000
    )
    result = code_llm.invoke(load_prompt(
        "event_worker",
        stack_context=state.get("stack_context", "Unknown"),
        file_contents=file_contents,
        LANGUAGE=LANGUAGE,
    ))

    return {"event_result": result, "source_evidence": [manifest]}

def security_worker(state: RepoState) -> RepoState:
    click.echo(t("security_extract"))
    file_contents, manifest = read_files_with_manifest(
        "security_worker", state["repo_path"], SECURITY_PATTERNS, keywords=SECURITY_KEYWORDS, max_total_chars=20000
    )
    result = security_llm.invoke(load_prompt(
        "security_worker",
        stack_context=state.get("stack_context", "Unknown"),
        file_contents=file_contents,
        LANGUAGE=LANGUAGE,
    ))

    return {"security_result": result, "source_evidence": [manifest]}

def sequence_worker(state: RepoState) -> RepoState:
    click.echo(t("sequence_extract"))
    file_contents, manifest = read_files_with_manifest(
        "sequence_worker", state["repo_path"], SEQUENCE_PATTERNS, keywords=SEQUENCE_KEYWORDS, max_total_chars=20000
    )
    result = code_llm.invoke(load_prompt(
        "sequence_worker",
        stack_context=state.get("stack_context", "Unknown"),
        file_contents=file_contents,
        LANGUAGE=LANGUAGE,
    ))

    return {"sequence_result": result, "source_evidence": [manifest]}

def tree_worker(state: RepoState) -> RepoState:
    click.echo(t("tree_extract"))
    tree_str, file_samples = _build_tree_structure(state["repo_path"])
    result = code_llm.invoke(load_prompt(
        "tree_worker",
        tree_str=tree_str,
        file_samples=file_samples if file_samples else "(no source files sampled)",
        LANGUAGE=LANGUAGE,
    ))
    manifest = f"[tree_worker] {tree_str.count(chr(10)) + 1} tree lines built."

    return {"tree_result": result, "source_evidence": [manifest]}

def config_worker(state: RepoState) -> RepoState:
    click.echo(t("config_extract"))
    return _config_worker(state)

def aggregator(state: RepoState) -> RepoState:
    it = state.get("iteration", 0) + 1
    click.echo(t("aggregator_write", it=it))
    overview = writer_llm.invoke(load_prompt(
        "aggregator",
        repo_path=state["repo_path"],
        stack_context=state.get("stack_context", "Unknown stack"),
        deps_result=state["deps_result"],
        api_result=state["api_result"],
        event_result=state["event_result"],
        security_result=state["security_result"],
        config_result=state["config_result"],
        sequence_result=state["sequence_result"],
        tree_result=state["tree_result"],
        LANGUAGE=LANGUAGE,
    ))
    click.echo(t("aggregator_done"))
    return {"overview_md": overview, "iteration": it}

def verifier(state: RepoState) -> RepoState:
    click.echo(t("verifier_check"))

    # Build the source evidence summary for the verifier
    evidence = "\n".join(state.get("source_evidence", []))

    critique = verifier_llm.invoke(load_prompt(
        "verifier",
        evidence=evidence,
        overview_md=state["overview_md"],
    ))

    # Parse the validation result — try full parse first, then regex fallback
    valid = False
    parsed = None

    # Attempt 1: parse the whole response as JSON (model may return clean JSON)
    try:
        parsed = json.loads(critique.strip())
    except (json.JSONDecodeError, AttributeError):
        pass

    # Attempt 2: extract the first {...} block that contains "valid" (handles nested arrays)
    if parsed is None:
        match = re.search(r'\{.*?"valid"\s*:\s*(true|false).*?\}', critique, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                parsed = json.loads(match.group())
            except (json.JSONDecodeError, AttributeError):
                pass

    if parsed and isinstance(parsed, dict):
        valid = parsed.get("valid", False) is True

    if valid:
        click.echo(t("verifier_pass"))
    else:
        click.echo(t("verifier_retry"))
        if parsed and isinstance(parsed, dict):
            try:
                for h in parsed.get("hallucinations", []):
                    click.echo(t("hallucination", h=h))
                for e in parsed.get("errors", []):
                    click.echo(t("error", e=e))
            except Exception:
                pass
    return {"check_valid": valid}

def should_retry(state: RepoState) -> str:
    if state["check_valid"] or state.get("iteration", 0) >= 3:
        return END
    return "aggregator"

# ── Build L2 Graph ─────────────────────────────────────────
def build_repo_graph():
    g = StateGraph(RepoState)
    for name, fn in [
        ("deps_worker",     deps_worker),
        ("api_worker",      api_worker),
        ("event_worker",    event_worker),
        ("security_worker", security_worker),
        ("sequence_worker", sequence_worker),
        ("config_worker",   config_worker),
        ("tree_worker",     tree_worker),
        ("aggregator",      aggregator),
        ("verifier",        verifier),
    ]:
        if name not in ["aggregator", "verifier"]:
            def make_cached(worker_name, worker_fn):
                def wrapped(state: RepoState):
                    return run_worker_with_cache(state, worker_name, worker_fn)
                return wrapped
            g.add_node(name, make_cached(name, fn))
        else:
            g.add_node(name, fn)

    for w in ["deps_worker", "api_worker", "event_worker", "security_worker", "sequence_worker", "config_worker", "tree_worker"]:
        g.add_edge("__start__", w)
        g.add_edge(w, "aggregator")

    g.add_edge("aggregator", "verifier")
    g.add_conditional_edges("verifier", should_retry, {"aggregator": "aggregator", END: END})
    return g.compile()

# ── L1 MapReduce ───────────────────────────────────────────
def scan_repo(repo_path: str) -> dict:
    click.echo(t("scan_repo", repo_path=repo_path))
    repo_hash = get_repo_hash(repo_path)

    _COUNTERS_BY_REPO[repo_path] = _AtomicCounter(TOTAL_PARALLEL_WORKERS)
    t_scan_start = time.time()
    
    if MAX_CONCURRENCY == 1:
        click.echo(t("phase_workers_seq", n=TOTAL_PARALLEL_WORKERS))
        config_dict = {"recursion_limit": 50, "max_concurrency": MAX_CONCURRENCY}
    elif MAX_CONCURRENCY > 1:
        click.echo(t("phase_workers_conc", n=TOTAL_PARALLEL_WORKERS, c=MAX_CONCURRENCY))
        config_dict = {"recursion_limit": 50, "max_concurrency": MAX_CONCURRENCY}
    else:
        click.echo(t("phase_workers", n=TOTAL_PARALLEL_WORKERS))
        config_dict = {"recursion_limit": 50}

    result = build_repo_graph().invoke({
        "repo_path": repo_path,
        "stack_context": detect_stack(repo_path),
        "repo_hash": repo_hash,
        "file_list": [],
        "deps_result": "",
        "api_result": "",
        "event_result": "",
        "security_result": "",
        "sequence_result": "",
        "config_result": "",
        "tree_result": "",
        "source_evidence": [],
        "overview_md": "",
        "iteration": 0,
        "check_valid": False,
    }, config=config_dict)

    _COUNTERS_BY_REPO.pop(repo_path, None)
    click.echo(t("scan_complete", elapsed=_format_elapsed(time.time() - t_scan_start)))

    return {
        "repo": repo_path,
        "docs": result["overview_md"],
        "deps": result.get("deps_result", ""),
        "api": result.get("api_result", ""),
        "events": result.get("event_result", ""),
        "security": result.get("security_result", ""),
        "sequences": result.get("sequence_result", ""),
        "config": result.get("config_result", ""),
        "tree": result.get("tree_result", ""),
    }

def map_repos(state: SystemState) -> SystemState:
    max_workers = MAX_CONCURRENCY if MAX_CONCURRENCY > 0 else None
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(scan_repo, state["repo_paths"]))
    return {"repo_docs": results}

def reduce_system(state: SystemState) -> SystemState:
    click.echo(t("reduce_build"))
    all_docs = "\n\n---\n\n".join([f"# {d['repo']}\n{d['docs']}" for d in state["repo_docs"]])
    system_doc = writer_llm.invoke(load_prompt(
        "reduce_system",
        all_docs=all_docs,
        LANGUAGE=LANGUAGE,
    ))
    click.echo(t("reduce_done"))
    return {"system_overview": system_doc}

def build_system_graph():
    g = StateGraph(SystemState)
    g.add_node("map_repos", map_repos)
    g.add_node("reduce_system", reduce_system)
    g.add_edge("__start__", "map_repos")
    g.add_edge("map_repos", "reduce_system")
    g.add_edge("reduce_system", END)
    return g.compile()

def run(repo_paths: list, verbose: bool = False) -> dict:
    if len(repo_paths) == 1:
        return scan_repo(repo_paths[0])
    return build_system_graph().invoke({"repo_paths": repo_paths, "repo_docs": []})
