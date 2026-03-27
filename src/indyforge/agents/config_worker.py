
from indyforge.config import CODE_MODEL, make_llm, LANGUAGE
from indyforge.config_loader import load_prompt
from indyforge.agents.file_reader import SKIP_DIRS
import os, glob

code_llm = make_llm(CODE_MODEL)

# ── Config file patterns per ecosystem ────────────────────
CONFIG_PATTERNS = {

    # Spring Boot / Java
    "spring": [
        "**/application.yml", "**/application.yaml",
        "**/application.properties",
        "**/application-dev.yml", "**/application-prod.yml",
        "**/application-staging.yml",
        "**/bootstrap.yml", "**/bootstrap.properties",
    ],

    # .NET / ASP.NET Core
    "dotnet": [
        "**/appsettings.json",
        "**/appsettings.Development.json",
        "**/appsettings.Production.json",
        "**/appsettings.Staging.json",
        "**/web.config",
        "**/app.config",
        "**/*.csproj",             # NuGet deps + target framework
    ],

    # Node / TypeScript
    "node": [
        "**/.env", "**/.env.example", "**/.env.local",
        "**/.env.development", "**/.env.production",
        "**/config.js", "**/config.ts",
        "**/config.json",
    ],

    # Python
    "python": [
        "**/settings.py",          # Django
        "**/config.py",
        "**/pyproject.toml",
        "**/setup.cfg",
        "**/.env",
    ],

    # Go
    "go": [
        "**/config.yaml", "**/config.yml",
        "**/config.json",
        "**/.env",
    ],

    # Infrastructure / Deploy
    "infra": [
        "**/docker-compose.yml", "**/docker-compose.yaml",
        "**/docker-compose.override.yml",
        "**/Dockerfile",
        "**/kubernetes/*.yml", "**/k8s/*.yml",
        "**/helm/**/values.yml", "**/helm/**/values.yaml",
        "**/.github/workflows/*.yml",  # CI/CD env vars
    ],
}

# ── Secret detection ───────────────────────────────────────
SECRET_KEYWORDS = [
    "password", "secret", "token", "api_key", "apikey",
    "private_key", "credentials", "auth", "pwd", "passwd"
]

def should_mask(key: str) -> bool:
    return any(s in key.lower() for s in SECRET_KEYWORDS)

def find_config_files(repo_path: str) -> dict:
    """Find all config files across all ecosystems."""
    found = {}
    for ecosystem, patterns in CONFIG_PATTERNS.items():
        for pattern in patterns:
            matches = glob.glob(f"{repo_path}/{pattern}", recursive=True)
            for path in matches:
                # Skip ignored directories using shared SKIP_DIRS (path component check)
                rel = os.path.relpath(path, repo_path)
                parts = rel.replace("\\", "/").split("/")
                if any(skip in parts for skip in SKIP_DIRS):
                    continue
                try:
                    with open(path, "r", errors="ignore") as f:
                        found[path] = {"ecosystem": ecosystem, "content": f.read()}
                except Exception:
                    pass
    return found

def config_worker(state: dict) -> dict:
    """
    Reads ALL config files across ecosystems and generates
    a documented table: key, value (masked if secret), purpose, notes.
    """
    configs = find_config_files(state["repo_path"])

    if not configs:
        return {"config_result": "_No configuration files found._", "source_evidence": ["[config_worker] No config files found."]}

    # Build content grouped by ecosystem
    grouped = {}
    for path, data in configs.items():
        eco = data["ecosystem"]
        if eco not in grouped:
            grouped[eco] = []
        grouped[eco].append((path, data["content"]))

    MAX_CHARS = 20000
    all_content = ""
    truncated = False
    for eco, files in grouped.items():
        if truncated:
            break
        eco_block = f"\n## Ecosystem: {eco.upper()}\n"
        for path, content in files:
            segment = f"\n### {path}\n```\n{content[:3000]}\n```\n"
            if len(all_content) + len(eco_block) + len(segment) > MAX_CHARS:
                all_content += eco_block
                all_content += "\n[Truncated: character limit reached, remaining files omitted.]\n"
                truncated = True
                break
            eco_block += segment
        if not truncated:
            all_content += eco_block

    result = code_llm.invoke(load_prompt(
        "config_worker",
        all_content=all_content,
        LANGUAGE=LANGUAGE,
    ))

    # Build evidence manifest for the verifier (like all other workers)
    manifest_lines = [f"[config_worker] {len(configs)} config file(s) found:"]
    for path in configs:
        rel_path = os.path.relpath(path, state["repo_path"])
        eco = configs[path]["ecosystem"]
        size = len(configs[path]["content"])
        manifest_lines.append(f"  - {rel_path} ({size} chars) [{eco}]")
    manifest = "\n".join(manifest_lines)

    return {"config_result": result, "source_evidence": [manifest]}
