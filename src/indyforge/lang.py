from indyforge.config import LANGUAGE

TRANSLATIONS = {
    "english": {
        "deps_extract": "  📦 [deps_worker]     Extracting dependencies...",
        "deps_done": "  ✅ [deps_worker]     Done.",
        "api_extract": "  🌐 [api_worker]      Extracting API endpoints...",
        "api_done": "  ✅ [api_worker]      Done.",
        "event_extract": "  📨 [event_worker]    Extracting event consumers/producers...",
        "event_done": "  ✅ [event_worker]    Done.",
        "security_extract": "  🔒 [security_worker] Analyzing security & CVE...",
        "security_done": "  ✅ [security_worker] Done.",
        "sequence_extract": "  🔀 [sequence_worker] Building sequence diagrams...",
        "sequence_done": "  ✅ [sequence_worker] Done.",
        "config_extract": "  ⚙️  [config_worker]   Reading config files...",
        "config_done": "  ✅ [config_worker]   Done.",
        "aggregator_write": "  📝 [aggregator]      Writing overview.md (iteration {it}/3)...",
        "aggregator_done": "  ✅ [aggregator]      Draft ready.",
        "verifier_check": "  🔍 [verifier]        Checking quality & grounding...",
        "verifier_pass": "  ✅ [verifier]        Quality & grounding check passed!",
        "verifier_retry": "  ⚠️  [verifier]        Issues found – retrying...",
        "hallucination": "    🚫 Hallucination: {h}",
        "error": "    ❌ Error: {e}",
        "scan_repo": "\n🏛️  Scanning repo: {repo_path}",
        "reduce_build": "\n🗺️  [reduce_system]   Building cross-repo system-overview...",
        "reduce_done": "  ✅ [reduce_system]   Done.",
        "cli_title": "🏛️  IndyForge - Raiders of the Lost Architecture",
        "cli_scan": "🔍 Scanning: {repos}",
        "cli_docs": "\n✅ Docs → {path}",
        "cli_sysdocs": "\n✅ System docs → {path}",
        "cli_file": "  └─ {path}",
        "cache_found": "💾 Found previous cache/checkpoint data. Do you want to use it? (Say No to delete and start from scratch)",
        "cache_used": "♻️ Utilizing existing cache data.",
        "cache_deleted": "🗑️ Cache deleted. Starting from scratch.",
        "cache_flag": "🗑️ Cache deleted via --no-cache flag."
    },
    "italian": {
        "deps_extract": "  📦 [deps_worker]     Estrazione dipendenze...",
        "deps_done": "  ✅ [deps_worker]     Fatto.",
        "api_extract": "  🌐 [api_worker]      Estrazione endpoint API...",
        "api_done": "  ✅ [api_worker]      Fatto.",
        "event_extract": "  📨 [event_worker]    Estrazione consumer/producer eventi...",
        "event_done": "  ✅ [event_worker]    Fatto.",
        "security_extract": "  🔒 [security_worker] Analisi sicurezza & CVE...",
        "security_done": "  ✅ [security_worker] Fatto.",
        "sequence_extract": "  🔀 [sequence_worker] Generazione sequence diagram...",
        "sequence_done": "  ✅ [sequence_worker] Fatto.",
        "config_extract": "  ⚙️  [config_worker]   Lettura file di configurazione...",
        "config_done": "  ✅ [config_worker]   Fatto.",
        "aggregator_write": "  📝 [aggregator]      Scrittura overview.md (iterazione {it}/3)...",
        "aggregator_done": "  ✅ [aggregator]      Bozza pronta.",
        "verifier_check": "  🔍 [verifier]        Controllo qualità & allucinazioni...",
        "verifier_pass": "  ✅ [verifier]        Qualità confermata, nessuna allucinazione!",
        "verifier_retry": "  ⚠️  [verifier]        Problemi rilevati – nuovo tentativo...",
        "hallucination": "    🚫 Allucinazione: {h}",
        "error": "    ❌ Errore: {e}",
        "scan_repo": "\n🏛️  Scansione repo: {repo_path}",
        "reduce_build": "\n🗺️  [reduce_system]   Creazione system-overview cross-repo...",
        "reduce_done": "  ✅ [reduce_system]   Fatto.",
        "cli_title": "🏛️  IndyForge - Alla ricerca dell'architettura perduta",
        "cli_scan": "🔍 Scansione in corso: {repos}",
        "cli_docs": "\n✅ Documentazione → {path}",
        "cli_sysdocs": "\n✅ Documentazione di sistema → {path}",
        "cli_file": "  └─ {path}",
        "cache_found": "💾 Trovati dati di cache/checkpoint precedenti. Vuoi utilizzarli? (Rispondi No per cancellarli e ripartire da zero)",
        "cache_used": "♻️ Utilizzo i dati di cache esistenti.",
        "cache_deleted": "🗑️ Cache eliminata. Riparto da zero.",
        "cache_flag": "🗑️ Cache eliminata tramite parametro --no-cache."
    }
}

def t(key: str, **kwargs) -> str:
    lang = LANGUAGE.lower()
    if lang not in TRANSLATIONS:
        lang = "english"
    text = TRANSLATIONS[lang].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
