# Tushare A股数据接口函数
from typing import Annotated
import pandas as pd
from .tushare_utils import TushareUtils


def get_tushare_stock_data(
    symbol: Annotated[str, "A股代码，如000001、600000或000001.SZ"],
    start_date: Annotated[str, "开始日期，格式YYYY-mm-dd"],
    end_date: Annotated[str, "结束日期，格式YYYY-mm-dd"],
):
    """
    获取A股股票价格数据(OHLCV)
    
    Args:
        symbol: A股代码，支持以下格式：
               - 6位数字：000001(自动识别为000001.SZ)、600000(自动识别为600000.SH)
               - 完整代码：000001.SZ、600000.SH、688001.SH等
        start_date: 开始日期，格式YYYY-mm-dd
        end_date: 结束日期，格式YYYY-mm-dd
    
    Returns:
        str: 格式化的股价数据
    """
    try:
        tushare_utils = TushareUtils()
        stock_data = tushare_utils.get_stock_data(symbol, start_date, end_date)
        
        if stock_data.empty:
            return f"未找到 {symbol} 在 {start_date} 到 {end_date} 期间的股价数据"
        
        # 格式化输出
        latest_data = stock_data.tail(5)  # 显示最近5天的数据
        result = f"## {symbol} A股价格数据 ({start_date} 到 {end_date}):\n\n"
        result += f"**数据总数:** {len(stock_data)} 个交易日\n\n"
        result += "**最近5个交易日数据:**\n"
        result += latest_data.to_string()
        result += f"\n\n**当前价格:** {stock_data['Close'].iloc[-1]:.2f} 元\n"
        result += f"**期间涨跌幅:** {((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0] - 1) * 100):.2f}%\n"
        
        return result
        
    except Exception as e:
        return f"获取A股数据失败 {symbol}: {str(e)}"


def get_tushare_company_info(
    symbol: Annotated[str, "A股代码，如000001或000001.SZ"],
):
    """
    获取A股公司详细信息
    
    Args:
        symbol: A股代码，支持6位数字(如000001)或完整代码(如000001.SZ)
    
    Returns:
        str: 格式化的公司信息
    """
    try:
        tushare_utils = TushareUtils()
        company_info = tushare_utils.get_company_info(symbol)
        
        if company_info.empty:
            return f"未找到 {symbol} 的公司信息"
        
        info = company_info.iloc[0]
        
        result = f"## {symbol} 公司信息:\n\n"
        result += f"**公司名称:** {info.get('Company Name', 'N/A')}\n"
        result += f"**董事长:** {info.get('Chairman', 'N/A')}\n"
        result += f"**总经理:** {info.get('Manager', 'N/A')}\n"
        result += f"**董秘:** {info.get('Secretary', 'N/A')}\n"
        result += f"**注册资本:** {info.get('Reg Capital', 'N/A')}\n"
        result += f"**成立日期:** {info.get('Setup Date', 'N/A')}\n"
        result += f"**所在省份:** {info.get('Province', 'N/A')}\n"
        result += f"**所在城市:** {info.get('City', 'N/A')}\n"
        result += f"**交易所:** {info.get('Exchange', 'N/A')}\n"
        result += f"**公司网站:** {info.get('Website', 'N/A')}\n"
        result += f"**电子邮箱:** {info.get('Email', 'N/A')}\n"
        result += f"**员工人数:** {info.get('Employees', 'N/A')}\n"
        
        result += f"\n**数据说明:** 基于tushare获取的A股公司详细信息。"
        
        return result
        
    except Exception as e:
        return f"获取A股公司信息失败 {symbol}: {str(e)}"


def get_tushare_balance_sheet(
    symbol: Annotated[str, "A股代码，如000001.SZ"],
    freq: Annotated[str, "报告频率: annual(年报) / quarterly(季报)"],
    curr_date: Annotated[str, "当前日期，格式yyyy-mm-dd"],
):
    """
    获取A股资产负债表数据
    """
    try:
        tushare_utils = TushareUtils()
        balance_sheet = tushare_utils.get_balance_sheet(symbol, freq)
        
        if balance_sheet.empty:
            return f"未找到 {symbol} 的资产负债表数据"
        
        latest_report = balance_sheet.iloc[0]
        result = f"## {symbol} {freq}资产负债表 (报告期: {latest_report.get('end_date', 'N/A')}):\n\n"
        
        # 主要财务指标
        key_items = {
            'total_assets': '总资产',
            'total_liab': '总负债', 
            'total_hldr_eqy_exc_min_int': '股东权益合计',
        }
        
        result += "**主要财务指标:**\n"
        for field, name in key_items.items():
            value = latest_report.get(field, 0)
            if pd.notna(value) and value != 0:
                result += f"- {name}: {value:,.0f} 万元\n"
        
        return result
        
    except Exception as e:
        return f"获取A股资产负债表失败 {symbol}: {str(e)}"


def get_tushare_cashflow(
    symbol: Annotated[str, "A股代码，如000001.SZ"],
    freq: Annotated[str, "报告频率: annual(年报) / quarterly(季报)"],
    curr_date: Annotated[str, "当前日期，格式yyyy-mm-dd"],
):
    """
    获取A股现金流量表数据
    """
    try:
        tushare_utils = TushareUtils()
        cashflow = tushare_utils.get_cash_flow(symbol, freq)
        
        if cashflow.empty:
            return f"未找到 {symbol} 的现金流量表数据"
        
        latest_report = cashflow.iloc[0]
        result = f"## {symbol} {freq}现金流量表 (报告期: {latest_report.get('end_date', 'N/A')}):\n\n"
        
        # 主要现金流项目
        key_items = {
            'n_cashflow_act': '经营活动现金流量净额',
            'n_cashflow_inv_act': '投资活动现金流量净额',
            'n_cashflow_fin_act': '筹资活动现金流量净额',
        }
        
        result += "**主要现金流指标:**\n"
        for field, name in key_items.items():
            value = latest_report.get(field, 0)
            if pd.notna(value):
                result += f"- {name}: {value:,.0f} 万元\n"
        
        return result
        
    except Exception as e:
        return f"获取A股现金流量表失败 {symbol}: {str(e)}"


def get_tushare_income_statements(
    symbol: Annotated[str, "A股代码，如000001.SZ"],
    freq: Annotated[str, "报告频率: annual(年报) / quarterly(季报)"],
    curr_date: Annotated[str, "当前日期，格式yyyy-mm-dd"],
):
    """
    获取A股利润表数据
    """
    try:
        tushare_utils = TushareUtils()
        income_stmt = tushare_utils.get_income_stmt(symbol, freq)
        
        if income_stmt.empty:
            return f"未找到 {symbol} 的利润表数据"
        
        latest_report = income_stmt.iloc[0]
        result = f"## {symbol} {freq}利润表 (报告期: {latest_report.get('end_date', 'N/A')}):\n\n"
        
        # 主要利润表项目
        key_items = {
            'revenue': '营业收入',
            'oper_cost': '营业成本',
            'n_income': '净利润',
            'basic_eps': '基本每股收益',
        }
        
        result += "**主要经营指标:**\n"
        for field, name in key_items.items():
            value = latest_report.get(field, 0)
            if pd.notna(value):
                if 'eps' in field:
                    result += f"- {name}: {value:.4f} 元\n"
                else:
                    result += f"- {name}: {value:,.0f} 万元\n"
        
        return result
        
    except Exception as e:
        return f"获取A股利润表失败 {symbol}: {str(e)}"


def get_tushare_daily_basic(
    symbol: Annotated[str, "A股代码，如000001.SZ"],
    curr_date: Annotated[str, "当前日期，格式yyyy-mm-dd"],
    look_back_days: Annotated[int, "回看天数"] = 30,
):
    """
    获取A股每日基本面数据(市盈率、市净率等)
    """
    try:
        # 计算开始日期
        curr_date_dt = pd.to_datetime(curr_date)
        start_date_dt = curr_date_dt - pd.Timedelta(days=look_back_days)
        start_date = start_date_dt.strftime("%Y-%m-%d")
        
        tushare_utils = TushareUtils()
        daily_basic = tushare_utils.get_daily_basic(symbol, start_date, curr_date)
        
        if daily_basic.empty:
            return f"未找到 {symbol} 在 {start_date} 到 {curr_date} 期间的基本面数据"
        
        # 获取最新的数据
        latest_data = daily_basic.iloc[-1]
        
        result = f"## {symbol} A股基本面数据 (截至 {curr_date}):\n\n"
        
        # 主要估值指标
        key_metrics = {
            'pe': '市盈率(PE)',
            'pb': '市净率(PB)',
            'total_mv': '总市值(万元)',
            'circ_mv': '流通市值(万元)',
        }
        
        result += "**估值指标:**\n"
        for field, name in key_metrics.items():
            value = latest_data.get(field, None)
            if pd.notna(value) and value != 0:
                if 'mv' in field:
                    result += f"- {name}: {value:,.0f}\n"
                else:
                    result += f"- {name}: {value:.2f}\n"
        
        return result
        
    except Exception as e:
        return f"获取A股基本面数据失败 {symbol}: {str(e)}"


def get_tushare_stock_stats(
    symbol: Annotated[str, "A股代码，如000001或000001.SZ"],
    indicator: Annotated[str, "技术指标名称，如RSI, MACD, MA等"],
    curr_date: Annotated[str, "当前日期，格式yyyy-mm-dd"],
    look_back_days: Annotated[int, "回看天数"] = 30,
):
    """
    获取A股技术指标数据
    
    Args:
        symbol: A股代码
        indicator: 技术指标名称 (RSI, MACD, MA, EMA, BOLL, KDJ, CCI, ATR, OBV)
        curr_date: 当前日期
        look_back_days: 回看天数，默认30天
    
    Returns:
        str: 格式化的技术指标数据
    """
    try:
        tushare_utils = TushareUtils()
        stats_data = tushare_utils.get_stock_stats(symbol, indicator, curr_date, look_back_days)
        
        if stats_data.empty:
            return f"未找到 {symbol} 的 {indicator} 技术指标数据"
        
        # 获取最新的数据
        latest_data = stats_data.tail(5)  # 显示最近5天的数据
        
        result = f"## {symbol} {indicator.upper()} 技术指标 (截至 {curr_date}):\n\n"
        result += f"**数据总数:** {len(stats_data)} 个交易日\n\n"
        result += "**最近5个交易日数据:**\n"
        result += latest_data.to_string()
        
        # 根据不同指标提供分析
        latest_row = stats_data.iloc[-1]
        
        if indicator.lower() == 'rsi':
            rsi_value = latest_row.get('rsi_14', 0)
            if rsi_value > 70:
                signal = "超买信号"
            elif rsi_value < 30:
                signal = "超卖信号"
            else:
                signal = "中性区间"
            result += f"\n\n**技术分析:**\n- 当前RSI: {rsi_value:.2f}\n- 信号: {signal}"
            
        elif indicator.lower() == 'macd':
            macd = latest_row.get('macd', 0)
            macds = latest_row.get('macds', 0)
            signal = "金叉(看涨)" if macd > macds else "死叉(看跌)"
            result += f"\n\n**技术分析:**\n- MACD: {macd:.4f}\n- Signal: {macds:.4f}\n- 信号: {signal}"
            
        elif indicator.lower() in ['ma', 'sma']:
            close = latest_row.get('close', 0)
            ma20 = latest_row.get('close_20_sma', 0)
            trend = "上升趋势" if close > ma20 else "下降趋势"
            result += f"\n\n**技术分析:**\n- 当前价格: {close:.2f}\n- MA20: {ma20:.2f}\n- 趋势: {trend}"
        
        result += f"\n\n**数据说明:** 基于tushare获取的A股数据计算的技术指标。"
        
        return result
        
    except Exception as e:
        return f"获取A股技术指标失败 {symbol}: {str(e)}"
