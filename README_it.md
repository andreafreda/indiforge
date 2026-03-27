# 🏛️ IndyForge

[**English**](README.md) | [Italiano]

> "I predatori dell'architettura perduta"

Strumento multi-agente basato su AI che scansiona microservizi e genera automaticamente la documentazione completa dell'architettura.
Controlla la nostra [**Guida per Principianti**](guides/GUIDE_FOR_NEWBIES_it.md) per iniziare!

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1.5-green)](https://langchain-ai.github.io/langgraph)
[![Ollama](https://img.shields.io/badge/LLM-MultiProvider-brightgreen)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 Documentazione
- [Guida per Principianti (Italiano)](guides/GUIDE_FOR_NEWBIES_it.md)

---

## 🚀 Avvio Rapido

```bash
pip install indyforge

# Imposta il tuo provider/lingua localmente (.env)
INDYFORGE_PROVIDER=ollama   # ollama, openai, anthropic, groq, azure
INDYFORGE_LANGUAGE=italian  # o english, french, ecc.

# Singolo repository
indyforge scan ./mio-servizio

# Multi-repository (panoramica di sistema parallela)
indyforge scan ./ordini ./pagamenti ./notifiche
```

## 📦 Cosa genera IndyForge

```
docs/
├── overview.md           # Doc architettura completa (8 sezioni)
├── api.md                # Endpoint API completi
├── events.md             # Flussi di consumatori e produttori
├── sequences.md          # Diagrammi di sequenza Mermaid
├── dependencies.md       # Dipendenze complete del progetto
├── security.md           # Sicurezza, strategie di autenticazione e vulnerabilità
├── config.md             # Impostazioni dell'applicazione dell'ecosistema
└── system-overview.md    # Architettura di sistema cross-repo (solo multi-repo)
```

---

## 🏗️ Architettura: MapReduce a due livelli

IndyForge utilizza un **pattern MapReduce a due livelli** per il massimo parallelismo, orchestrato da LangGraph:

```
Input Multi-Repo
       |
  MAP L1: 1 thread per repository (ThreadPoolExecutor)
  |         |           |
ordini   pagamenti  notifiche
    |
  MAP L2: 6 worker in parallelo con rilevamento automatico dello stack!
  |---------|---------|---------|----------|----------|
Deps       API      Eventi   Sicurezza  Sequenze   Config
    |
  REDUCE L2: aggregatore (bozza di overview.md)
       |
  VERIFICATORE: Controlli rigorosi in più fasi (Messa a terra, Completezza, Accuratezza, Coerenza)
       |--> Loop di riflessione → torna all'Aggregatore (max 3 tentativi se vengono trovate allucinazioni/errori)
       |
REDUCE L1: system-overview.md (mappa cross-repo)
```

---

## 🤖 Anti-Allucinazione e Loop di Riflessione

Per eliminare le allucinazioni degli LLM, IndyForge applica un rigoroso pattern **Source Evidence Manifest**:
1. **Prove dalla sorgente (Source Evidence)**: Ogni worker (`api_worker`, `config_worker`, ecc.) utilizza `file_reader.py` per estrarre solo i file rilevanti, restituendo sia le informazioni estratte che un Manifest di Messa a Terra che registra i file esatti analizzati.
2. **Bozza dell'Aggregatore**: L'aggregatore scrive una bozza iniziale dell'architettura in markdown utilizzando i risultati dei worker.
3. **Controlli del Verificatore**: Il verificatore rigoroso confronta la prova originale (Source Evidence) con il Markdown finalizzato eseguendo:
    - **Controllo di Messa a Terra (Grounding)**: Assicura che nessun endpoint/dipendenza/argomento sia inventato se non presente nei file.
    - **Controllo di Completezza**: Verifica che tutte le 8 sezioni siano popolate.
    - **Controllo di Accuratezza**: Testa la formattazione markdown, le stringhe di versione e la sintassi.
    - **Controllo di Coerenza**: Individua contraddizioni interne.
4. **Correzione**: Se il verificatore rifiuta la bozza, questa torna all'aggregatore con un feedback esplicito.

---

## 💰 Costi e Supporto Multi-Provider

Configurazione tramite `.env` o variabili d'ambiente del sistema (`INDYFORGE_PROVIDER`):
- `ollama` (Locale - 100% Gratuito)
- `openai`
- `anthropic`
- `groq`
- `azure`

---

## 📁 Struttura del Progetto

```
indyforge/
├── src/indyforge/
│   ├── config.py                 # Factory LLM Multi-provider
│   ├── cli.py                    # Punto di ingresso CLI indyforge scan
│   ├── lang.py                   # Dizionari di localizzazione (IT/EN)
│   └── agents/
│       ├── mapreduce_graph.py    # Grafo MapReduce, Aggregatore e Verificatore
│       ├── file_reader.py        # Estrazione sicura dei file e limiti di contesto
│       └── config_worker.py      # Analizzatore di configurazione cross-ecosistema
├── examples/
│   └── orderservice/             # Servizio Spring Boot di esempio
```

---

## 🤝 Contribuire

```bash
git clone https://github.com/andreafreda/indyforge
cd indyforge
pip install -e .
indyforge scan examples/orderservice
```
