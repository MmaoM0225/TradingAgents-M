import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "./data",  # 统一使用项目根目录下的data目录
    "data_cache_dir": "./data/cache",  # 统一使用data目录下的cache子目录
    "market_data_dir": "./data/market_data",  # 市场数据目录
    "price_data_dir": "./data/market_data/price_data",  # 股价数据目录
    # 数据日期范围配置 - 使用动态计算而非硬编码
    "data_years_back": 5,  # 回溯多少年的数据
    "default_data_start": "2010-01-01",  # 默认数据开始日期
    "use_dynamic_date_range": True,  # 是否使用动态日期范围
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings  
    "online_tools": False,  
    # Proxy settings
    "use_proxy": True,
    "http_proxy": "http://127.0.0.1:7890",
    "https_proxy": "http://127.0.0.1:7890",
}
