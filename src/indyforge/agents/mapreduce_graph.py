
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
import concurrent.futures
import operator
import os
import click
import hashlib
import json

from indyforge.config import CODE_MODEL, WRITER_MODEL, SECURITY_MODEL, VERIFIER_MODEL, make_llm, LANGUAGE
from indyforge.lang import t
from indyforge.agents.config_worker import config_worker as _config_worker
from indyforge.agents.file_reader import (
    read_files_by_pattern, read_files_with_manifest,
    DEPS_PATTERNS, API_PATTERNS, API_KEYWORDS,
    EVENT_PATTERNS, EVENT_KEYWORDS,
    SEQUENCE_PATTERNS, SEQUENCE_KEYWORDS,
    SECURITY_PATTERNS, SECURITY_KEYWORDS,
)

def detect_stack(repo_path: str) -> str:
    stack = []
    try:
        files = os.listdir(repo_path)
        if "pom.xml" in files or "build.gradle" in files: stack.append("Java/Spring")
        if "package.json" in files: stack.append("Node.js/TypeScript")
        if "requirements.txt" in files or "pyproject.toml" in files: stack.append("Python")
        if "go.mod" in files: stack.append("Go")
        if any(f.endswith(".csproj") or f.endswith(".sln") for f in files): stack.append(".NET/C#")
    except Exception:
        pass
    return " + ".join(stack) if stack else "Unknown stack"

CACHE_DIR = ".indyforge_cache"

def get_repo_hash(repo_path: str) -> str:
    hasher = hashlib.md5()
    for root, dirs, files in os.walk(repo_path):
        if any(ign in root for ign in [".git", "node_modules", "target", "build", "__pycache__", ".venv"]):
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
    os.makedirs(CACHE_DIR, exist_ok=True)
    repo_name = os.path.basename(os.path.abspath(state["repo_path"]))
    repo_hash = state.get("repo_hash", "nohash")
    
    cache_file = os.path.join(CACHE_DIR, f"{repo_name}_{worker_name}_{repo_hash}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            click.echo(f"  ⚡ [cache] Ripristinato {worker_name} dal checkpoint locale!")
            return cached_data
        except Exception:
            pass
            
    result = worker_fn(state)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f)
    except Exception:
        pass
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
    result = code_llm.invoke(f"""
    Analyze these dependency/build files from a microservice (Stack: {state.get("stack_context", "Unknown")}):

    {file_contents}

    Extract ALL dependencies with their exact versions.
    Return a markdown table: | Package | Version | Scope | Risk |
    - Version: exact version from the file (e.g. 3.2.1, ^2.0.0, >=1.5)
    - Scope: compile, runtime, test, dev, optional
    - Risk: flag known CVEs or outdated major versions
    If no dependency files were found, state that clearly.
    All your output MUST be in {LANGUAGE}.
    """)
    click.echo(t("deps_done"))
    return {"deps_result": result, "source_evidence": [manifest]}

def api_worker(state: RepoState) -> RepoState:
    click.echo(t("api_extract"))
    file_contents, manifest = read_files_with_manifest(
        "api_worker", state["repo_path"], API_PATTERNS, keywords=API_KEYWORDS, max_total_chars=20000
    )
    result = code_llm.invoke(f"""
    Analyze these source files from a microservice (Stack: {state.get("stack_context", "Unknown")}):

    {file_contents}

    Extract ALL API endpoints (REST, SOAP, gRPC, GraphQL, JMX).
    Return a markdown table: | Method | Path | Description | Auth Required |
    Include: HTTP method, full path, what it does, whether auth is needed.
    If no API endpoints were found, state that clearly.
    All your output MUST be in {LANGUAGE}.
    """)
    click.echo(t("api_done"))
    return {"api_result": result, "source_evidence": [manifest]}

def event_worker(state: RepoState) -> RepoState:
    click.echo(t("event_extract"))
    file_contents, manifest = read_files_with_manifest(
        "event_worker", state["repo_path"], EVENT_PATTERNS, keywords=EVENT_KEYWORDS, max_total_chars=20000
    )
    result = code_llm.invoke(f"""
    Analyze these source and config files from a microservice (Stack: {state.get("stack_context", "Unknown")}):

    {file_contents}

    Extract ALL event/messaging configuration:
    - Message broker type (Kafka, RabbitMQ, JMS, SQS, Azure Service Bus, etc.)
    - Topics/queues: name, purpose
    - Consumers: which classes listen to which topics
    - Producers: which classes publish to which topics
    Return structured markdown with tables.
    If no event/messaging code was found, state that clearly.
    All your output MUST be in {LANGUAGE}.
    """)
    click.echo(t("event_done"))
    return {"event_result": result, "source_evidence": [manifest]}

def security_worker(state: RepoState) -> RepoState:
    click.echo(t("security_extract"))
    file_contents, manifest = read_files_with_manifest(
        "security_worker", state["repo_path"], SECURITY_PATTERNS, keywords=SECURITY_KEYWORDS, max_total_chars=20000
    )
    result = security_llm.invoke(f"""
    Analyze these source and config files for security concerns (Stack: {state.get("stack_context", "Unknown")}):

    {file_contents}

    Identify:
    - Authentication type (JWT, OAuth2, Basic, API Key, etc.)
    - Authorization patterns (@PreAuthorize, [Authorize], etc.)
    - Known security risks (hardcoded secrets, missing CORS, weak hashing)
    - CVE flags on dependencies if visible
    - Recommendations for improvement
    Return structured markdown.
    If no security-related code was found, state that clearly.
    All your output MUST be in {LANGUAGE}.
    """)
    click.echo(t("security_done"))
    return {"security_result": result, "source_evidence": [manifest]}

def sequence_worker(state: RepoState) -> RepoState:
    click.echo(t("sequence_extract"))
    file_contents, manifest = read_files_with_manifest(
        "sequence_worker", state["repo_path"], SEQUENCE_PATTERNS, keywords=SEQUENCE_KEYWORDS, max_total_chars=20000
    )
    result = code_llm.invoke(f"""
    Analyze these source files from a microservice (Stack: {state.get("stack_context", "Unknown")}):

    {file_contents}

    Build Mermaid sequence diagrams for the top 3 most important endpoints.
    Trace the full call flow: controller -> service -> repository/DB -> event broker.
    Return valid Mermaid sequenceDiagram syntax for each endpoint.
    If not enough code was found, state that clearly.
    All your output MUST be in {LANGUAGE} (except for mermaid syntax which remains in English).
    """)
    click.echo(t("sequence_done"))
    return {"sequence_result": result, "source_evidence": [manifest]}

def config_worker(state: RepoState) -> RepoState:
    click.echo(t("config_extract"))
    result = _config_worker(state)
    click.echo(t("config_done"))
    return result

def aggregator(state: RepoState) -> RepoState:
    it = state.get("iteration", 0) + 1
    click.echo(t("aggregator_write", it=it))
    overview = writer_llm.invoke(f"""
    Generate overview.md for microservice at {state["repo_path"]}.

    ## 1. Project Purpose
    Describe technically the service (language, framework, main responsibilities, exposed ports). Do not use marketing jargon, hyperboles, or generic words. Keep it strictly technical.
    ## 2. General Architecture
    ## 3. Full Dependencies
    {state["deps_result"]}
    ## 4. REST/SOAP/gRPC/GraphQL API Endpoints
    {state["api_result"]}
    ## 5. Event Consumers & Producers
    {state["event_result"]}
    ## 6. Security & Auth
    {state["security_result"]}
    ## 7. Configuration Keys
    {state["config_result"]}
    ## 8. Sequence Diagrams
    {state["sequence_result"]}

    All your text and titles MUST be in {LANGUAGE}.
    """)
    click.echo(t("aggregator_done"))
    return {"overview_md": overview, "iteration": it}

def verifier(state: RepoState) -> RepoState:
    click.echo(t("verifier_check"))

    # Build the source evidence summary for the verifier
    evidence = "\n".join(state.get("source_evidence", []))

    critique = verifier_llm.invoke(f"""
    You are a STRICT verifier. Your job is to catch hallucinations and errors.

    ## SOURCE EVIDENCE (what was ACTUALLY found in the repo files)
    {evidence}

    ## GENERATED OVERVIEW
    {state["overview_md"]}

    ## VERIFICATION RULES
    1. GROUNDING CHECK: Does the overview mention dependencies, endpoints, topics,
       or services that are NOT present in the source evidence? If a worker found
       "No relevant files", the overview MUST NOT invent content for that section.
    2. COMPLETENESS CHECK: Does the overview cover all sections?
       (Purpose, Architecture, Dependencies, API, Events, Security, Config, Sequences)
    3. ACCURACY CHECK: Are dependency versions correct? Are endpoint paths accurate?
    4. CONSISTENCY CHECK: Do the sections contradict each other?

    Return ONLY valid JSON (no markdown fencing):
    {{
        "valid": true or false,
        "hallucinations": ["list of things mentioned in overview but NOT in source evidence"],
        "missing": ["list of things in source evidence but NOT in overview"],
        "errors": ["other errors found"]
    }}
    """)

    # Parse the validation result robustly
    import re, json
    valid = False
    match = re.search(r'\{[^{}]*"valid"\s*:\s*(true|false)[^{}]*\}', critique, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            parsed = json.loads(match.group())
            valid = parsed.get("valid", False) is True
        except (json.JSONDecodeError, AttributeError):
            valid = False

    if valid:
        click.echo(t("verifier_pass"))
    else:
        click.echo(t("verifier_retry"))
        # Log what the verifier found
        if match:
            try:
                parsed = json.loads(match.group())
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
        ("deps_worker", deps_worker),
        ("api_worker", api_worker),
        ("event_worker", event_worker),
        ("security_worker", security_worker),
        ("sequence_worker", sequence_worker),
        ("config_worker", config_worker),
        ("aggregator", aggregator),
        ("verifier", verifier),
    ]:
        if name not in ["aggregator", "verifier"]:
            # Capture fn in closure correctly using default argument
            def make_cached(worker_name, worker_fn):
                def wrapped(state: RepoState):
                    return run_worker_with_cache(state, worker_name, worker_fn)
                return wrapped
            g.add_node(name, make_cached(name, fn))
        else:
            g.add_node(name, fn)

    for w in ["deps_worker", "api_worker", "event_worker", "security_worker", "sequence_worker", "config_worker"]:
        g.add_edge("__start__", w)
        g.add_edge(w, "aggregator")

    g.add_edge("aggregator", "verifier")
    g.add_conditional_edges("verifier", should_retry, {"aggregator": "aggregator", END: END})
    return g.compile()

# ── L1 MapReduce ───────────────────────────────────────────
def scan_repo(repo_path: str) -> dict:
    click.echo(t("scan_repo", repo_path=repo_path))
    repo_hash = get_repo_hash(repo_path)
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
        "source_evidence": [],
        "overview_md": "",
        "iteration": 0,
        "check_valid": False,
    })
    return {
        "repo": repo_path,
        "docs": result["overview_md"],
        "deps": result.get("deps_result", ""),
        "api": result.get("api_result", ""),
        "events": result.get("event_result", ""),
        "security": result.get("security_result", ""),
        "sequences": result.get("sequence_result", ""),
        "config": result.get("config_result", ""),
    }

def map_repos(state: SystemState) -> SystemState:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(scan_repo, state["repo_paths"]))
    return {"repo_docs": results}

def reduce_system(state: SystemState) -> SystemState:
    click.echo(t("reduce_build"))
    all_docs = "\n\n---\n\n".join([f"# {d['repo']}\n{d['docs']}" for d in state["repo_docs"]])
    system_doc = writer_llm.invoke(f"""
    Generate system-overview.md for this microservice ecosystem:
    {all_docs}
    Include: service mesh, shared Kafka topics, cross-repo risks.
    All your output MUST be in {LANGUAGE}.
    """)
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
