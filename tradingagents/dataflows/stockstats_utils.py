import pandas as pd
import yfinance as yf
from stockstats import wrap
from typing import Annotated
import os
from .config import get_config


class StockstatsUtils:
    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        data_dir: Annotated[
            str,
            "directory where the stock data is stored.",
        ],
        online: Annotated[
            bool,
            "whether to use online tools to fetch data or offline tools. If True, will use online tools.",
        ] = False,
    ):
        df = None
        data = None

        # Get config for unified path configuration
        config = get_config()
        
        if not online:
            try:
                # 使用动态文件查找功能
                from .utils import get_or_generate_data_filename
                data_file = get_or_generate_data_filename(symbol, "price")
                data = pd.read_csv(data_file)
                df = wrap(data)
            except FileNotFoundError:
                raise Exception("Stockstats fail: Yahoo Finance data not fetched yet!")
        else:
            # 使用统一的动态日期范围和文件查找
            from .utils import get_or_generate_data_filename, get_dynamic_date_range
            
            # 转换curr_date为字符串（如果需要）
            if hasattr(curr_date, 'strftime'):
                curr_date_str = curr_date.strftime("%Y-%m-%d")
            else:
                curr_date_str = str(curr_date)
            
            # 统一使用config配置的data_cache_dir并确保目录存在
            os.makedirs(config["data_cache_dir"], exist_ok=True)

            data_file = get_or_generate_data_filename(symbol, "cache")

            if os.path.exists(data_file):
                data = pd.read_csv(data_file)
                data["Date"] = pd.to_datetime(data["Date"])
            else:
                # 设置yfinance专用代理
                if config.get("use_proxy", False):
                    http_proxy = config.get("http_proxy")
                    https_proxy = config.get("https_proxy")
                    if http_proxy:
                        os.environ["http_proxy"] = http_proxy
                    if https_proxy:
                        os.environ["https_proxy"] = https_proxy
                
                # 获取动态日期范围用于下载
                start_date, end_date = get_dynamic_date_range()
                
                data = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    multi_level_index=False,
                    progress=False,
                    auto_adjust=True,
                )
                data = data.reset_index()
                data.to_csv(data_file, index=False, encoding='utf-8')

            df = wrap(data)
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            
        # 对于offline模式，确保curr_date是字符串格式
        if not online:
            if hasattr(curr_date, 'strftime'):
                curr_date_str = curr_date.strftime("%Y-%m-%d") 
            else:
                curr_date_str = str(curr_date)

        df[indicator]  # trigger stockstats to calculate the indicator
        matching_rows = df[df["Date"].str.startswith(curr_date_str)]

        if not matching_rows.empty:
            indicator_value = matching_rows[indicator].values[0]
            return indicator_value
        else:
            return "N/A: Not a trading day (weekend or holiday)"
