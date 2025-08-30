# gets data/stats

import yfinance as yf
from typing import Annotated, Callable, Any, Optional
from pandas import DataFrame
import pandas as pd
from functools import wraps

from .utils import save_output, SavePathType, decorate_all_methods
from .config import setup_proxy

# 设置代理（如果配置中启用了）
setup_proxy()


def init_ticker(func: Callable) -> Callable:
    """Decorator to initialize yf.Ticker and pass it to the function."""

    @wraps(func)
    def wrapper(symbol: Annotated[str, "ticker symbol"], *args, **kwargs) -> Any:
        ticker = yf.Ticker(symbol)
        return func(ticker, *args, **kwargs)

    return wrapper


@decorate_all_methods(init_ticker)
class YFinanceUtils:

    def get_stock_data(
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[
            str, "start date for retrieving stock price data, YYYY-mm-dd"
        ],
        end_date: Annotated[
            str, "end date for retrieving stock price data, YYYY-mm-dd"
        ],
        save_path: SavePathType = None,
    ) -> DataFrame:
        """retrieve stock price data for designated ticker symbol"""
        ticker = symbol
        try:
            # add one day to the end_date so that the data range is inclusive
            end_date = pd.to_datetime(end_date) + pd.DateOffset(days=1)
            end_date = end_date.strftime("%Y-%m-%d")
            stock_data = ticker.history(start=start_date, end=end_date)
            
            if stock_data.empty:
                print(f"未找到股票数据 {symbol}: {start_date} 到 {end_date}")
                return pd.DataFrame()
            
            # save_output(stock_data, f"Stock data for {ticker.ticker}", save_path)
            return stock_data
        except Exception as e:
            print(f"获取股票数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_info(
        symbol: Annotated[str, "ticker symbol"],
    ) -> dict:
        """Fetches and returns latest stock information."""
        ticker = symbol
        try:
            stock_info = ticker.info
            return stock_info if stock_info else {}
        except Exception as e:
            print(f"获取股票信息失败 {symbol}: {e}")
            return {}

    def get_company_info(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """Fetches and returns company information as a DataFrame."""
        ticker = symbol
        try:
            info = ticker.info
            if not info:
                info = {}
            
            company_info = {
                "Company Name": info.get("shortName", "N/A"),
                "Industry": info.get("industry", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "Country": info.get("country", "N/A"),
                "Website": info.get("website", "N/A"),
            }
        except Exception as e:
            print(f"获取公司信息失败 {symbol}: {e}")
            company_info = {
                "Company Name": "N/A",
                "Industry": "N/A",
                "Sector": "N/A",
                "Country": "N/A",
                "Website": "N/A",
            }
            
        company_info_df = DataFrame([company_info])
        if save_path:
            company_info_df.to_csv(save_path, encoding='utf-8')
            print(f"Company info for {ticker.ticker} saved to {save_path}")
        return company_info_df

    def get_stock_dividends(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """Fetches and returns the latest dividends data as a DataFrame."""
        ticker = symbol
        try:
            dividends = ticker.dividends
            if dividends.empty:
                print(f"未找到股息数据 {symbol}")
            if save_path:
                dividends.to_csv(save_path, encoding='utf-8')
                print(f"Dividends for {ticker.ticker} saved to {save_path}")
            return dividends
        except Exception as e:
            print(f"获取股息数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_income_stmt(symbol: Annotated[str, "ticker symbol"]) -> DataFrame:
        """Fetches and returns the latest income statement of the company as a DataFrame."""
        ticker = symbol
        try:
            income_stmt = ticker.financials
            if income_stmt.empty:
                print(f"未找到收入表数据 {symbol}")
            return income_stmt
        except Exception as e:
            print(f"获取收入表失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_balance_sheet(symbol: Annotated[str, "ticker symbol"]) -> DataFrame:
        """Fetches and returns the latest balance sheet of the company as a DataFrame."""
        ticker = symbol
        try:
            balance_sheet = ticker.balance_sheet
            if balance_sheet.empty:
                print(f"未找到资产负债表数据 {symbol}")
            return balance_sheet
        except Exception as e:
            print(f"获取资产负债表失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_cash_flow(symbol: Annotated[str, "ticker symbol"]) -> DataFrame:
        """Fetches and returns the latest cash flow statement of the company as a DataFrame."""
        ticker = symbol
        try:
            cash_flow = ticker.cashflow
            if cash_flow.empty:
                print(f"未找到现金流数据 {symbol}")
            return cash_flow
        except Exception as e:
            print(f"获取现金流失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_analyst_recommendations(symbol: Annotated[str, "ticker symbol"]) -> tuple:
        """Fetches the latest analyst recommendations and returns the most common recommendation and its count."""
        ticker = symbol
        try:
            recommendations = ticker.recommendations
            if recommendations is None or recommendations.empty:
                print(f"未找到分析师建议 {symbol}")
                return None, 0  # No recommendations available

            # Assuming 'period' column exists and needs to be excluded
            row_0 = recommendations.iloc[0, 1:]  # Exclude 'period' column if necessary

            # Find the maximum voting result
            max_votes = row_0.max()
            majority_voting_result = row_0[row_0 == max_votes].index.tolist()

            return majority_voting_result[0], max_votes
        except Exception as e:
            print(f"获取分析师建议失败 {symbol}: {e}")
            return None, 0
