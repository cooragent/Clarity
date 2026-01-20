import tradingagents.default_config as default_config
from typing import Dict, Optional

# Use default config but allow it to be overridden
_config: Optional[Dict] = None
DATA_DIR: Optional[str] = None


def initialize_config():
    """Initialize the configuration with default values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.get_default_config()
        DATA_DIR = _config["data_dir"]


def reload_config_from_env():
    global _config, DATA_DIR
    _config = default_config.get_default_config()
    DATA_DIR = _config["data_dir"]
    try:
        from . import interface as interface_module

        interface_module.DATA_DIR = DATA_DIR
    except Exception:
        pass


def set_config(config: Dict):
    """Update the configuration with custom values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.get_default_config()
    _config.update(config)
    DATA_DIR = _config["data_dir"]


def get_config() -> Dict:
    """Get the current configuration."""
    if _config is None:
        initialize_config()
    return _config.copy()


# Initialize with default config
initialize_config()
