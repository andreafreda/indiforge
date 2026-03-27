# 🏛️ IndyForge

[English] | [**Italiano** →](README_it.md)

> *"Raiders of the Lost Architecture"*

AI-powered multi-agent tool that scans any microservice (or entire ecosystem) and generates full, verified architecture documentation — automatically.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1.5-green)](https://langchain-ai.github.io/langgraph)
[![LLM](https://img.shields.io/badge/LLM-MultiProvider-brightgreen)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🚀 Quickstart

```bash
# 1. Install
git clone https://github.com/andreafreda/indyforge && cd indyforge
pip install -e .

# 2. Configure (.env — copy from .env.example)
INDYFORGE_PROVIDER=ollama        # ollama | openai | anthropic | groq | azure
INDYFORGE_LANGUAGE=english       # english | italian

# 3. Run
indyforge scan ./my-service                              # single repo
indyforge scan ./orders ./payments ./notifications       # multi-repo
indyforge scan ./my-service --no-cache                   # force fresh scan
```

> **New to IndyForge?** Read the [Newbie Guide →](guides/GUIDE_FOR_NEWBIES_en.md) for a step-by-step walkthrough.

---

## 📦 Output

| File | Contents |
|---|---|
| `overview.md` | Full architecture doc — purpose, dependencies, API, events, security, config, sequences, file tree |
| `api.md` | REST / SOAP / gRPC / GraphQL endpoints |
| `events.md` | Kafka / RabbitMQ / SNS consumers & producers |
| `security.md` | Auth strategies, CVE hints, exposed secrets |
| `sequences.md` | Mermaid sequence diagrams |
| `dependencies.md` | All project dependencies with versions |
| `config.md` | Config keys table (secrets masked) |
| `tree.md` | Annotated project file tree |
| `system-overview.md` | Cross-repo architecture map *(multi-repo only)* |

---

## 🏗️ How It Works

IndyForge uses a **two-level MapReduce** orchestrated by LangGraph:

```
Input (one or more repos)
      │
  L1 MAP ─── ThreadPoolExecutor (1 thread/repo)
      │
  L2 MAP ─── 7 workers in parallel (LangGraph fan-out)
              ├── deps_worker      → dependencies
              ├── api_worker       → REST/SOAP/gRPC/GraphQL endpoints
              ├── event_worker     → Kafka/RabbitMQ/SQS topics
              ├── security_worker  → CVE, auth, secrets
              ├── sequence_worker  → Mermaid diagrams
              ├── config_worker    → config keys
              └── tree_worker      → annotated file tree
      │
  REDUCE L2 ── aggregator (writes overview.md)
      │
  VERIFIER ─── grounding · completeness · accuracy · consistency
      │         └── reflection loop → back to aggregator (max 3 retries)
      │
  REDUCE L1 ── system-overview.md (cross-repo)
```

### Anti-Hallucination
Every worker produces a **Source Evidence Manifest** (which files it read, how many chars). The verifier compares the manifest against the generated markdown and rejects any claim not grounded in the source files.

### Crash Recovery
Workers checkpoint their results to `.indyforge_cache/` inside the scanned repo. If a scan crashes mid-way, re-running it will ask whether to reuse the checkpoint — skipping already-completed workers. On successful completion, the cache is automatically deleted.

---

## ⚙️ Configuration

All configuration is via `.env` (copy `.env.example`). Key variables:

| Variable | Default | Description |
|---|---|---|
| `INDYFORGE_PROVIDER` | `ollama` | LLM backend: `ollama`, `openai`, `anthropic`, `groq`, `azure` |
| `INDYFORGE_LANGUAGE` | `english` | Output language: `english`, `italian` |
| `INDYFORGE_MODEL` | — | Override: use one model for all agents |
| `INDYFORGE_CODE_MODEL` | `deepseek-coder:6.7b` | Code analysis agent |
| `INDYFORGE_WRITER_MODEL` | `llama3.1:8b` | Writer / aggregator agent |
| `INDYFORGE_SECURITY_MODEL` | `mistral:7b` | Security analysis agent |
| `INDYFORGE_VERIFIER_MODEL` | `llama3.1:8b` | Verifier / reflection agent |

Prompts live in `config/prompts/` and keyword patterns in `config/keywords/` — no code changes needed to customize them.

---

## 📁 Project Structure

```
indyforge/
├── config/
│   ├── prompts/          # LLM prompt templates (.txt) — one per agent
│   └── keywords/         # File patterns & search keywords (.yaml) — one per language
├── src/indyforge/
│   ├── config.py         # Multi-provider LLM factory + _StringLLMWrapper
│   ├── config_loader.py  # Prompt & keyword loader with path caching
│   ├── cli.py            # `indyforge scan` entry point
│   ├── lang.py           # EN/IT localization strings
│   └── agents/
│       ├── mapreduce_graph.py  # Main graph, workers, aggregator, verifier
│       ├── file_reader.py      # Safe file extraction with context limits
│       └── config_worker.py    # Cross-ecosystem config file analyzer
├── examples/
│   └── orderservice/     # Sample Spring Boot service for testing
├── guides/               # Step-by-step guides for new users
├── tests/                # Unit tests
└── .env.example          # Fully documented configuration reference
```

---

## 🤝 Contributing

```bash
git clone https://github.com/andreafreda/indyforge
cd indyforge
pip install -e .
indyforge scan examples/orderservice   # smoke test
pytest tests/                          # run unit tests
```
