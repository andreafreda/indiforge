from dotenv import load_dotenv
import os

load_dotenv()

# If INDYFORGE_MODEL is set, use it for everything (easy override)
_global = os.getenv("INDYFORGE_MODEL")

CODE_MODEL     = _global or os.getenv("INDYFORGE_CODE_MODEL",     "deepseek-coder:6.7b")
WRITER_MODEL   = _global or os.getenv("INDYFORGE_WRITER_MODEL",   "llama3.1:8b")
SECURITY_MODEL = _global or os.getenv("INDYFORGE_SECURITY_MODEL", "mistral:7b")
VERIFIER_MODEL = _global or os.getenv("INDYFORGE_VERIFIER_MODEL", "llama3.1:8b")

PROVIDER = os.getenv("INDYFORGE_PROVIDER", "ollama").lower()
LANGUAGE = os.getenv("INDYFORGE_LANGUAGE", "english")

def make_llm(model_name: str):
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name)
    elif PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name)
    elif PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model_name)
    elif PROVIDER == "azure":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(azure_deployment=model_name)
    else:  # default ollama
        from langchain_ollama import OllamaLLM
        return OllamaLLM(model=model_name)
