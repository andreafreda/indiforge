# 👶 Guida per Newbie a IndyForge

Benvenuto in **IndyForge**! Se non hai mai usato questo strumento (o se l'intelligenza artificiale applicata all'architettura software ti sembra magia nera), sei nel posto giusto. Questa guida ti porterà passo-passo dall'installazione fino alla lettura dei tuoi primi documenti generati.

---

## 🧐 1. Cos'è IndyForge?

Pensa a IndyForge come a uno *sviluppatore senior instancabile*. Gli dai in pasto la cartella di un progetto (o di più progetti) e lui si occupa di leggere il codice, capirne il funzionamento, trovare le dipendenze, gli endpoint API e i pattern di sicurezza.
Alla fine del processo, invece di scriverti un papiro in codice, ti genera dei documenti MarkDown `.md` perfettamente formattati e leggibili.

---

## 🛠️ 2. Prerequisiti: Cosa ti serve prima di iniziare

Prima di poter usare IndyForge, ti serviranno due cose:
1. **Python (versione 3.11 o successiva)** installato sul tuo computer.
2. **Un modello linguistico (LLM)**. IndyForge è configurato per usare *Ollama* di default (che è al 100% gratuito e gira in locale sul tuo PC). 
   - Se hai un Mac o un PC recente, scarica e installa [Ollama](https://ollama.com/).
   - Apri un terminale e lancia `ollama pull llama3.1` (per scaricare il modello di scrittura) e `ollama pull deepseek-coder:6.7b` (per scaricare il modello che leggerà il codice).
   *(Nota: Se non vuoi usare Ollama perché il tuo PC è lento, puoi usare le chiavi API di OpenAI o Anthropic: ti spieghiamo come nel capitolo seguente).*

---

## 💾 3. Installazione e Configurazione Rapida

1. Apri il tuo terminale (Prompt dei Comandi, PowerShell o Terminale Mac/Linux).
2. Clona o scarica la cartella di questo progetto e naviga al suo interno:
   ```bash
   cd path/to/indyforge
   ```
3. Installa lo strumento sul tuo computer:
   ```bash
   pip install -e .
   ```
   *Questo comando dirà a Python di installare IndyForge in modo che tu possa richiamarlo digitando semplicemente `indyforge` da qualsiasi punto del tuo computer.*

### Vuoi usare l'Intelligenza Artificiale in Cloud (es. ChatGPT)?
Nessun problema! Crea un file chiamato `.env` nella cartella in cui lancerai IndyForge e scrivici dentro:
```env
# Esempio per OpenAI
INDYFORGE_PROVIDER=openai
OPENAI_API_KEY=sk-la-tua-chiave-segreta
```
*(Sono supportati anche `anthropic`, `groq`, `azure`. Se non scrivi nulla, lui userà `ollama` sul tuo PC di default).*

### Lingua in Italiano 🇮🇹
Vuoi che i documenti generati siano in Italiano? Aggiungi questa riga nel tuo `.env`:
```env
INDYFORGE_LANGUAGE=italian
```

---

## 🚀 4. La tua prima Scansione!

Ora arriva la parte divertente! Hai il codice sorgente di un microservizio sulla tua scrivania? Mettiamolo sotto indagine.
Assicurati di avere il terminale aperto (e l'app di Ollama avviata in background, se hai scelto il modello locale).

Scrivi questo comando (sostituendo `percorso/del/tuo/progetto` con la cratella reale del progetto che vuoi scansionare):
```bash
indyforge scan percorso/del/tuo/progetto
```

A questo punto vedrai IndyForge prendere vita! I log ti mostreranno i **6 Worker** specializzati che lavorano in parallelo sul tuo codice (uno estrae le code Kafka, uno le API REST, uno guarda la configurazione, ecc.).
Se vengono rilevati eventuali "allucinazioni" (ovvero l'AI immagina cose che non ci sono nel codice), un **Verifier** lo bacchetta e lo costringe a riprovare finché non è fedele al 100%!

---

## 📖 5. Cosa leggere alla fine

Appena IndyForge avrà stampato `✅ Docs → /docs/...` significa che ha finito. 
Apri la cartella che ai appena scansionato (oppure la cartella `./docs` nella directory in cui ti trovi). Troverai svariati file:

- **`overview.md`**: Il documento principe. Spiega a cosa serve il progetto, la sua architettura generale, le librerie in uso, e riunisce tutto in un solo posto.
- **`api.md`**: La tabella pulitissima di tutti gli endpoint REST o GraphQL (e se hanno bisogno di autenticazione o no).
- **`events.md`**: Tutto ciò che riguarda code, RabbitMQ, Kafka, messaggistica asincrona.
- **`security.md`**: Se nel progetto ci sono vulnerabilità o query scoperte, verranno annotate qui.
- **`sequences.md`**: Diagrammi dinamici Mermaid che spiegano pezzo per pezzo il "Viaggio del dato" dei framework più famosi!
- **`dependencies.md` / `config.md`**: Utili per sapere esattamente quali credenziali o pacchetti l'app richiede per girare.

### Hai scansionato molteplici progetti insieme?
Lanciando un comando come `indyforge scan ./progetto1 ./progetto2` genererai anche un file bonus: **`system-overview.md`**.
Questo file incredibile farà il "punto della situazione" mettendoli a confronto e facendoti capire come (e se) `progetto1` parla e interagisce con `progetto2`.

---

## 🆘 6. Risoluzione dei Problemi Frequenti

- **"Termine 'indyforge' non riconosciuto"** 
  *Soluzione*: Assicurati di aver lanciato `pip install -e .` e che le variabili di ambiente (Path) del tuo Python siano configurate correttamente su Windows.
- **"Ollama non risponde / Connection Error"**
  *Soluzione*: Hai tenuto Ollama spento. Avvia l'app di Ollama dal menu Start/Applicazioni e accertati di aver scaricato i modelli con `ollama pull deepseek-coder:6.7b` e `ollama pull llama3.1:8b`.
- **L'AI scrive cavolate ("Allucinazioni non risolte")**
  *Soluzione*: Il progetto potrebbe essere troppo colossale. Se un singolo microservizio è enorme, IndyForge fa del suo meglio, ma consigliamo di usare LLM di classe superiore tramite API (es. `INDYFORGE_PROVIDER=openai`) per una comprensione immacolata.

**Buon Reverse Engineering! 🏛️**
