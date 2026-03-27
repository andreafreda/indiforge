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
MAX_CONCURRENCY = int(os.getenv("INDYFORGE_MAX_CONCURRENCY", "0"))


class _StringLLMWrapper:
    """
    Wraps any LangChain LLM/ChatModel so that .invoke() always returns
    a plain str instead of an AIMessage object.

    - OllamaLLM.invoke()       → str           (already fine)
    - ChatOpenAI.invoke()      → AIMessage     (need .content)
    - ChatAnthropic.invoke()   → AIMessage     (need .content)
    - ChatGroq.invoke()        → AIMessage     (need .content)
    - AzureChatOpenAI.invoke() → AIMessage     (need .content)
    """

    def __init__(self, llm):
        self._llm = llm

    def invoke(self, prompt, **kwargs):
        result = self._llm.invoke(prompt, **kwargs)
        if isinstance(result, str):
            return result
        # AIMessage / HumanMessage / BaseMessage all have .content
        if hasattr(result, "content"):
            return result.content
        return str(result)

    def __getattr__(self, name):
        return getattr(self._llm, name)


def make_llm(model_name: str):
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model_name)
    elif PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model_name)
    elif PROVIDER == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(model=model_name)
    elif PROVIDER == "azure":
        from langchain_openai import AzureChatOpenAI
        llm = AzureChatOpenAI(azure_deployment=model_name)
    else:  # default ollama
        from langchain_ollama import OllamaLLM
        llm = OllamaLLM(model=model_name)
    return _StringLLMWrapper(llm)

