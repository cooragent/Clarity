import os

# Get project directory
_PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))

DEFAULT_CONFIG = {
    "project_dir": _PROJECT_DIR,
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    # Data directory - use environment variable or default to local cache
    "data_dir": os.getenv(
        "TRADINGAGENTS_DATA_DIR",
        os.path.join(_PROJECT_DIR, "dataflows", "data_cache"),
    ),
    "data_cache_dir": os.path.join(_PROJECT_DIR, "dataflows/data_cache"),
    # LLM settings
    "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
    "deep_think_llm": os.getenv("DEEP_THINK_LLM", "gpt-4o"),
    "quick_think_llm": os.getenv("QUICK_THINK_LLM", "gpt-4o-mini"),
    "backend_url": os.getenv("LLM_BACKEND_URL", "https://api.openai.com/v1"),
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings - use online tools by default since local data may not exist
    "online_tools": True,
}
