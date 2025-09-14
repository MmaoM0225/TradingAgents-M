import os
import json
import pandas as pd
from datetime import date, timedelta, datetime
from typing import Annotated, Tuple, Optional
import glob
from .config import get_config

SavePathType = Annotated[str, "File path to save data. If None, data is not saved."]

def save_output(data: pd.DataFrame, tag: str, save_path: SavePathType = None) -> None:
    if save_path:
        data.to_csv(save_path, encoding='utf-8')
        print(f"{tag} saved to {save_path}")


def get_current_date():
    return date.today().strftime("%Y-%m-%d")


def get_dynamic_date_range(years_back: int = None) -> Tuple[str, str]:
    """
    获取动态的日期范围
    Args:
        years_back: 回溯年数，如果为None则使用配置中的默认值
    Returns:
        (start_date, end_date) 元组，格式为 YYYY-mm-dd
    """
    config = get_config()
    if years_back is None:
        years_back = config.get("data_years_back", 15)
    
    today = pd.Timestamp.today()
    start_date = today - pd.DateOffset(years=years_back)
    
    return start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def find_data_file(symbol: str, data_type: str = "price") -> Optional[str]:
    """
    自动查找数据文件，支持不同的日期范围格式
    Args:
        symbol: 股票代码
        data_type: 数据类型 ('price' 或 'cache')
    Returns:
        找到的文件路径，如果没找到返回None
    """
    config = get_config()
    
    if data_type == "price":
        search_dir = config["price_data_dir"]
        pattern = f"{symbol}-YFin-data-*.csv"
    else:  # cache
        search_dir = config["data_cache_dir"]
        pattern = f"{symbol}-YFin-data-*.csv"
    
    # 搜索匹配的文件
    search_pattern = os.path.join(search_dir, pattern)
    matching_files = glob.glob(search_pattern)
    
    if matching_files:
        # 返回最新的文件（按文件名排序，通常日期越新排在后面）
        return sorted(matching_files)[-1]
    
    return None


def get_or_generate_data_filename(symbol: str, data_type: str = "price", 
                                use_dynamic: bool = None) -> str:
    """
    获取或生成数据文件名
    Args:
        symbol: 股票代码
        data_type: 数据类型 ('price' 或 'cache')  
        use_dynamic: 是否使用动态日期范围，如果为None则使用配置
    Returns:
        数据文件的完整路径
    """
    config = get_config()
    
    if use_dynamic is None:
        use_dynamic = config.get("use_dynamic_date_range", True)
    
    # 首先尝试找到现有文件
    existing_file = find_data_file(symbol, data_type)
    if existing_file and os.path.exists(existing_file):
        return existing_file
    
    # 如果没有找到现有文件，生成新的文件名
    if use_dynamic:
        start_date, end_date = get_dynamic_date_range()
    else:
        start_date = config.get("default_data_start", "2010-01-01")
        end_date = get_current_date()
    
    filename = f"{symbol}-YFin-data-{start_date}-{end_date}.csv"
    
    if data_type == "price":
        return os.path.join(config["price_data_dir"], filename)
    else:  # cache
        return os.path.join(config["data_cache_dir"], filename)


def decorate_all_methods(decorator):
    def class_decorator(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value):
                setattr(cls, attr_name, decorator(attr_value))
        return cls

    return class_decorator


def get_next_weekday(date):

    if not isinstance(date, datetime):
        date = datetime.strptime(date, "%Y-%m-%d")

    if date.weekday() >= 5:
        days_to_add = 7 - date.weekday()
        next_weekday = date + timedelta(days=days_to_add)
        return next_weekday
    else:
        return date
