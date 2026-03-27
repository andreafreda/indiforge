# 🏛️ IndyForge

[**English** →](README.md) | [Italiano]

> *"I predatori dell'architettura perduta"*

Strumento multi-agente AI che scansiona qualsiasi microservizio (o un intero ecosistema) e genera documentazione architetturale completa e verificata — automaticamente.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1.5-green)](https://langchain-ai.github.io/langgraph)
[![LLM](https://img.shields.io/badge/LLM-MultiProvider-brightgreen)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🚀 Avvio Rapido

```bash
# 1. Installazione
git clone https://github.com/andreafreda/indyforge && cd indyforge
pip install -e .

# 2. Configurazione (.env — copia da .env.example)
INDYFORGE_PROVIDER=ollama        # ollama | openai | anthropic | groq | azure
INDYFORGE_LANGUAGE=italian       # english | italian

# 3. Lancio
indyforge scan ./mio-servizio                            # singolo repo
indyforge scan ./ordini ./pagamenti ./notifiche          # multi-repo
indyforge scan ./mio-servizio --no-cache                 # scansione fresca forzata
```

> **Prima volta con IndyForge?** Leggi la [Guida per Principianti →](guides/GUIDE_FOR_NEWBIES_it.md) per un percorso guidato passo-passo.

---

## 📦 Output generato

| File | Contenuto |
|---|---|
| `overview.md` | Doc architettura completa — scopo, dipendenze, API, eventi, sicurezza, config, sequenze, albero file |
| `api.md` | Endpoint REST / SOAP / gRPC / GraphQL |
| `events.md` | Consumer & producer Kafka / RabbitMQ / SNS |
| `security.md` | Strategie di autenticazione, CVE, segreti esposti |
| `sequences.md` | Diagrammi di sequenza Mermaid |
| `dependencies.md` | Tutte le dipendenze del progetto con versioni |
| `config.md` | Tabella chiavi di configurazione (segreti mascherati) |
| `tree.md` | Alberatura del progetto annotata |
| `system-overview.md` | Mappa architetturale cross-repo *(solo multi-repo)* |

---

## 🏗️ Come funziona

IndyForge usa un **MapReduce a due livelli** orchestrato da LangGraph:

```
Input (uno o più repo)
      │
  L1 MAP ─── ThreadPoolExecutor (1 thread/repo)
      │
  L2 MAP ─── 7 worker in parallelo (LangGraph fan-out)
              ├── deps_worker      → dipendenze
              ├── api_worker       → endpoint REST/SOAP/gRPC/GraphQL
              ├── event_worker     → topic Kafka/RabbitMQ/SQS
              ├── security_worker  → CVE, auth, segreti
              ├── sequence_worker  → diagrammi Mermaid
              ├── config_worker    → chiavi di configurazione
              └── tree_worker      → alberatura annotata
      │
  REDUCE L2 ── aggregator (scrive overview.md)
      │
  VERIFIER ─── grounding · completezza · accuratezza · coerenza
      │         └── reflection loop → torna all'aggregator (max 3 tentativi)
      │
  REDUCE L1 ── system-overview.md (cross-repo)
```

### Anti-Allucinazione
Ogni worker produce un **Source Evidence Manifest** (quali file ha letto, quanti caratteri). Il verifier confronta il manifest con il markdown generato e rifiuta qualunque affermazione non supportata dai file sorgente.

### Crash Recovery
I worker salvano i propri risultati in `.indyforge_cache/` dentro il repo scansionato. Se la scan si interrompe a metà, rilanciandola viene chiesto se riusare il checkpoint — saltando i worker già completati. A scan riuscita, la cache viene eliminata automaticamente.

---

## ⚙️ Configurazione

Tutta la configurazione avviene via `.env` (copia `.env.example`). Variabili principali:

| Variabile | Default | Descrizione |
|---|---|---|
| `INDYFORGE_PROVIDER` | `ollama` | Backend LLM: `ollama`, `openai`, `anthropic`, `groq`, `azure` |
| `INDYFORGE_LANGUAGE` | `english` | Lingua output: `english`, `italian` |
| `INDYFORGE_MODEL` | — | Override: usa un solo modello per tutti gli agenti |
| `INDYFORGE_CODE_MODEL` | `deepseek-coder:6.7b` | Agente analisi codice |
| `INDYFORGE_WRITER_MODEL` | `llama3.1:8b` | Agente writer / aggregator |
| `INDYFORGE_SECURITY_MODEL` | `mistral:7b` | Agente analisi sicurezza |
| `INDYFORGE_VERIFIER_MODEL` | `llama3.1:8b` | Agente verifier / reflection |

I prompt si trovano in `config/prompts/` e i pattern keyword in `config/keywords/` — personalizzabili senza toccare il codice Python.

---

## 📁 Struttura del progetto

```
indyforge/
├── config/
│   ├── prompts/          # Template prompt LLM (.txt) — uno per agente
│   └── keywords/         # Pattern file e keyword di ricerca (.yaml) — uno per linguaggio
├── src/indyforge/
│   ├── config.py         # Factory LLM multi-provider + _StringLLMWrapper
│   ├── config_loader.py  # Loader prompt & keyword con path caching
│   ├── cli.py            # Entry point `indyforge scan`
│   ├── lang.py           # Stringhe di localizzazione IT/EN
│   └── agents/
│       ├── mapreduce_graph.py  # Grafo principale, worker, aggregator, verifier
│       ├── file_reader.py      # Estrazione file sicura con limiti di contesto
│       └── config_worker.py    # Analizzatore config cross-ecosistema
├── examples/
│   └── orderservice/     # Servizio Spring Boot di esempio per i test
├── guides/               # Guide passo-passo per nuovi utenti
├── tests/                # Unit test
└── .env.example          # Riferimento di configurazione completamente documentato
```

---

## 🤝 Contribuire

```bash
git clone https://github.com/andreafreda/indyforge
cd indyforge
pip install -e .
indyforge scan examples/orderservice   # smoke test
pytest tests/                          # esegui i test unitari
```
