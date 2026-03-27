# 👶 IndyForge — Guida per Principianti

[**English** →](GUIDE_FOR_NEWBIES_en.md) | [Italiano]

> Questa guida è per chi non ha mai usato IndyForge. Se sei già a tuo agio con la CLI, leggi il [README](../README_it.md) — è più sintetico.

---

## 🧐 Cosa fa concretamente IndyForge?

Gli dai una cartella di progetto. Lui legge tutto il codice e genera documentazione Markdown strutturata che risponde a domande come:

- *A cosa serve questo servizio?*
- *Quali API espone? Quali servizi chiama?*
- *Cosa pubblica/consuma su Kafka o RabbitMQ?*
- *Ci sono password hardcodate, autenticazioni deboli o librerie obsolete?*
- *Come si interconnette l'intero ecosistema?*

Lancia **7 agenti AI specializzati in parallelo**, poi verifica l'output alla ricerca di allucinazioni prima di salvare qualsiasi cosa su disco.

---

## 🛠️ Passo 1 — Prerequisiti

Ti servono due cose:

**1. Python 3.11+**
Controlla la tua versione:
```bash
python --version
```
Se dice `3.10` o inferiore, [scarica Python](https://www.python.org/downloads/) e installa l'ultima versione 3.11+.

**2. Un modello linguistico**

IndyForge funziona con modelli locali (gratuiti) o API cloud (a pagamento). Inizia con il locale se non sei sicuro:

**Opzione A — Locale con Ollama (consigliata per principianti)**
1. Scarica e installa [Ollama](https://ollama.com/)
2. Apri un terminale e scarica i modelli di default:
```bash
ollama pull deepseek-coder:6.7b   # analisi codice
ollama pull llama3.1:8b            # scrittura e verifica
ollama pull mistral:7b             # analisi sicurezza
```

**Opzione B — API Cloud (se il tuo PC è lento)**
Crea un file `.env` nella cartella del progetto e aggiungi la tua chiave:
```env
# OpenAI
INDYFORGE_PROVIDER=openai
OPENAI_API_KEY=sk-la-tua-chiave

# Anthropic Claude
INDYFORGE_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-la-tua-chiave
```
Per tutte le opzioni di provider, vedi [`.env.example`](../.env.example).

---

## 💾 Passo 2 — Installazione

```bash
# Clona il progetto
git clone https://github.com/andreafreda/indyforge
cd indyforge

# Installa
pip install -e .
```

Fatto. Ora `indyforge` è disponibile come comando ovunque sul tuo sistema.

**Verifica l'installazione:**
```bash
indyforge --help
```

---

## 🌍 Passo 3 — Imposta la tua lingua

Se vuoi la documentazione generata in Italiano, crea un file `.env`:
```env
INDYFORGE_LANGUAGE=italian
```
Il default è Inglese. Questo influisce solo sui *documenti generati*, non sui messaggi CLI dello strumento.

---

## 🚀 Passo 4 — La tua prima scansione

Assicurati che Ollama sia in esecuzione (se hai scelto l'Opzione A), poi:

```bash
indyforge scan percorso/del/tuo/microservizio
```

Vedrai una vista di avanzamento in tempo reale con tutti e 7 i worker che si avviano in parallelo, ognuno che stampa quando finisce con il tempo impiegato e un contatore `[N/7]`. L'intera scansione di solito richiede **1–10 minuti** a seconda delle dimensioni del progetto e del tuo modello/hardware.

**Cosa produce:**
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

Per salvare i documenti in una cartella personalizzata:
```bash
indyforge scan ./mio-servizio --out ./output/docs-mio-servizio
```

---

## 📖 Passo 5 — Leggere l'output

Apri prima `overview.md` — è il documento principale che collega tutto. Poi vai nei file specifici in base a ciò che ti serve:

| Voglio sapere... | Apri questo file |
|---|---|
| Cosa fa il servizio e la sua architettura | `overview.md` |
| Tutti gli endpoint API | `api.md` |
| Flussi Kafka / RabbitMQ / eventi | `events.md` |
| Rischi di sicurezza, segreti hardcodati | `security.md` |
| Come funzionano i flussi di richiesta end-to-end | `sequences.md` |
| Tutte le dipendenze + versioni | `dependencies.md` |
| Chiavi di configurazione (password mascherate) | `config.md` |
| Quali file ci sono nel progetto e cosa fanno | `tree.md` |

---

## 🔀 Scansionare più servizi contemporaneamente

```bash
indyforge scan ./ordini ./pagamenti ./notifiche
```

Questo genera tutto quanto sopra **per ogni servizio**, più un bonus `system-overview.md` che mappa come tutti i servizi interagiscono tra loro.

---

## ♻️ Ripresa dopo un crash

Se la scansione si interrompe a metà, rilancia lo stesso comando. IndyForge chiederà:

```
💾 Found previous checkpoint data. Do you want to use it?
```

Rispondi **Y** e salterà i worker già completati per riprendere da dove si era fermato. Rispondi **N** per ricominciare da capo.

Per ricominciare sempre da zero (ignorando qualsiasi checkpoint salvato):
```bash
indyforge scan ./mio-servizio --no-cache
```

---

## 🆘 Risoluzione dei problemi

| Problema | Soluzione |
|---|---|
| `'indyforge' non riconosciuto` | Esegui di nuovo `pip install -e .` e assicurati che la cartella Scripts di Python sia nel PATH |
| `Connection refused` / errore Ollama | Avvia l'app Ollama ed esegui `ollama serve` in un terminale, poi riprova |
| Scansione lenta | Usa un provider cloud (`INDYFORGE_PROVIDER=openai`) o un modello locale più piccolo (`INDYFORGE_MODEL=llama3.2:3b`) |
| L'AI scrive cose non presenti nel codice | Normale su repo enormi — usa un modello più grande via API per la massima accuratezza |
| Scansione bloccata / congelata | Premi Ctrl+C — i checkpoint sono salvati, puoi riprendere |

---

**Buon Reverse Engineering! 🏛️**
