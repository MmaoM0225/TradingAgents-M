# 获取A股数据 - 基于tushare

import tushare as ts
from typing import Annotated, Callable, Any, Optional
from pandas import DataFrame
import pandas as pd
from functools import wraps
from datetime import datetime, timedelta
import os
from stockstats import wrap

from .utils import save_output, SavePathType, decorate_all_methods
from .config import get_config

# 加载.env文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装python-dotenv，就跳过
    pass


def normalize_stock_code(symbol: str) -> str:
    """
    标准化股票代码，自动添加交易所后缀
    
    Args:
        symbol: 股票代码，可以是6位数字或已包含后缀的完整代码
        
    Returns:
        str: 标准化的股票代码（包含交易所后缀）
        
    Examples:
        normalize_stock_code("000001") -> "000001.SZ"  # 深交所主板
        normalize_stock_code("002001") -> "002001.SZ"  # 深交所中小板
        normalize_stock_code("300001") -> "300001.SZ"  # 深交所创业板
        normalize_stock_code("600000") -> "600000.SH"  # 上交所主板
        normalize_stock_code("688001") -> "688001.SH"  # 上交所科创板
        normalize_stock_code("430001") -> "430001.BJ"  # 北交所
        normalize_stock_code("000001.SZ") -> "000001.SZ"  # 已有后缀，保持不变
    """
    # 如果已经包含后缀，直接返回
    if '.' in symbol:
        return symbol.upper()
    
    # 如果不是6位数字，直接返回原值
    if not symbol.isdigit() or len(symbol) != 6:
        return symbol
    
    # 根据股票代码前缀判断交易所
    code_prefix = symbol[:3]
    
    # 深交所股票代码规则
    if code_prefix.startswith('00'):  # 000xxx - 深交所主板
        return f"{symbol}.SZ"
    elif code_prefix.startswith('002'):  # 002xxx - 深交所中小板
        return f"{symbol}.SZ"
    elif code_prefix.startswith('300'):  # 300xxx - 深交所创业板
        return f"{symbol}.SZ"
    
    # 上交所股票代码规则
    elif code_prefix.startswith('60'):  # 60xxxx - 上交所主板
        return f"{symbol}.SH"
    elif code_prefix.startswith('688'):  # 688xxx - 上交所科创板
        return f"{symbol}.SH"
    elif code_prefix.startswith('689'):  # 689xxx - 上交所科创板
        return f"{symbol}.SH"
    
    # 北交所股票代码规则
    elif code_prefix.startswith('43') or code_prefix.startswith('83') or code_prefix.startswith('87'):
        return f"{symbol}.BJ"
    
    # 其他情况，可能是港股或其他市场，保持原样
    else:
        # 默认判断：6开头的认为是上交所，其他认为是深交所
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"


def detect_stock_type(symbol: str) -> str:
    """
    自动检测股票类型
    
    Args:
        symbol: 股票代码
        
    Returns:
        str: "CN" (A股) 或 "US" (美股)
    """
    # 标准化代码
    normalized = normalize_stock_code(symbol)
    
    # 如果包含中国交易所后缀，则为A股
    if any(suffix in normalized.upper() for suffix in ['.SZ', '.SH', '.BJ']):
        return "CN"
    
    # 如果是6位纯数字，很可能是A股
    if symbol.isdigit() and len(symbol) == 6:
        return "CN"
    
    # 其他情况默认为美股
    return "US"


def init_tushare(func: Callable) -> Callable:
    """Decorator to initialize tushare pro api and pass it to the function."""

    @wraps(func)
    def wrapper(self, symbol: Annotated[str, "股票代码，如000001或000001.SZ"], *args, **kwargs) -> Any:
        config = get_config()
        token = config.get("tushare_token") or os.getenv("TUSHARE_TOKEN")
        
        if not token:
            raise ValueError("请设置tushare token。可以在配置文件中设置tushare_token或设置环境变量TUSHARE_TOKEN")
        
        # 标准化股票代码
        normalized_symbol = normalize_stock_code(symbol)
        
        # 初始化tushare pro api
        pro = ts.pro_api(token)
        return func(pro, normalized_symbol, *args, **kwargs)

    return wrapper


@decorate_all_methods(init_tushare)
class TushareUtils:

    def get_stock_data(
        pro_api,  # tushare pro api实例
        symbol: Annotated[str, "股票代码，如000001、600000或000001.SZ"],
        start_date: Annotated[
            str, "开始日期，格式YYYY-mm-dd"
        ],
        end_date: Annotated[
            str, "结束日期，格式YYYY-mm-dd"
        ],
        save_path: SavePathType = None,
    ) -> DataFrame:
        """获取A股股票价格数据(OHLCV)"""
        try:
            # 转换日期格式为tushare需要的格式(YYYYMMDD)
            start_date_ts = pd.to_datetime(start_date).strftime("%Y%m%d")
            end_date_ts = pd.to_datetime(end_date).strftime("%Y%m%d")
            
            # 获取日线数据
            stock_data = pro_api.daily(
                ts_code=symbol,
                start_date=start_date_ts,
                end_date=end_date_ts
            )
            
            if stock_data.empty:
                print(f"未找到股票数据 {symbol}: {start_date} 到 {end_date}")
                return pd.DataFrame()
            
            # 转换为yfinance格式的列名，便于兼容现有代码
            stock_data = stock_data.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'vol': 'Volume',
                'amount': 'Amount'
            })
            
            # 设置日期为索引
            stock_data['trade_date'] = pd.to_datetime(stock_data['trade_date'])
            stock_data = stock_data.set_index('trade_date')
            stock_data = stock_data.sort_index()  # 按日期升序排列
            
            # 只保留OHLCV列
            stock_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            if save_path:
                save_output(stock_data, f"A股数据 {symbol}", save_path)
                
            return stock_data
            
        except Exception as e:
            print(f"获取A股数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_info(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001或000001.SZ"],
    ) -> dict:
        """获取A股基本信息"""
        try:
            # 获取股票基本信息
            basic_info = pro_api.stock_basic(ts_code=symbol, fields='ts_code,symbol,name,area,industry,market,list_date')
            
            if basic_info.empty:
                print(f"未找到股票基本信息 {symbol}")
                return {}
            
            info = basic_info.iloc[0]
            stock_info = {
                'ts_code': info.get('ts_code', 'N/A'),
                'symbol': info.get('symbol', 'N/A'),
                'name': info.get('name', 'N/A'),
                'area': info.get('area', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market': info.get('market', 'N/A'),
                'list_date': info.get('list_date', 'N/A')
            }
            
            return stock_info
            
        except Exception as e:
            print(f"获取股票信息失败 {symbol}: {e}")
            return {}

    def get_company_info(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001或000001.SZ"],
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """获取A股公司详细信息（使用stock_company接口）"""
        try:
            # 获取公司详细信息
            company_data = pro_api.stock_company(ts_code=symbol)
            
            if company_data.empty:
                company_info = {
                    "Company Name": "N/A",
                    "Chairman": "N/A",
                    "Manager": "N/A",
                    "Secretary": "N/A",
                    "Reg Capital": "N/A",
                    "Setup Date": "N/A",
                    "Province": "N/A",
                    "City": "N/A",
                    "Exchange": "N/A",
                    "Website": "N/A",
                    "Email": "N/A",
                    "Employees": "N/A",
                }
            else:
                info = company_data.iloc[0]
                
                # 如果com_name为空，尝试从stock_basic获取公司名称
                company_name = info.get("com_name")
                if not company_name or pd.isna(company_name):
                    try:
                        basic_info = pro_api.stock_basic(ts_code=symbol, fields='name')
                        if not basic_info.empty:
                            company_name = basic_info.iloc[0].get('name', 'N/A')
                        else:
                            company_name = "N/A"
                    except:
                        company_name = "N/A"
                
                company_info = {
                    "Company Name": company_name,
                    "Chairman": info.get("chairman", "N/A"),
                    "Manager": info.get("manager", "N/A"),
                    "Secretary": info.get("secretary", "N/A"),
                    "Reg Capital": f"{info.get('reg_capital', 0):,.0f}万元" if pd.notna(info.get('reg_capital')) and info.get('reg_capital', 0) > 0 else "N/A",
                    "Setup Date": info.get("setup_date", "N/A"),
                    "Province": info.get("province", "N/A"),
                    "City": info.get("city", "N/A"),
                    "Exchange": info.get("exchange", "N/A"),
                    "Website": info.get("website", "N/A"),
                    "Email": info.get("email", "N/A"),
                    "Employees": f"{info.get('employees', 0):,}人" if pd.notna(info.get('employees')) and info.get('employees', 0) > 0 else "N/A",
                }
                
        except Exception as e:
            print(f"获取公司信息失败 {symbol}: {e}")
            company_info = {
                "Company Name": "N/A",
                "Chairman": "N/A",
                "Manager": "N/A",
                "Secretary": "N/A",
                "Reg Capital": "N/A",
                "Setup Date": "N/A",
                "Province": "N/A",
                "City": "N/A",
                "Exchange": "N/A",
                "Website": "N/A",
                "Email": "N/A",
                "Employees": "N/A",
            }
            
        company_info_df = DataFrame([company_info])
        if save_path:
            company_info_df.to_csv(save_path, encoding='utf-8')
            print(f"公司信息 {symbol} 已保存到 {save_path}")
        return company_info_df

    def get_stock_dividends(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001.SZ"],
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """获取A股分红数据"""
        try:
            # 获取分红送股数据
            dividends = pro_api.dividend(ts_code=symbol)
            
            if dividends.empty:
                print(f"未找到分红数据 {symbol}")
                return pd.DataFrame()
                
            # 转换日期格式
            if 'div_proc' in dividends.columns:
                dividends['div_proc'] = pd.to_datetime(dividends['div_proc'])
                dividends = dividends.set_index('div_proc')
                dividends = dividends.sort_index()
                
            if save_path:
                dividends.to_csv(save_path, encoding='utf-8')
                print(f"分红数据 {symbol} 已保存到 {save_path}")
                
            return dividends
            
        except Exception as e:
            print(f"获取分红数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_income_stmt(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001.SZ"],
        period: Annotated[str, "报告期类型：annual(年报), quarterly(季报)"] = "annual"
    ) -> DataFrame:
        """获取A股利润表"""
        try:
            # 根据period参数选择报告类型
            report_type = '1' if period == 'annual' else '3'  # 1:年报, 3:季报
            
            # 获取利润表数据
            income_stmt = pro_api.income(ts_code=symbol, report_type=report_type)
            
            if income_stmt.empty:
                print(f"未找到利润表数据 {symbol}")
                return pd.DataFrame()
                
            # 按报告期排序
            if 'end_date' in income_stmt.columns:
                income_stmt['end_date'] = pd.to_datetime(income_stmt['end_date'])
                income_stmt = income_stmt.sort_values('end_date', ascending=False)
                
            return income_stmt
            
        except Exception as e:
            print(f"获取利润表失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_balance_sheet(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001.SZ"],
        period: Annotated[str, "报告期类型：annual(年报), quarterly(季报)"] = "annual"
    ) -> DataFrame:
        """获取A股资产负债表"""
        try:
            # 根据period参数选择报告类型
            report_type = '1' if period == 'annual' else '3'  # 1:年报, 3:季报
            
            # 获取资产负债表数据
            balance_sheet = pro_api.balancesheet(ts_code=symbol, report_type=report_type)
            
            if balance_sheet.empty:
                print(f"未找到资产负债表数据 {symbol}")
                return pd.DataFrame()
                
            # 按报告期排序
            if 'end_date' in balance_sheet.columns:
                balance_sheet['end_date'] = pd.to_datetime(balance_sheet['end_date'])
                balance_sheet = balance_sheet.sort_values('end_date', ascending=False)
                
            return balance_sheet
            
        except Exception as e:
            print(f"获取资产负债表失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_cash_flow(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001.SZ"],
        period: Annotated[str, "报告期类型：annual(年报), quarterly(季报)"] = "annual"
    ) -> DataFrame:
        """获取A股现金流量表"""
        try:
            # 根据period参数选择报告类型
            report_type = '1' if period == 'annual' else '3'  # 1:年报, 3:季报
            
            # 获取现金流量表数据
            cash_flow = pro_api.cashflow(ts_code=symbol, report_type=report_type)
            
            if cash_flow.empty:
                print(f"未找到现金流量表数据 {symbol}")
                return pd.DataFrame()
                
            # 按报告期排序
            if 'end_date' in cash_flow.columns:
                cash_flow['end_date'] = pd.to_datetime(cash_flow['end_date'])
                cash_flow = cash_flow.sort_values('end_date', ascending=False)
                
            return cash_flow
            
        except Exception as e:
            print(f"获取现金流量表失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_daily_basic(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001.SZ"],
        start_date: Annotated[str, "开始日期，格式YYYY-mm-dd"],
        end_date: Annotated[str, "结束日期，格式YYYY-mm-dd"],
    ) -> DataFrame:
        """获取A股每日基本面数据(市盈率、市净率等)"""
        try:
            # 转换日期格式
            start_date_ts = pd.to_datetime(start_date).strftime("%Y%m%d")
            end_date_ts = pd.to_datetime(end_date).strftime("%Y%m%d")
            
            # 获取每日基本面数据
            daily_basic = pro_api.daily_basic(
                ts_code=symbol,
                start_date=start_date_ts,
                end_date=end_date_ts
            )
            
            if daily_basic.empty:
                print(f"未找到每日基本面数据 {symbol}: {start_date} 到 {end_date}")
                return pd.DataFrame()
                
            # 设置日期为索引
            daily_basic['trade_date'] = pd.to_datetime(daily_basic['trade_date'])
            daily_basic = daily_basic.set_index('trade_date')
            daily_basic = daily_basic.sort_index()
            
            return daily_basic
            
        except Exception as e:
            print(f"获取每日基本面数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_list(
        pro_api,
        exchange: Annotated[str, "交易所：SSE(上交所), SZSE(深交所)"] = None,
        list_status: Annotated[str, "上市状态：L(上市), D(退市), P(暂停上市)"] = "L"
    ) -> DataFrame:
        """获取A股股票列表"""
        try:
            # 获取股票基本信息
            stock_list = pro_api.stock_basic(
                exchange=exchange,
                list_status=list_status,
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            if stock_list.empty:
                print("未找到股票列表数据")
                return pd.DataFrame()
                
            return stock_list
            
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_stock_stats(
        pro_api,
        symbol: Annotated[str, "股票代码，如000001或000001.SZ"],
        indicator: Annotated[str, "技术指标名称，如RSI, MACD, MA等"],
        curr_date: Annotated[str, "当前日期，格式YYYY-mm-dd"],
        look_back_days: Annotated[int, "回看天数"] = 252,
    ) -> DataFrame:
        """
        获取A股技术指标数据
        
        Args:
            symbol: A股代码
            indicator: 技术指标名称
            curr_date: 当前日期
            look_back_days: 回看天数，默认252天(约一年)
            
        Returns:
            DataFrame: 包含技术指标的数据
        """
        try:
            # 计算开始日期
            curr_date_dt = pd.to_datetime(curr_date)
            start_date_dt = curr_date_dt - pd.Timedelta(days=look_back_days * 1.5)  # 多取一些数据确保有足够的计算基础
            start_date = start_date_dt.strftime("%Y-%m-%d")
            
            # 获取股价数据
            tushare_utils = TushareUtils()
            stock_data = tushare_utils.get_stock_data(symbol, start_date, curr_date)
            
            if stock_data.empty:
                print(f"未找到股价数据 {symbol}: {start_date} 到 {curr_date}")
                return pd.DataFrame()
            
            # 使用stockstats计算技术指标
            stock_stats = wrap(stock_data)
            
            # 根据指标名称获取相应数据
            indicator_lower = indicator.lower()
            
            if indicator_lower == 'rsi':
                result_data = stock_stats[['close', 'rsi_14']]
            elif indicator_lower == 'macd':
                result_data = stock_stats[['close', 'macd', 'macds', 'macdh']]
            elif indicator_lower in ['ma', 'sma']:
                result_data = stock_stats[['close', 'close_5_sma', 'close_10_sma', 'close_20_sma', 'close_60_sma']]
            elif indicator_lower == 'ema':
                result_data = stock_stats[['close', 'close_12_ema', 'close_26_ema']]
            elif indicator_lower == 'bollinger' or indicator_lower == 'boll':
                result_data = stock_stats[['close', 'boll', 'boll_ub', 'boll_lb']]
            elif indicator_lower == 'kdj':
                result_data = stock_stats[['close', 'kdjk', 'kdjd', 'kdjj']]
            elif indicator_lower == 'cci':
                result_data = stock_stats[['close', 'cci']]
            elif indicator_lower == 'atr':
                result_data = stock_stats[['close', 'atr']]
            elif indicator_lower == 'obv':
                result_data = stock_stats[['close', 'volume', 'obv']]
            else:
                # 默认返回常用指标
                result_data = stock_stats[['close', 'rsi_14', 'macd', 'close_20_sma']]
            
            # 只返回指定时间范围内的数据
            end_date_dt = pd.to_datetime(curr_date)
            start_filter_dt = end_date_dt - pd.Timedelta(days=look_back_days)
            
            result_data = result_data[result_data.index >= start_filter_dt]
            
            return result_data
            
        except Exception as e:
            print(f"获取A股技术指标失败 {symbol}: {e}")
            return pd.DataFrame()

