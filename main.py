from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()

# Example 1: Using Google models (current)
config["llm_provider"] = "google"  # Use a different model
config["backend_url"] = "https://generativelanguage.googleapis.com/v1"  # Use a different backend
config["deep_think_llm"] = "gemini-2.0-flash"  # Use a different model
config["quick_think_llm"] = "gemini-2.0-flash"  # Use a different model

# Example 2: Using DeepSeek models (uncomment to use)
# config["llm_provider"] = "deepseek"
# config["backend_url"] = "https://api.deepseek.com/v1"
# config["deep_think_llm"] = "deepseek-reasoner"  # Enhanced reasoning
# config["quick_think_llm"] = "deepseek-chat"     # General purpose

# Example 3: Using SiliconFlow models (uncomment to use)
# config["llm_provider"] = "siliconflow"
# config["backend_url"] = "https://api.siliconflow.cn/v1"
# config["deep_think_llm"] = "Qwen/Qwen2.5-72B-Instruct"     # Large model for reasoning
# config["quick_think_llm"] = "Qwen/Qwen2.5-7B-Instruct"     # Efficient model for quick tasks

# Example 4: Using Alibaba DashScope models (uncomment to use)
# config["llm_provider"] = "alibaba dashscope"
# config["backend_url"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# config["deep_think_llm"] = "qwen-max"      # Flagship model for complex reasoning
# config["quick_think_llm"] = "qwen-turbo"   # High-speed model for quick tasks

config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Enable online tools

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
