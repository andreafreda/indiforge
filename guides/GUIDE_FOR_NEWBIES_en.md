# 👶 IndyForge — Newbie Guide

[English] | [**Italiano** →](GUIDE_FOR_NEWBIES_it.md)

> This guide is for people who have never used IndyForge before. If you're already comfortable with the CLI, check the [README](../README.md) instead — it's more concise.

---

## 🧐 What does IndyForge actually do?

You give it a project folder. It reads the code — all of it — and generates structured Markdown documentation that answers questions like:

- *What does this service do?*
- *Which APIs does it expose? Which services does it call?*
- *What does it publish/consume on Kafka or RabbitMQ?*
- *Are there hardcoded passwords, weak auth, or outdated libraries?*
- *How does the whole ecosystem interconnect?*

It runs **7 specialized AI agents in parallel**, then cross-checks the output for hallucinations before saving anything to disk.

---

## 🛠️ Step 1 — Prerequisites

You need two things:

**1. Python 3.11+**
Check your version:
```bash
python --version
```
If it says `3.10` or lower, [download Python](https://www.python.org/downloads/) and install the latest 3.11+ version.

**2. A language model**

IndyForge works with local models (free) or cloud APIs (paid). Start with local if you're unsure:

**Option A — Local with Ollama (recommended for beginners)**
1. Download and install [Ollama](https://ollama.com/)
2. Open a terminal and pull the default models:
```bash
ollama pull deepseek-coder:6.7b   # code analysis
ollama pull llama3.1:8b            # writing & verification
ollama pull mistral:7b             # security analysis
```

**Option B — Cloud API (if your PC is slow)**
Create a `.env` file in the project folder and add your key:
```env
# OpenAI
INDYFORGE_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Anthropic Claude
INDYFORGE_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```
For all provider options, see [`.env.example`](../.env.example).

---

## 💾 Step 2 — Installation

```bash
# Clone the project
git clone https://github.com/andreafreda/indyforge
cd indyforge

# Install
pip install -e .
```

Done. Now `indyforge` is available as a command anywhere on your system.

**Verify the installation:**
```bash
indyforge --help
```

---

## 🌍 Step 3 — Set your language

If you want documentation generated in Italian, create a `.env` file:
```env
INDYFORGE_LANGUAGE=italian
```
Default is English. This only affects the *generated docs*, not the tool's CLI messages.

---

## 🚀 Step 4 — Your first scan

Make sure Ollama is running (if you chose Option A), then:

```bash
indyforge scan path/to/your/microservice
```

You'll see a live progress view showing all 7 workers launching in parallel, each printing when it finishes with elapsed time and a `[N/7]` counter. The whole scan usually takes **1–10 minutes** depending on the project size and your model/hardware.

**What it outputs:**
```
✅ Docs → ./docs/overview.md
  └─ ./docs/api.md
  └─ ./docs/events.md
  └─ ./docs/security.md
  └─ ./docs/sequences.md
  └─ ./docs/dependencies.md
  └─ ./docs/config.md
  └─ ./docs/tree.md
```

To save docs to a custom folder:
```bash
indyforge scan ./my-service --out ./output/my-service-docs
```

---

## 📖 Step 5 — Reading the output

Open `overview.md` first — it's the master document that links everything together. Then dive into specific files based on what you need:

| I want to know... | Open this file |
|---|---|
| What the service does and its architecture | `overview.md` |
| All API endpoints | `api.md` |
| Kafka / RabbitMQ / event flows | `events.md` |
| Security risks, hardcoded secrets | `security.md` |
| How request flows work end-to-end | `sequences.md` |
| All dependencies + versions | `dependencies.md` |
| Config keys (passwords masked) | `config.md` |
| Which files are in the project and what they do | `tree.md` |

---

## 🔀 Scanning multiple services at once

```bash
indyforge scan ./orders ./payments ./notifications
```

This generates everything above **for each service**, plus a bonus `system-overview.md` that maps how all the services interact with each other.

---

## ♻️ Crash recovery

If the scan crashes halfway through, just re-run the same command. IndyForge will ask:

```
💾 Found previous checkpoint data. Do you want to use it?
```

Say **Y** and it will skip already-completed workers and resume from where it stopped. Say **N** to start fresh.

To always start fresh (ignoring any saved checkpoint):
```bash
indyforge scan ./my-service --no-cache
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---|---|
| `'indyforge' is not recognized` | Run `pip install -e .` again and make sure Python's Scripts folder is in your PATH |
| `Connection refused` / Ollama error | Start the Ollama app and run `ollama serve` in a terminal, then retry |
| Slow scan | Use a cloud provider (`INDYFORGE_PROVIDER=openai`) or a smaller local model (`INDYFORGE_MODEL=llama3.2:3b`) |
| AI writes things not in the code | Normal on huge repos — use a larger model via API for best accuracy |
| Scan stuck / frozen | Press Ctrl+C — checkpoints are saved so you can resume |

---

**Happy Reverse Engineering! 🏛️**
