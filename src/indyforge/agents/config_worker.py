
from indyforge.config import CODE_MODEL, make_llm, LANGUAGE
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
                # Skip node_modules, .git, build dirs
                if any(x in path for x in ["node_modules", ".git", "build", "target", "dist", "bin", "obj"]):
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
        return {"config_result": "_No configuration files found._"}

    # Build content grouped by ecosystem
    grouped = {}
    for path, data in configs.items():
        eco = data["ecosystem"]
        if eco not in grouped:
            grouped[eco] = []
        grouped[eco].append((path, data["content"]))

    all_content = ""
    for eco, files in grouped.items():
        all_content += f"\n## Ecosystem: {eco.upper()}\n"
        for path, content in files:
            segment = f"\n### {path}\n```\n{content[:3000]}\n```\n"
            if len(all_content) + len(segment) > 12000:
                all_content += "\n\n[WARNING: Global limit of 12000 characters reached. Some configurations were truncated.]\n"
                break
            all_content += segment
        if "> 12000" in all_content or len(all_content) > 12000:
            break

    result = code_llm.invoke(f"""
    Analyze these configuration files from a microservice:

    {all_content}

    For EVERY configuration key found, generate a markdown table:
    | Key | Value | Purpose | Notes |

    Rules:
    - Mask passwords/secrets/tokens as [MASKED]
    - Purpose: plain English explanation of what this key does
    - Notes: warn hardcoded values, missing env vars, non-default ports, risky settings
    - Group output by ecosystem (Spring, .NET, Node, Infra, etc.)

    Example rows:
    | ConnectionStrings.DefaultConnection | [MASKED] | SQL Server connection string for main DB | ⚠️ Should use env var |
    | Logging.LogLevel.Default | Warning | Minimum log level for all namespaces | Consider Debug in dev |
    | ASPNETCORE_ENVIRONMENT | Production | ASP.NET Core runtime environment | ✅ Correctly set |
    | spring.kafka.consumer.max-poll-records | 100 | Max Kafka records per poll | Tune for throughput |

    All your output MUST be in {LANGUAGE}.
    """)

    return {"config_result": result}
