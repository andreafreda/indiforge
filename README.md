# 🏛️ IndyForge

> "Raiders of the Lost Architecture"

AI-powered multi-agent tool that scans any microservice(s) and generates full architecture documentation automatically.
Check our [**Newbie Guide**](guides/GUIDE_FOR_NEWBIES_en.md) to get started!

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1.5-green)](https://langchain-ai.github.io/langgraph)
[![Ollama](https://img.shields.io/badge/LLM-MultiProvider-brightgreen)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 Documentation
- [English Newbie Guide](guides/GUIDE_FOR_NEWBIES_en.md)
- [Guida per Principianti (Italiano)](guides/GUIDE_FOR_NEWBIES_it.md)

---

## 🚀 Quickstart

```bash
pip install indyforge

# Set your provider/language locally (.env)
INDYFORGE_PROVIDER=ollama   # ollama, openai, anthropic, groq, azure
INDYFORGE_LANGUAGE=english  # or italian, french, etc.

# Single repo
indyforge scan ./my-service

# Multi-repo (parallel system overview)
indyforge scan ./orders ./payments ./notifications
```

## 📦 What IndyForge Generates

```
docs/
├── overview.md           # Full architecture doc (8 sections)
├── api.md                # Complete API endpoints
├── events.md             # Consumers and Producers flows
├── sequences.md          # Mermaid sequence diagrams
├── dependencies.md       # Full project dependencies
├── security.md           # Security, auth strategies & vulnerabilities
├── config.md             # Ecosystem application settings
└── system-overview.md    # Cross-repo system architecture (multi-repo only)
```

---

## 🏗️ Architecture: Two-Level MapReduce

IndyForge uses a **two-level MapReduce pattern** for maximum parallelism, orchestrated by LangGraph:

```
Multi-Repo Input
       |
  MAP L1: 1 thread/repo (ThreadPoolExecutor)
  |         |           |
orders   payments  notifications
    |
  MAP L2: 6 workers in parallel with automatic Stack Detection!
  |---------|---------|---------|----------|----------|
Deps       API      Events   Security  Sequences   Config
    |
  REDUCE L2: aggregator (drafts overview.md)
       |
  VERIFIER: Strict multi-step checks (Grounding, Completeness, Accuracy, Consistency)
       |--> Reflection loop → back to Aggregator (max 3 retries if hallucinations/errors found)
       |
REDUCE L1: system-overview.md (cross-repo map)
```

---

## 🤖 Anti-Hallucination & Reflection Loop

To eliminate LLM hallucinations, IndyForge enforces a strict **Source Evidence Manifest** pattern:
1. **Source Evidence**: Every worker (`api_worker`, `config_worker`, etc.) uses `file_reader.py` to extract only relevant files, returning both the extracted information and a Grounding Manifest logging the exact files analyzed.
2. **Aggregator Draft**: The aggregator writes an initial architecture markdown using worker results.
3. **Verifier Checks**: The strict verifier compares the original Source Evidence against the finalized Markdown performing:
    - **Grounding Check**: Ensuring no endpoint/dependency/topic is invented if not present in the files.
    - **Completeness Check**: Verifies all 8 sections are populated.
    - **Accuracy Check**: Tests markdown formatting, version strings, and syntax.
    - **Consistency Check**: Spots internal contradictions.
4. **Correction**: If the verifier rejects the draft, it loops back to the aggregator with explicit feedback.

---

## 💰 Cost & Multi-Provider Support

Configure via `.env` or system environment (`INDYFORGE_PROVIDER`):
- `ollama` (Local - 100% Free)
- `openai`
- `anthropic`
- `groq`
- `azure`

---

## 📁 Project Structure

```
indyforge/
├── src/indyforge/
│   ├── config.py                 # Multi-provider LLM Factory
│   ├── cli.py                    # indyforge scan entry point
│   ├── lang.py                   # Localization dictionaries (IT/EN)
│   └── agents/
│       ├── mapreduce_graph.py    # MapReduce graph, Aggregator & Verifier
│       ├── file_reader.py        # Safe file extraction and Context limits
│       └── config_worker.py      # Cross-ecosystem configuration analyzer
├── examples/
│   └── orderservice/             # Sample Spring Boot service
```

---

## 🤝 Contributing

```bash
git clone https://github.com/andreafreda/indyforge
cd indyforge
pip install -e .
indyforge scan examples/orderservice
```
