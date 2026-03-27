
import os
import glob
from typing import List, Dict, Optional

# ── Directories to always skip ─────────────────────────────
SKIP_DIRS = [
    "node_modules", ".git", "__pycache__", "build", "target",
    "dist", "bin", "obj", ".gradle", ".mvn", ".idea", ".vscode",
    "venv", ".venv", "env",
]

# ── File patterns by analysis type ─────────────────────────

DEPS_PATTERNS = [
    "**/pom.xml",
    "**/build.gradle", "**/build.gradle.kts",
    "**/package.json",
    "**/requirements.txt", "**/pyproject.toml", "**/setup.py", "**/setup.cfg",
    "**/go.mod",
    "**/*.csproj", "**/packages.config", "**/Directory.Packages.props",
    "**/Gemfile",
    "**/Cargo.toml",
]

API_PATTERNS = [
    # Source code (controllers, routes, endpoints)
    "**/*.java", "**/*.kt",
    "**/*.py",
    "**/*.ts", "**/*.js",
    "**/*.cs",
    "**/*.go",
    # API definitions
    "**/*.proto",
    "**/*.wsdl",
    "**/*.graphql", "**/*.gql",
    "**/openapi.yml", "**/openapi.yaml", "**/swagger.json", "**/swagger.yml",
]

# Keywords that indicate a source file contains API endpoints
API_KEYWORDS = [
    # Java / Spring
    "@RestController", "@Controller", "@RequestMapping",
    "@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping", "@PatchMapping",
    "@WebService", "@WebMethod",
    # .NET
    "[ApiController]", "[HttpGet]", "[HttpPost]", "[HttpPut]", "[HttpDelete]",
    "[Route(", "ControllerBase",
    # Python / Flask / FastAPI / Django
    "@app.route", "@router.", "APIView", "ViewSet",
    "@api_view", "path(", "re_path(",
    # Node / Express
    "router.get", "router.post", "router.put", "router.delete",
    "app.get(", "app.post(", "app.put(", "app.delete(",
    # Go
    "HandleFunc", "http.Handle",
    # gRPC
    "service ", "rpc ",
]

EVENT_PATTERNS = [
    "**/*.java", "**/*.kt",
    "**/*.py",
    "**/*.ts", "**/*.js",
    "**/*.cs",
    "**/*.go",
    # Config files that contain event broker configuration
    "**/application.yml", "**/application.yaml", "**/application.properties",
    "**/docker-compose.yml", "**/docker-compose.yaml",
    "**/appsettings.json",
]

# Keywords that indicate a source file contains event/messaging code
EVENT_KEYWORDS = [
    # Kafka
    "@KafkaListener", "KafkaTemplate", "KafkaProducer", "KafkaConsumer",
    "kafka", "KAFKA",
    # RabbitMQ
    "@RabbitListener", "RabbitTemplate", "amqp", "AMQP",
    "RabbitMQ", "rabbitmq",
    # JMS
    "@JmsListener", "JmsTemplate", "jms",
    # AWS SQS / SNS
    "SqsClient", "SnsClient", "sqs", "sns",
    # Azure Service Bus
    "ServiceBusClient", "servicebus",
    # Generic
    "MessageListener", "EventHandler", "event_handler",
    "consumer", "producer", "subscriber", "publisher",
]

SEQUENCE_PATTERNS = [
    "**/*.java", "**/*.kt",
    "**/*.py",
    "**/*.ts", "**/*.js",
    "**/*.cs",
    "**/*.go",
]

# Keywords that indicate a source file is a controller/service/repository
SEQUENCE_KEYWORDS = [
    # Controllers
    "@RestController", "@Controller", "[ApiController]",
    "@app.route", "@router.", "router.get", "HandleFunc",
    # Services
    "@Service", "@Component", "@Injectable",
    "Service", "service",
    # Repositories / DAOs
    "@Repository", "Repository", "repository",
    "JpaRepository", "CrudRepository",
    "DbContext", "DbSet",
]

SECURITY_PATTERNS = [
    "**/*.java", "**/*.kt",
    "**/*.py",
    "**/*.ts", "**/*.js",
    "**/*.cs",
    "**/*.go",
    # Config files with security settings
    "**/application.yml", "**/application.yaml", "**/application.properties",
    "**/appsettings.json",
    "**/web.config",
    # Dependency manifests (for CVE checking)
    "**/pom.xml", "**/build.gradle", "**/package.json",
    "**/requirements.txt", "**/*.csproj",
]

SECURITY_KEYWORDS = [
    # Auth
    "JWT", "jwt", "OAuth", "oauth", "Bearer",
    "@PreAuthorize", "@Secured", "@RolesAllowed",
    "spring-security", "SecurityFilterChain", "WebSecurityConfigurerAdapter",
    # .NET
    "[Authorize]", "AddAuthentication", "AddJwtBearer",
    "IdentityServer",
    # Python
    "flask_login", "flask_jwt", "django.contrib.auth",
    "fastapi.security",
    # Node
    "passport", "jsonwebtoken", "express-jwt",
    # General
    "CORS", "cors", "CSRF", "csrf",
    "bcrypt", "argon2", "password", "secret",
    "SSL", "TLS", "certificate",
    "encrypt", "decrypt", "hash",
]


def _should_skip(path: str) -> bool:
    """Check if a path contains any directory we want to skip."""
    parts = path.replace("\\", "/").split("/")
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
            if _should_skip(path):
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


def read_files_by_pattern(
    repo_path: str,
    patterns: List[str],
    keywords: Optional[List[str]] = None,
    max_chars_per_file: int = 3000,
    max_total_chars: int = 15000,
) -> str:
    """
    Find files matching glob patterns, optionally filter by keyword presence,
    read their contents and return a formatted string for LLM consumption.
    Kept for backward compatibility (config_worker uses this).
    """
    found_files = _find_matching_files(repo_path, patterns, keywords)
    return _build_content_string(repo_path, found_files, max_chars_per_file, max_total_chars)


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

