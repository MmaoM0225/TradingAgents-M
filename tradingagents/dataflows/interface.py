from typing import Annotated, Dict
from .reddit_utils import fetch_top_from_category
from .yfin_utils import *
from .stockstats_utils import *
from .googlenews_utils import *
from .finnhub_utils import get_data_in_range
from .finnhub_downloader import download_finnhub_data
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
import pandas as pd
import requests
from tqdm import tqdm
import yfinance as yf
from openai import OpenAI
from .config import get_config, set_config, DATA_DIR


def get_finnhub_news(
    ticker: Annotated[
        str,
        "Search query of a company's, e.g. 'AAPL, TSM, etc.",
    ],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
):
    """
    Retrieve news about a company within a time frame
    先检查本地文件，如果不存在则从Finnhub API下载数据

    Args
        ticker (str): ticker for the company you are interested in
        curr_date (str): Current date in yyyy-mm-dd format  
        look_back_days (int): how many days to look back
    Returns
        str: dataframe containing the news of the company in the time frame
    """

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    # 先尝试从本地读取数据
    result = get_data_in_range(ticker, before, curr_date, "news_data", DATA_DIR)

    # 如果本地没有数据，尝试下载
    if len(result) == 0:
        print(f"本地未找到 {ticker} 的新闻数据，正在从Finnhub下载...")
        downloaded_data = download_finnhub_data(ticker, before, curr_date, "news_data")
        if downloaded_data:
            # 重新读取下载后的数据
            result = get_data_in_range(ticker, before, curr_date, "news_data", DATA_DIR)
        
        # 如果还是没有数据，返回提示信息
        if len(result) == 0:
            return f"暂无 {ticker} 公司在 {before} 到 {curr_date} 期间的新闻数据。可能是API配置问题或该时段确实无相关新闻。"

    combined_result = ""
    for day, data in result.items():
        if len(data) == 0:
            continue
        for entry in data:
            current_news = (
                "### " + entry["headline"] + f" ({day})" + "\n" + entry["summary"]
            )
            combined_result += current_news + "\n\n"

    return f"## {ticker} News, from {before} to {curr_date}:\n" + str(combined_result)


def get_finnhub_company_insider_sentiment(
    ticker: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[
        str,
        "current date of you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "number of days to look back"],
):
    """
    Retrieve insider sentiment about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading on, yyyy-mm-dd
    Returns:
        str: a report of the sentiment in the past 15 days starting at curr_date
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    # 先尝试从本地读取数据
    data = get_data_in_range(ticker, before, curr_date, "insider_senti", DATA_DIR)

    # 如果本地没有数据，尝试下载
    if len(data) == 0:
        print(f"本地未找到 {ticker} 的内部人情绪数据，正在从Finnhub下载...")
        downloaded_data = download_finnhub_data(ticker, before, curr_date, "insider_senti")
        if downloaded_data:
            # 重新读取下载后的数据
            data = get_data_in_range(ticker, before, curr_date, "insider_senti", DATA_DIR)
        
        # 如果还是没有数据，返回提示信息
        if len(data) == 0:
            return f"暂无 {ticker} 公司在 {before} 到 {curr_date} 期间的内部人情绪数据。可能是API配置问题或该时段确实无相关数据。"

    result_str = ""
    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### {entry['year']}-{entry['month']}:\nChange: {entry['change']}\nMonthly Share Purchase Ratio: {entry['mspr']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} Insider Sentiment Data for {before} to {curr_date}:\n"
        + result_str
        + "The change field refers to the net buying/selling from all insiders' transactions. The mspr field refers to monthly share purchase ratio."
    )


def get_finnhub_company_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[
        str,
        "current date you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "how many days to look back"],
):
    """
    Retrieve insider transcaction information about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading at, yyyy-mm-dd
    Returns:
        str: a report of the company's insider transaction/trading informtaion in the past 15 days
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    # 先尝试从本地读取数据  
    data = get_data_in_range(ticker, before, curr_date, "insider_trans", DATA_DIR)

    # 如果本地没有数据，尝试下载
    if len(data) == 0:
        print(f"本地未找到 {ticker} 的内部人交易数据，正在从Finnhub下载...")
        downloaded_data = download_finnhub_data(ticker, before, curr_date, "insider_trans")
        if downloaded_data:
            # 重新读取下载后的数据
            data = get_data_in_range(ticker, before, curr_date, "insider_trans", DATA_DIR)
        
        # 如果还是没有数据，返回提示信息
        if len(data) == 0:
            return f"暂无 {ticker} 公司在 {before} 到 {curr_date} 期间的内部人交易数据。可能是API配置问题或该时段确实无相关数据。"

    result_str = ""

    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### Filing Date: {entry['filingDate']}, {entry['name']}:\nChange:{entry['change']}\nShares: {entry['share']}\nTransaction Price: {entry['transactionPrice']}\nTransaction Code: {entry['transactionCode']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} insider transactions from {before} to {curr_date}:\n"
        + result_str
        + "The change field reflects the variation in share count—here a negative number indicates a reduction in holdings—while share specifies the total number of shares involved. The transactionPrice denotes the per-share price at which the trade was executed, and transactionDate marks when the transaction occurred. The name field identifies the insider making the trade, and transactionCode (e.g., S for sale) clarifies the nature of the transaction. FilingDate records when the transaction was officially reported, and the unique id links to the specific SEC filing, as indicated by the source. Additionally, the symbol ties the transaction to a particular company, isDerivative flags whether the trade involves derivative securities, and currency notes the currency context of the transaction."
    )


def get_simfin_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "balance_sheet",
        "companies",
        "us",
        f"us-balance-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No balance sheet available before the given current date.")
        return ""

    # Get the most recent balance sheet by selecting the row with the latest Publish Date
    latest_balance_sheet = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_balance_sheet = latest_balance_sheet.drop("SimFinId")

    return (
        f"## {freq} balance sheet for {ticker} released on {str(latest_balance_sheet['Publish Date'])[0:10]}: \n"
        + str(latest_balance_sheet)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of assets, liabilities, and equity. Assets are grouped as current (liquid items like cash and receivables) and noncurrent (long-term investments and property). Liabilities are split between short-term obligations and long-term debts, while equity reflects shareholder funds such as paid-in capital and retained earnings. Together, these components ensure that total assets equal the sum of liabilities and equity."
    )


def get_simfin_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "cash_flow",
        "companies",
        "us",
        f"us-cashflow-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No cash flow statement available before the given current date.")
        return ""

    # Get the most recent cash flow statement by selecting the row with the latest Publish Date
    latest_cash_flow = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_cash_flow = latest_cash_flow.drop("SimFinId")

    return (
        f"## {freq} cash flow statement for {ticker} released on {str(latest_cash_flow['Publish Date'])[0:10]}: \n"
        + str(latest_cash_flow)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of cash movements. Operating activities show cash generated from core business operations, including net income adjustments for non-cash items and working capital changes. Investing activities cover asset acquisitions/disposals and investments. Financing activities include debt transactions, equity issuances/repurchases, and dividend payments. The net change in cash represents the overall increase or decrease in the company's cash position during the reporting period."
    )


def get_simfin_income_statements(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "income_statements",
        "companies",
        "us",
        f"us-income-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No income statement available before the given current date.")
        return ""

    # Get the most recent income statement by selecting the row with the latest Publish Date
    latest_income = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_income = latest_income.drop("SimFinId")

    return (
        f"## {freq} income statement for {ticker} released on {str(latest_income['Publish Date'])[0:10]}: \n"
        + str(latest_income)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a comprehensive breakdown of the company's financial performance. Starting with Revenue, it shows Cost of Revenue and resulting Gross Profit. Operating Expenses are detailed, including SG&A, R&D, and Depreciation. The statement then shows Operating Income, followed by non-operating items and Interest Expense, leading to Pretax Income. After accounting for Income Tax and any Extraordinary items, it concludes with Net Income, representing the company's bottom-line profit or loss for the period."
    )


def get_yfinance_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency: annual / quarterly (Yahoo Finance默认提供年度数据)",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    通过Yahoo Finance获取资产负债表数据
    Yahoo Finance提供免费的财务报表数据，无需API密钥
    """
    try:
        import yfinance as yf
        
        # 创建ticker对象
        stock = yf.Ticker(ticker)
        
        # 获取资产负债表
        balance_sheet = stock.balance_sheet
        
        if balance_sheet.empty:
            return f"暂无 {ticker} 公司的资产负债表数据。可能是该股票代码不存在或Yahoo Finance暂无数据。"
        
        # 取最新的财务数据 (最左边的列)
        latest_data = balance_sheet.iloc[:, 0]
        latest_date = balance_sheet.columns[0]
        
        # 格式化输出
        formatted_output = f"## Balance Sheet for {ticker} (Latest: {latest_date.strftime('%Y-%m-%d')}):\n\n"
        
        # 主要资产负债表项目
        formatted_output += "### Assets:\n"
        formatted_output += f"- Total Assets: {format_financial_value(latest_data.get('Total Assets', 'N/A'))}\n"
        formatted_output += f"- Current Assets: {format_financial_value(latest_data.get('Current Assets', 'N/A'))}\n"
        formatted_output += f"- Cash and Cash Equivalents: {format_financial_value(latest_data.get('Cash And Cash Equivalents', 'N/A'))}\n"
        formatted_output += f"- Receivables: {format_financial_value(latest_data.get('Receivables', 'N/A'))}\n"
        formatted_output += f"- Inventory: {format_financial_value(latest_data.get('Inventory', 'N/A'))}\n"
        
        formatted_output += "\n### Liabilities:\n"
        formatted_output += f"- Total Liabilities: {format_financial_value(latest_data.get('Total Liabilities Net Minority Interest', 'N/A'))}\n"
        formatted_output += f"- Current Liabilities: {format_financial_value(latest_data.get('Current Liabilities', 'N/A'))}\n"
        formatted_output += f"- Long Term Debt: {format_financial_value(latest_data.get('Long Term Debt', 'N/A'))}\n"
        formatted_output += f"- Short Term Debt: {format_financial_value(latest_data.get('Current Debt', 'N/A'))}\n"
        
        formatted_output += "\n### Equity:\n"
        formatted_output += f"- Total Stockholder Equity: {format_financial_value(latest_data.get('Stockholders Equity', 'N/A'))}\n"
        formatted_output += f"- Retained Earnings: {format_financial_value(latest_data.get('Retained Earnings', 'N/A'))}\n"
        
        # 添加财务比率计算
        total_assets = latest_data.get('Total Assets', 0)
        total_liabilities = latest_data.get('Total Liabilities Net Minority Interest', 0)
        if total_assets and total_liabilities:
            debt_to_asset_ratio = (total_liabilities / total_assets) * 100
            formatted_output += f"\n### Key Ratios:\n"
            formatted_output += f"- Debt-to-Asset Ratio: {debt_to_asset_ratio:.2f}%\n"
        
        return formatted_output
        
    except Exception as e:
        return f"获取 {ticker} 资产负债表数据时出错: {str(e)}。建议检查股票代码是否正确。"


def get_yfinance_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency: annual / quarterly (Yahoo Finance默认提供年度数据)",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    通过Yahoo Finance获取现金流量表数据
    Yahoo Finance提供免费的财务报表数据，无需API密钥
    """
    try:
        import yfinance as yf
        
        # 创建ticker对象
        stock = yf.Ticker(ticker)
        
        # 获取现金流量表
        cashflow = stock.cashflow
        
        if cashflow.empty:
            return f"暂无 {ticker} 公司的现金流量表数据。可能是该股票代码不存在或Yahoo Finance暂无数据。"
        
        # 取最新的财务数据
        latest_data = cashflow.iloc[:, 0]
        latest_date = cashflow.columns[0]
        
        # 格式化输出
        formatted_output = f"## Cash Flow Statement for {ticker} (Latest: {latest_date.strftime('%Y-%m-%d')}):\n\n"
        
        # 现金流量表主要项目
        formatted_output += "### Operating Cash Flow:\n"
        formatted_output += f"- Operating Cash Flow: {format_financial_value(latest_data.get('Operating Cash Flow', 'N/A'))}\n"
        formatted_output += f"- Net Income: {format_financial_value(latest_data.get('Net Income', 'N/A'))}\n"
        formatted_output += f"- Depreciation & Amortization: {format_financial_value(latest_data.get('Depreciation And Amortization', 'N/A'))}\n"
        formatted_output += f"- Changes in Working Capital: {format_financial_value(latest_data.get('Change In Working Capital', 'N/A'))}\n"
        
        formatted_output += "\n### Investing Cash Flow:\n"
        formatted_output += f"- Investing Cash Flow: {format_financial_value(latest_data.get('Investing Cash Flow', 'N/A'))}\n"
        formatted_output += f"- Capital Expenditures: {format_financial_value(latest_data.get('Capital Expenditure', 'N/A'))}\n"
        formatted_output += f"- Investments: {format_financial_value(latest_data.get('Net Investment Purchase And Sale', 'N/A'))}\n"
        
        formatted_output += "\n### Financing Cash Flow:\n"
        formatted_output += f"- Financing Cash Flow: {format_financial_value(latest_data.get('Financing Cash Flow', 'N/A'))}\n"
        formatted_output += f"- Dividends Paid: {format_financial_value(latest_data.get('Cash Dividends Paid', 'N/A'))}\n"
        formatted_output += f"- Stock Repurchases: {format_financial_value(latest_data.get('Repurchase Of Capital Stock', 'N/A'))}\n"
        
        formatted_output += "\n### Net Change in Cash:\n"
        operating_cf = latest_data.get('Operating Cash Flow', 0) or 0
        investing_cf = latest_data.get('Investing Cash Flow', 0) or 0
        financing_cf = latest_data.get('Financing Cash Flow', 0) or 0
        net_change = operating_cf + investing_cf + financing_cf
        formatted_output += f"- Net Change in Cash: {format_financial_value(net_change)}\n"
        
        # 计算自由现金流
        capex = latest_data.get('Capital Expenditure', 0) or 0
        free_cash_flow = operating_cf + capex  # capex通常是负数
        formatted_output += f"- Free Cash Flow: {format_financial_value(free_cash_flow)}\n"
        
        return formatted_output
        
    except Exception as e:
        return f"获取 {ticker} 现金流量表数据时出错: {str(e)}。建议检查股票代码是否正确。"


def get_yfinance_income_statements(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency: annual / quarterly (Yahoo Finance默认提供年度数据)",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    通过Yahoo Finance获取损益表数据
    Yahoo Finance提供免费的财务报表数据，无需API密钥
    """
    try:
        import yfinance as yf
        
        # 创建ticker对象
        stock = yf.Ticker(ticker)
        
        # 获取损益表
        financials = stock.financials
        
        if financials.empty:
            return f"暂无 {ticker} 公司的损益表数据。可能是该股票代码不存在或Yahoo Finance暂无数据。"
        
        # 取最新的财务数据
        latest_data = financials.iloc[:, 0]
        latest_date = financials.columns[0]
        
        # 格式化输出
        formatted_output = f"## Income Statement for {ticker} (Latest: {latest_date.strftime('%Y-%m-%d')}):\n\n"
        
        # 损益表主要项目
        formatted_output += "### Revenue & Costs:\n"
        formatted_output += f"- Total Revenue: {format_financial_value(latest_data.get('Total Revenue', 'N/A'))}\n"
        formatted_output += f"- Cost of Revenue: {format_financial_value(latest_data.get('Cost Of Revenue', 'N/A'))}\n"
        
        # 计算毛利润
        total_revenue = latest_data.get('Total Revenue', 0) or 0
        cost_of_revenue = latest_data.get('Cost Of Revenue', 0) or 0
        gross_profit = total_revenue - cost_of_revenue
        formatted_output += f"- Gross Profit: {format_financial_value(gross_profit)}\n"
        
        formatted_output += "\n### Operating Results:\n"
        formatted_output += f"- Operating Income: {format_financial_value(latest_data.get('Operating Income', 'N/A'))}\n"
        formatted_output += f"- Research & Development: {format_financial_value(latest_data.get('Research And Development', 'N/A'))}\n"
        formatted_output += f"- Selling General & Administrative: {format_financial_value(latest_data.get('Selling General And Administration', 'N/A'))}\n"
        formatted_output += f"- Total Operating Expenses: {format_financial_value(latest_data.get('Total Expenses', 'N/A'))}\n"
        
        formatted_output += "\n### Net Income:\n"
        formatted_output += f"- Income Before Tax: {format_financial_value(latest_data.get('Pretax Income', 'N/A'))}\n"
        formatted_output += f"- Tax Provision: {format_financial_value(latest_data.get('Tax Provision', 'N/A'))}\n"
        formatted_output += f"- Net Income: {format_financial_value(latest_data.get('Net Income', 'N/A'))}\n"
        
        # 获取股票信息计算每股收益
        try:
            info = stock.info
            shares_outstanding = info.get('sharesOutstanding', 0)
            net_income = latest_data.get('Net Income', 0) or 0
            if shares_outstanding and net_income:
                eps = net_income / shares_outstanding
                formatted_output += f"\n### Per Share Data:\n"
                formatted_output += f"- Earnings Per Share (calculated): ${eps:.2f}\n"
                formatted_output += f"- Shares Outstanding: {format_financial_value(shares_outstanding)}\n"
        except:
            pass
        
        # 计算关键比率
        if total_revenue and gross_profit:
            gross_margin = (gross_profit / total_revenue) * 100
            formatted_output += f"\n### Key Ratios:\n"
            formatted_output += f"- Gross Margin: {gross_margin:.2f}%\n"
            
            operating_income = latest_data.get('Operating Income', 0) or 0
            if operating_income:
                operating_margin = (operating_income / total_revenue) * 100
                formatted_output += f"- Operating Margin: {operating_margin:.2f}%\n"
            
            net_income = latest_data.get('Net Income', 0) or 0
            if net_income:
                net_margin = (net_income / total_revenue) * 100
                formatted_output += f"- Net Margin: {net_margin:.2f}%\n"
        
        return formatted_output
        
    except Exception as e:
        return f"获取 {ticker} 损益表数据时出错: {str(e)}。建议检查股票代码是否正确。"


def format_financial_value(value):
    """格式化财务数值显示"""
    if value == 'N/A' or value is None:
        return 'N/A'
    
    try:
        value = float(value)
        if abs(value) >= 1e12:
            return f"${value/1e12:.2f}T"
        elif abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:,.2f}"
    except:
        return str(value)


def get_google_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    query = query.replace(" ", "+")

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    news_results = getNewsData(query, before, curr_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return ""

    return f"## {query} Google News, from {before} to {curr_date}:\n\n{news_str}"


def get_reddit_global_news(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(desc=f"Getting Global News on {start_date}", total=total_iterations)

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "global_news",
            curr_date_str,
            max_limit_per_day,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)
        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"## Global News Reddit, from {before} to {curr_date}:\n{news_str}"


def get_reddit_company_news(
    ticker: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        ticker: ticker symbol of the company
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(
        desc=f"Getting Company News for {ticker} on {start_date}",
        total=total_iterations,
    )

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "company_news",
            curr_date_str,
            max_limit_per_day,
            ticker,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)

        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"##{ticker} News Reddit, from {before} to {curr_date}:\n\n{news_str}"


def get_stock_stats_indicators_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }

    if indicator not in best_ind_params:
        raise ValueError(
            f"Indicator {indicator} is not supported. Please choose from: {list(best_ind_params.keys())}"
        )

    end_date = curr_date
    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date - relativedelta(days=look_back_days)

    if not online:
        # read from YFin data
        data = pd.read_csv(
            os.path.join(
                DATA_DIR,
                f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
            )
        )
        data["Date"] = pd.to_datetime(data["Date"], utc=True)
        dates_in_df = data["Date"].astype(str).str[:10]

        ind_string = ""
        while curr_date >= before:
            # only do the trading dates
            if curr_date.strftime("%Y-%m-%d") in dates_in_df.values:
                indicator_value = get_stockstats_indicator(
                    symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
                )

                ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)
    else:
        # online gathering
        ind_string = ""
        while curr_date >= before:
            indicator_value = get_stockstats_indicator(
                symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
            )

            ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)

    result_str = (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {end_date}:\n\n"
        + ind_string
        + "\n\n"
        + best_ind_params.get(indicator, "No description available.")
    )

    return result_str


def get_stockstats_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    curr_date = curr_date.strftime("%Y-%m-%d")

    try:
        indicator_value = StockstatsUtils.get_stock_stats(
            symbol,
            indicator,
            curr_date,
            os.path.join(DATA_DIR, "market_data", "price_data"),
            online=online,
        )
    except Exception as e:
        print(
            f"Error getting stockstats indicator data for indicator {indicator} on {curr_date}: {e}"
        )
        return ""

    return str(indicator_value)


def get_YFin_data_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    # calculate past days
    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    start_date = before.strftime("%Y-%m-%d")

    # read in data using dynamic file finding
    from .utils import get_or_generate_data_filename
    data_file = get_or_generate_data_filename(symbol, "price")
    data = pd.read_csv(data_file)

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= curr_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # Set pandas display options to show the full DataFrame
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None, "display.width", None
    ):
        df_string = filtered_data.to_string()

    return (
        f"## Raw Market Data for {symbol} from {start_date} to {curr_date}:\n\n"
        + df_string
    )


def get_YFin_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    # 设置yfinance专用代理
    config = get_config()
    if config.get("use_proxy", False):
        import os
        http_proxy = config.get("http_proxy")
        https_proxy = config.get("https_proxy")
        if http_proxy:
            os.environ["http_proxy"] = http_proxy
        if https_proxy:
            os.environ["https_proxy"] = https_proxy

    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    # Create ticker object
    ticker = yf.Ticker(symbol.upper())

    # Fetch historical data for the specified date range
    data = ticker.history(start=start_date, end=end_date)

    # Check if data is empty
    if data.empty:
        return (
            f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
        )

    # Remove timezone info from index for cleaner output
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    # Round numerical values to 2 decimal places for cleaner display
    numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
    for col in numeric_columns:
        if col in data.columns:
            data[col] = data[col].round(2)

    # Convert DataFrame to CSV string
    csv_string = data.to_csv()

    # Add header information
    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(data)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string


def get_YFin_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    # 设置yfinance专用代理
    config = get_config()
    if config.get("use_proxy", False):
        import os
        http_proxy = config.get("http_proxy")
        https_proxy = config.get("https_proxy")
        if http_proxy:
            os.environ["http_proxy"] = http_proxy
        if https_proxy:
            os.environ["https_proxy"] = https_proxy
    # read in data using dynamic file finding
    from .utils import get_or_generate_data_filename
    data_file = get_or_generate_data_filename(symbol, "price")
    data = pd.read_csv(data_file)

    # 动态检查数据日期范围而不是硬编码
    if not data.empty:
        data_start = data["Date"].min()[:10]  # 提取日期部分
        data_end = data["Date"].max()[:10]
        if end_date > data_end or start_date < data_start:
            print(f"警告: 请求的日期范围 {start_date} 到 {end_date} 超出了数据范围 {data_start} 到 {data_end}")
            # 不抛出异常，而是使用可用的数据范围

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= end_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # remove the index from the dataframe
    filtered_data = filtered_data.reset_index(drop=True)

    return filtered_data


def get_stock_news_llm(ticker, curr_date):
    """
    通用股票新闻获取函数，适配所有LLM提供商
    使用标准的chat completion API，而非OpenAI专有功能
    """
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return f"API密钥未设置，无法获取{ticker}的最新社交媒体和新闻信息。请设置相应的环境变量。"
        
    try:
        client = OpenAI(base_url=config["backend_url"], api_key=api_key)
        
        # 构建查询提示
        prompt = f"""
请帮我分析{ticker}公司在{curr_date}前7天到{curr_date}期间的社交媒体和新闻情况。

请从以下方面进行分析：
1. 最近的公司新闻和公告
2. 社交媒体上的公众讨论和情绪
3. 分析师和投资者的观点
4. 市场反应和股价相关讨论
5. 任何可能影响股价的重要事件或消息

请提供具体的、有时间标记的信息，并分析这些信息对投资决策的影响。

注意：只关注{curr_date}前7天到{curr_date}这个时间段内的信息。
"""

        response = client.chat.completions.create(
            model=config["quick_think_llm"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位专业的股票新闻和社交媒体分析师。请基于你的知识和推理能力，提供关于指定公司的新闻和社交媒体分析。虽然你无法实时搜索，但请根据一般的市场趋势和公司情况提供有价值的分析观点。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # 如果LLM调用失败，返回一个基础的新闻查询结果
        return f"""
## {ticker} 社交媒体和新闻分析 ({curr_date}前7天到{curr_date})

**注意：** 由于API调用失败 ({str(e)})，无法获取实时的社交媒体和新闻数据。

**建议的分析方向：**
- 检查{ticker}的官方公告和财报
- 关注行业新闻和相关政策变化  
- 监控社交平台如推特、雪球等的讨论热度
- 分析同行业公司的表现对比
- 留意宏观经济因素对该股票的影响

**风险提示：** 建议通过多个可靠渠道验证新闻信息的真实性。
"""

def get_stock_news_openai(ticker, curr_date):
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
        
    client = OpenAI(base_url=config["backend_url"], api_key=api_key)

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"您能否搜索从{curr_date}前7天到{curr_date}期间关于{ticker}的社交媒体信息？确保您只获取该时间段内发布的数据。",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_global_news_llm(curr_date):
    """
    通用全球新闻获取函数，适配所有LLM提供商
    使用标准的chat completion API，而非OpenAI专有功能
    """
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return f"API密钥未设置，无法获取{curr_date}期间的全球宏观经济新闻信息。请设置相应的环境变量。"
        
    try:
        client = OpenAI(base_url=config["backend_url"], api_key=api_key)
        
        # 构建查询提示
        prompt = f"""
请分析{curr_date}前7天到{curr_date}期间的全球宏观经济新闻和趋势。

请从以下方面进行分析：
1. 主要经济体的重要经济数据和政策变化
2. 央行货币政策动向和利率变化
3. 国际贸易和地缘政治事件
4. 大宗商品和汇率市场的重要变化
5. 可能影响全球市场的重大新闻事件

请提供具体的、有时间标记的分析，并说明这些事件对全球投资市场的潜在影响。

注意：请基于一般的经济趋势和市场规律，提供有价值的宏观分析观点。
时间范围：{curr_date}前7天到{curr_date}
"""

        response = client.chat.completions.create(
            model=config["quick_think_llm"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位专业的宏观经济分析师和全球新闻分析专家。请基于你的知识和分析能力，提供关于指定时期的全球经济新闻分析。虽然你无法实时搜索，但请根据一般的经济趋势和市场规律提供有价值的宏观分析观点。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # 如果LLM调用失败，返回一个基础的分析结果
        return f"""
## 全球宏观经济新闻分析 ({curr_date}前7天到{curr_date})

**注意：** 由于API调用失败 ({str(e)})，无法获取实时的全球经济新闻数据。

**建议关注的重点领域：**
- 美联储、欧央行、中国人民银行等主要央行政策动向
- 美国、欧盟、中国等主要经济体的经济数据发布
- 国际贸易争端和地缘政治紧张局势
- 原油、黄金、美元指数等关键资产价格变化
- 通胀数据、就业数据、GDP增长率等核心指标

**分析建议：** 
- 关注央行官员讲话和政策信号
- 监控主要经济体的PMI、CPI、就业报告等数据
- 分析地缘政治事件对风险资产的影响
- 评估全球供应链和贸易流动的变化

**风险提示：** 宏观经济分析需要结合多方面信息，建议通过官方渠道验证重要经济数据。
"""


def get_fundamentals_llm(ticker, curr_date):
    """
    通用基本面分析获取函数，适配所有LLM提供商
    使用标准的chat completion API，而非OpenAI专有功能
    """
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return f"API密钥未设置，无法获取{ticker}的基本面分析信息。请设置相应的环境变量。"
        
    try:
        client = OpenAI(base_url=config["backend_url"], api_key=api_key)
        
        # 构建查询提示
        prompt = f"""
请分析{ticker}公司在{curr_date}前一个月到{curr_date}期间的基本面情况。

请从以下方面进行分析：
1. 财务指标分析（PE、PS、PB、ROE、ROA等）
2. 现金流状况和债务水平
3. 营收和利润增长趋势
4. 市场地位和竞争优势
5. 行业前景和公司发展战略
6. 管理层质量和公司治理
7. 分红政策和股东回报

请以表格形式总结关键财务指标，并提供详细的基本面分析报告。

注意：请基于该公司的一般经营特点和行业状况，提供专业的基本面分析观点。
分析时间：{curr_date}前一个月到{curr_date}
"""

        response = client.chat.completions.create(
            model=config["quick_think_llm"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位专业的基本面分析师和财务分析专家。请基于你的专业知识，提供关于指定公司的全面基本面分析。虽然你无法获取实时财务数据，但请根据该公司的经营特点、行业地位和一般财务规律提供有价值的分析观点。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # 如果LLM调用失败，返回一个基础的分析结果
        return f"""
## {ticker} 基本面分析 ({curr_date}前一个月到{curr_date})

**注意：** 由于API调用失败 ({str(e)})，无法获取实时的基本面分析数据。

**建议分析的关键指标：**

| 指标类别 | 关键指标 | 建议关注点 |
|---------|----------|-----------|
| 估值指标 | PE、PS、PB | 与行业平均水平对比 |
| 盈利能力 | ROE、ROA、毛利率 | 盈利质量和趋势变化 |
| 财务健康 | 负债率、流动比率 | 财务稳定性评估 |
| 成长性 | 营收增长率、净利润增长率 | 可持续增长能力 |
| 现金流 | 经营现金流、自由现金流 | 现金产生能力 |

**分析建议：**
- 查阅{ticker}最新的季度财报和年报
- 对比同行业公司的关键财务指标
- 关注公司的业务模式和盈利驱动因素
- 分析行业发展趋势对公司的影响
- 评估管理层的战略执行能力

**风险提示：** 基本面分析需要结合最新的财务数据，建议通过官方财报和权威财经平台获取准确信息。
"""


def get_global_news_openai(curr_date):
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
        
    client = OpenAI(base_url=config["backend_url"], api_key=api_key)

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"您能否搜索从{curr_date}前7天到{curr_date}期间对交易有参考价值的全球或宏观经济新闻？确保您只获取该时间段内发布的数据。",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_global_news_llm(curr_date):
    """
    通用全球新闻获取函数，适配所有LLM提供商
    使用标准的chat completion API，而非OpenAI专有功能
    """
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return f"API密钥未设置，无法获取{curr_date}期间的全球宏观经济新闻信息。请设置相应的环境变量。"
        
    try:
        client = OpenAI(base_url=config["backend_url"], api_key=api_key)
        
        # 构建查询提示
        prompt = f"""
请分析{curr_date}前7天到{curr_date}期间的全球宏观经济新闻和趋势。

请从以下方面进行分析：
1. 主要经济体的重要经济数据和政策变化
2. 央行货币政策动向和利率变化
3. 国际贸易和地缘政治事件
4. 大宗商品和汇率市场的重要变化
5. 可能影响全球市场的重大新闻事件

请提供具体的、有时间标记的分析，并说明这些事件对全球投资市场的潜在影响。

注意：请基于一般的经济趋势和市场规律，提供有价值的宏观分析观点。
时间范围：{curr_date}前7天到{curr_date}
"""

        response = client.chat.completions.create(
            model=config["quick_think_llm"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位专业的宏观经济分析师和全球新闻分析专家。请基于你的知识和分析能力，提供关于指定时期的全球经济新闻分析。虽然你无法实时搜索，但请根据一般的经济趋势和市场规律提供有价值的宏观分析观点。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # 如果LLM调用失败，返回一个基础的分析结果
        return f"""
## 全球宏观经济新闻分析 ({curr_date}前7天到{curr_date})

**注意：** 由于API调用失败 ({str(e)})，无法获取实时的全球经济新闻数据。

**建议关注的重点领域：**
- 美联储、欧央行、中国人民银行等主要央行政策动向
- 美国、欧盟、中国等主要经济体的经济数据发布
- 国际贸易争端和地缘政治紧张局势
- 原油、黄金、美元指数等关键资产价格变化
- 通胀数据、就业数据、GDP增长率等核心指标

**分析建议：** 
- 关注央行官员讲话和政策信号
- 监控主要经济体的PMI、CPI、就业报告等数据
- 分析地缘政治事件对风险资产的影响
- 评估全球供应链和贸易流动的变化

**风险提示：** 宏观经济分析需要结合多方面信息，建议通过官方渠道验证重要经济数据。
"""


def get_fundamentals_llm(ticker, curr_date):
    """
    通用基本面分析获取函数，适配所有LLM提供商
    使用标准的chat completion API，而非OpenAI专有功能
    """
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return f"API密钥未设置，无法获取{ticker}的基本面分析信息。请设置相应的环境变量。"
        
    try:
        client = OpenAI(base_url=config["backend_url"], api_key=api_key)
        
        # 构建查询提示
        prompt = f"""
请分析{ticker}公司在{curr_date}前一个月到{curr_date}期间的基本面情况。

请从以下方面进行分析：
1. 财务指标分析（PE、PS、PB、ROE、ROA等）
2. 现金流状况和债务水平
3. 营收和利润增长趋势
4. 市场地位和竞争优势
5. 行业前景和公司发展战略
6. 管理层质量和公司治理
7. 分红政策和股东回报

请以表格形式总结关键财务指标，并提供详细的基本面分析报告。

注意：请基于该公司的一般经营特点和行业状况，提供专业的基本面分析观点。
分析时间：{curr_date}前一个月到{curr_date}
"""

        response = client.chat.completions.create(
            model=config["quick_think_llm"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位专业的基本面分析师和财务分析专家。请基于你的专业知识，提供关于指定公司的全面基本面分析。虽然你无法获取实时财务数据，但请根据该公司的经营特点、行业地位和一般财务规律提供有价值的分析观点。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # 如果LLM调用失败，返回一个基础的分析结果
        return f"""
## {ticker} 基本面分析 ({curr_date}前一个月到{curr_date})

**注意：** 由于API调用失败 ({str(e)})，无法获取实时的基本面分析数据。

**建议分析的关键指标：**

| 指标类别 | 关键指标 | 建议关注点 |
|---------|----------|-----------|
| 估值指标 | PE、PS、PB | 与行业平均水平对比 |
| 盈利能力 | ROE、ROA、毛利率 | 盈利质量和趋势变化 |
| 财务健康 | 负债率、流动比率 | 财务稳定性评估 |
| 成长性 | 营收增长率、净利润增长率 | 可持续增长能力 |
| 现金流 | 经营现金流、自由现金流 | 现金产生能力 |

**分析建议：**
- 查阅{ticker}最新的季度财报和年报
- 对比同行业公司的关键财务指标
- 关注公司的业务模式和盈利驱动因素
- 分析行业发展趋势对公司的影响
- 评估管理层的战略执行能力

**风险提示：** 基本面分析需要结合最新的财务数据，建议通过官方财报和权威财经平台获取准确信息。
"""


def get_fundamentals_openai(ticker, curr_date):
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
        
    client = OpenAI(base_url=config["backend_url"], api_key=api_key)

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"您能否搜索关于{ticker}在{curr_date}前一个月到{curr_date}月期间的基本面讨论？确保您只获取该时间段内发布的数据。请以表格形式列出，包含PE/PS/现金流等。",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_global_news_llm(curr_date):
    """
    通用全球新闻获取函数，适配所有LLM提供商
    使用标准的chat completion API，而非OpenAI专有功能
    """
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return f"API密钥未设置，无法获取{curr_date}期间的全球宏观经济新闻信息。请设置相应的环境变量。"
        
    try:
        client = OpenAI(base_url=config["backend_url"], api_key=api_key)
        
        # 构建查询提示
        prompt = f"""
请分析{curr_date}前7天到{curr_date}期间的全球宏观经济新闻和趋势。

请从以下方面进行分析：
1. 主要经济体的重要经济数据和政策变化
2. 央行货币政策动向和利率变化
3. 国际贸易和地缘政治事件
4. 大宗商品和汇率市场的重要变化
5. 可能影响全球市场的重大新闻事件

请提供具体的、有时间标记的分析，并说明这些事件对全球投资市场的潜在影响。

注意：请基于一般的经济趋势和市场规律，提供有价值的宏观分析观点。
时间范围：{curr_date}前7天到{curr_date}
"""

        response = client.chat.completions.create(
            model=config["quick_think_llm"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位专业的宏观经济分析师和全球新闻分析专家。请基于你的知识和分析能力，提供关于指定时期的全球经济新闻分析。虽然你无法实时搜索，但请根据一般的经济趋势和市场规律提供有价值的宏观分析观点。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # 如果LLM调用失败，返回一个基础的分析结果
        return f"""
## 全球宏观经济新闻分析 ({curr_date}前7天到{curr_date})

**注意：** 由于API调用失败 ({str(e)})，无法获取实时的全球经济新闻数据。

**建议关注的重点领域：**
- 美联储、欧央行、中国人民银行等主要央行政策动向
- 美国、欧盟、中国等主要经济体的经济数据发布
- 国际贸易争端和地缘政治紧张局势
- 原油、黄金、美元指数等关键资产价格变化
- 通胀数据、就业数据、GDP增长率等核心指标

**分析建议：** 
- 关注央行官员讲话和政策信号
- 监控主要经济体的PMI、CPI、就业报告等数据
- 分析地缘政治事件对风险资产的影响
- 评估全球供应链和贸易流动的变化

**风险提示：** 宏观经济分析需要结合多方面信息，建议通过官方渠道验证重要经济数据。
"""


def get_fundamentals_llm(ticker, curr_date):
    """
    通用基本面分析获取函数，适配所有LLM提供商
    使用标准的chat completion API，而非OpenAI专有功能
    """
    config = get_config()
    
    # Get appropriate API key based on provider
    provider = config.get("llm_provider", "openai").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "alibaba dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:  # openai, ollama, etc.
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return f"API密钥未设置，无法获取{ticker}的基本面分析信息。请设置相应的环境变量。"
        
    try:
        client = OpenAI(base_url=config["backend_url"], api_key=api_key)
        
        # 构建查询提示
        prompt = f"""
请分析{ticker}公司在{curr_date}前一个月到{curr_date}期间的基本面情况。

请从以下方面进行分析：
1. 财务指标分析（PE、PS、PB、ROE、ROA等）
2. 现金流状况和债务水平
3. 营收和利润增长趋势
4. 市场地位和竞争优势
5. 行业前景和公司发展战略
6. 管理层质量和公司治理
7. 分红政策和股东回报

请以表格形式总结关键财务指标，并提供详细的基本面分析报告。

注意：请基于该公司的一般经营特点和行业状况，提供专业的基本面分析观点。
分析时间：{curr_date}前一个月到{curr_date}
"""

        response = client.chat.completions.create(
            model=config["quick_think_llm"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位专业的基本面分析师和财务分析专家。请基于你的专业知识，提供关于指定公司的全面基本面分析。虽然你无法获取实时财务数据，但请根据该公司的经营特点、行业地位和一般财务规律提供有价值的分析观点。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # 如果LLM调用失败，返回一个基础的分析结果
        return f"""
## {ticker} 基本面分析 ({curr_date}前一个月到{curr_date})

**注意：** 由于API调用失败 ({str(e)})，无法获取实时的基本面分析数据。

**建议分析的关键指标：**

| 指标类别 | 关键指标 | 建议关注点 |
|---------|----------|-----------|
| 估值指标 | PE、PS、PB | 与行业平均水平对比 |
| 盈利能力 | ROE、ROA、毛利率 | 盈利质量和趋势变化 |
| 财务健康 | 负债率、流动比率 | 财务稳定性评估 |
| 成长性 | 营收增长率、净利润增长率 | 可持续增长能力 |
| 现金流 | 经营现金流、自由现金流 | 现金产生能力 |

**分析建议：**
- 查阅{ticker}最新的季度财报和年报
- 对比同行业公司的关键财务指标
- 关注公司的业务模式和盈利驱动因素
- 分析行业发展趋势对公司的影响
- 评估管理层的战略执行能力

**风险提示：** 基本面分析需要结合最新的财务数据，建议通过官方财报和权威财经平台获取准确信息。
"""
