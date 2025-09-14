import json
import os


def get_data_in_range(ticker, start_date, end_date, data_type, data_dir, period=None):
    """
    Gets finnhub data saved and processed on disk.
    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        data_type (str): Type of data from finnhub to fetch. Can be insider_trans, SEC_filings, news_data, insider_senti, or fin_as_reported.
        data_dir (str): Directory where the data is saved.
        period (str): Default to none, if there is a period specified, should be annual or quarterly.
    """

    if period:
        data_path = os.path.join(
            data_dir,
            "finnhub_data",
            data_type,
            f"{ticker}_{period}_data_formatted.json",
        )
    else:
        data_path = os.path.join(
            data_dir, "finnhub_data", data_type, f"{ticker}_data_formatted.json"
        )

    # 检查文件是否存在
    if not os.path.exists(data_path):
        return {}  # 如果文件不存在，返回空字典
        
    try:
        with open(data_path, "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}  # 如果文件读取失败，返回空字典
    except json.JSONDecodeError:
        return {}  # 如果JSON解析失败，返回空字典
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试GBK编码
        try:
            with open(data_path, "r", encoding='gbk') as f:
                data = json.load(f)
        except:
            return {}  # 如果仍然失败，返回空字典

    # filter keys (date, str in format YYYY-MM-DD) by the date range (str, str in format YYYY-MM-DD)
    filtered_data = {}
    for key, value in data.items():
        if len(value) == 0:
            continue
            
        # 针对内部人数据的特殊处理：按月数据需要特殊的日期匹配逻辑
        if data_type in ["insider_senti", "insider_trans"]:
            # 内部人数据按月统计，日期格式为 YYYY-MM-01
            # 需要检查该月是否与查询日期范围有重叠
            from datetime import datetime
            try:
                data_date = datetime.strptime(key, "%Y-%m-%d")
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                
                # 获取该月的最后一天
                if data_date.month == 12:
                    next_month = data_date.replace(year=data_date.year + 1, month=1, day=1)
                else:
                    next_month = data_date.replace(month=data_date.month + 1, day=1)
                from datetime import timedelta
                month_end = next_month - timedelta(days=1)
                
                # 检查月份范围是否与查询范围有重叠
                if data_date <= end_date_obj and month_end >= start_date_obj:
                    filtered_data[key] = value
            except ValueError:
                # 如果日期解析失败，使用原有逻辑
                if start_date <= key <= end_date:
                    filtered_data[key] = value
        else:
            # 其他数据类型使用原有的日期过滤逻辑
            if start_date <= key <= end_date:
                filtered_data[key] = value
                
    return filtered_data
