import os

# Get project directory
_PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))

def get_default_config() -> dict:
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if llm_provider == "openai":
        default_backend_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        default_quick_think_llm = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        default_deep_think_llm = os.getenv("OPENAI_DEEP_MODEL", "gpt-4o")
    elif llm_provider == "qwen":
        default_backend_url = os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        default_quick_think_llm = os.getenv("QWEN_MODEL", "qwen-latest")
        default_deep_think_llm = os.getenv("QWEN_DEEP_MODEL", default_quick_think_llm)
    else:
        default_backend_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        default_quick_think_llm = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        default_deep_think_llm = os.getenv("OPENAI_DEEP_MODEL", "gpt-4o")

    return {
        "project_dir": _PROJECT_DIR,
        "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./runtime/results"),
        "data_dir": os.getenv(
            "TRADINGAGENTS_DATA_DIR",
            os.path.join(_PROJECT_DIR, "dataflows", "data_cache"),
        ),
        "data_cache_dir": os.path.join(_PROJECT_DIR, "dataflows/data_cache"),
        "llm_provider": llm_provider,
        "deep_think_llm": os.getenv("DEEP_THINK_LLM", default_deep_think_llm),
        "quick_think_llm": os.getenv("QUICK_THINK_LLM", default_quick_think_llm),
        "backend_url": os.getenv("LLM_BACKEND_URL", default_backend_url),
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
        "max_recur_limit": 100,
        "online_tools": True,
    }


DEFAULT_CONFIG = get_default_config()
