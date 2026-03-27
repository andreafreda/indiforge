# 👶 Newbie Guide to IndyForge

[English] | [**Italiano**](GUIDE_FOR_NEWBIES_it.md)

Welcome to **IndyForge**! If you've never used this tool (or if AI applied to software architecture seems like black magic to you), you're in the right place. This guide will take you step-by-step from installation to reading your first generated documents.

---

## 🧐 1. What is IndyForge?

Think of IndyForge as a *tireless senior developer*. You feed it a project folder (or multiple projects) and it takes care of reading the code, understanding how it works, finding dependencies, API endpoints, and security patterns.
At the end of the process, instead of writing you a long technical paper, it generates perfectly formatted and readable `.md` MarkDown documents.

---

## 🛠️ 2. Prerequisites: What you need before starting

Before you can use IndyForge, you'll need two things:
1. **Python (version 3.11 or later)** installed on your computer.
2. **A language model (LLM)**. IndyForge is configured to use *Ollama* by default (which is 100% free and runs locally on your PC). 
   - If you have a recent Mac or PC, download and install [Ollama](https://ollama.com/).
   - Open a terminal and run `ollama pull llama3.1` (to download the writing model) and `ollama pull deepseek-coder:6.7b` (to download the model that will read the code).
   *(Note: If you don't want to use Ollama because your PC is slow, you can use API keys from OpenAI or Anthropic: we explain how in the next chapter).*

---

## 💾 3. Quick Installation and Configuration

1. Open your terminal (Command Prompt, PowerShell, or Mac/Linux Terminal).
2. Clone or download this project folder and navigate inside it:
   ```bash
   cd path/to/indyforge
   ```
3. Install the tool on your computer:
   ```bash
   pip install -e .
   ```
   *This command will tell Python to install IndyForge so that you can call it by simply typing `indyforge` from anywhere on your computer.*

### Want to use Cloud AI (e.g. ChatGPT)?
No problem! Create a file named `.env` in the folder where you'll run IndyForge and write in it:
```env
# Example for OpenAI
INDYFORGE_PROVIDER=openai
OPENAI_API_KEY=sk-your-secret-key
```
*(Also supported: `anthropic`, `groq`, `azure`. If you don't write anything, it will use `ollama` on your PC by default).*

---

## 🚀 4. Your first Scan!

Now comes the fun part! Do you have the source code of a microservice on your desk? Let's investigate it.
Make sure you have the terminal open (and the Ollama app running in the background, if you chose the local model).

Write this command (replacing `path/to/your/project` with the actual folder of the project you want to scan):
```bash
indyforge scan path/to/your/project
```

At this point, you'll see IndyForge come to life! The logs will show you the **6 specialized Workers** working in parallel on your code (one extracts Kafka queues, one REST APIs, one looks at the configuration, etc.).
If any "hallucinations" are detected (i.e. the AI imagines things that are not in the code), a **Verifier** corrects it and forces it to try again until it's 100% accurate!

---

## 📖 5. What to read at the end

As soon as IndyForge has printed `✅ Docs → /docs/...` it means it's finished. 
Open the folder you just scanned (or the `./docs` folder in the directory you are in). You will find several files:

- **`overview.md`**: The main document. It explains what the project is for, its general architecture, the libraries in use, and brings everything together in one place.
- **`api.md`**: A clean table of all REST or GraphQL endpoints (and whether they need authentication or not).
- **`events.md`**: Everything related to queues, RabbitMQ, Kafka, asynchronous messaging.
- **`security.md`**: If there are vulnerabilities or exposed queries in the project, they will be noted here.
- **`sequences.md`**: Dynamic Mermaid diagrams that explain piece by piece the "Data Journey" of the most famous frameworks!
- **`dependencies.md` / `config.md`**: Useful for knowing exactly what credentials or packages the app needs to run.

### Scanned multiple projects together?
By running a command like `indyforge scan ./project1 ./project2` you will also generate a bonus file: **`system-overview.md`**.
This incredible file will "sum up the situation" by comparing them and making you understand how (and if) `project1` talks and interacts with `project2`.

---

## 🆘 6. Troubleshooting Frequently Asked Questions

- **"Term 'indyforge' not recognized"** 
  *Solution*: Make sure you've run `pip install -e .` and that your Python environment variables (Path) are correctly configured on Windows.
- **"Ollama not responding / Connection Error"**
  *Solution*: You have Ollama turned off. Start the Ollama app from the Start menu/Applications and make sure you've downloaded the models with `ollama pull deepseek-coder:6.7b` and `ollama pull llama3.1:8b`.
- **The AI writes nonsense ("Unresolved Hallucinations")**
  *Solution*: The project might be too massive. If a single microservice is huge, IndyForge does its best, but we recommend using higher-class LLMs via API (e.g. `INDYFORGE_PROVIDER=openai`) for pristine understanding.

**Happy Reverse Engineering! 🏛️**
