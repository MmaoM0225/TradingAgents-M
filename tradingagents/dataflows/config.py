import tradingagents.default_config as default_config
from typing import Dict, Optional
import os

# Use default config but allow it to be overridden
_config: Optional[Dict] = None
DATA_DIR: Optional[str] = None


def initialize_config():
    """Initialize the configuration with default values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
        DATA_DIR = _config["data_dir"]


def set_config(config: Dict):
    """Update the configuration with custom values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
    _config.update(config)
    DATA_DIR = _config["data_dir"]


def get_config() -> Dict:
    """Get the current configuration."""
    if _config is None:
        initialize_config()
    return _config.copy()


def setup_proxy():
    """设置代理环境变量（如果配置中启用了代理）"""
    config = get_config()
    if config.get("use_proxy", False):
        http_proxy = config.get("http_proxy")
        https_proxy = config.get("https_proxy")
        
        if http_proxy:
            os.environ["http_proxy"] = http_proxy
        if https_proxy:
            os.environ["https_proxy"] = https_proxy
            
        print(f"代理已设置: HTTP={http_proxy}, HTTPS={https_proxy}")


# Initialize with default config
initialize_config()
