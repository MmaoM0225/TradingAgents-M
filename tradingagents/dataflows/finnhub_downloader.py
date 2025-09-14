"""
Finnhub数据下载器
提供从Finnhub API下载数据并保存到本地的功能
"""

import os
import json
import requests
from datetime import datetime
from .config import get_config

# 尝试加载.env文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装python-dotenv，就跳过
    pass


def download_finnhub_data(ticker, start_date, end_date, data_type):
    """
    从Finnhub API下载数据并保存到本地
    Args:
        ticker (str): 股票代码
        start_date (str): 开始日期 YYYY-MM-DD 
        end_date (str): 结束日期 YYYY-MM-DD
        data_type (str): 数据类型 (news_data, insider_senti, insider_trans)
    Returns:
        dict: 下载的数据
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print(f"警告: 未设置FINNHUB_API_KEY环境变量，无法下载{data_type}数据")
        return {}

    base_url = "https://finnhub.io/api/v1"
    
    try:
        if data_type == "news_data":
            # 下载新闻数据
            url = f"{base_url}/company-news"
            params = {
                "symbol": ticker,
                "from": start_date,
                "to": end_date,
                "token": api_key
            }
            
        elif data_type == "insider_senti":
            # 下载内部人情绪数据
            url = f"{base_url}/stock/insider-sentiment"
            params = {
                "symbol": ticker,
                "from": start_date,
                "to": end_date,
                "token": api_key
            }
            
        elif data_type == "insider_trans":
            # 下载内部人交易数据
            url = f"{base_url}/stock/insider-transactions"
            params = {
                "symbol": ticker,
                "from": start_date,
                "to": end_date,
                "token": api_key
            }
        else:
            print(f"不支持的数据类型: {data_type}")
            return {}

        print(f"正在下载 {ticker} 的 {data_type} 数据...")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # 确保目录存在
            current_data_dir = get_config()["data_dir"]
            data_dir = os.path.join(current_data_dir, "finnhub_data", data_type)
            os.makedirs(data_dir, exist_ok=True)
            
            # 按日期整理数据
            organized_data = {}
            
            if data_type == "news_data" and isinstance(data, list):
                for item in data:
                    date_str = datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d')
                    if date_str not in organized_data:
                        organized_data[date_str] = []
                    organized_data[date_str].append(item)
                    
            elif data_type in ["insider_senti", "insider_trans"]:
                if isinstance(data, dict) and 'data' in data:
                    for item in data['data']:
                        # 根据不同数据类型获取日期字段
                        if data_type == "insider_senti":
                            year = item.get('year', '')
                            month = str(item.get('month', '')).zfill(2) 
                            date_str = f"{year}-{month}-01"
                        else:  # insider_trans
                            # 处理内部人交易数据的日期字段，可能是时间戳或字符串
                            transaction_date = item.get('transactionDate', 0)
                            try:
                                if isinstance(transaction_date, (int, float)) and transaction_date > 0:
                                    # 如果是时间戳
                                    date_str = datetime.fromtimestamp(transaction_date).strftime('%Y-%m-%d')
                                elif isinstance(transaction_date, str) and transaction_date:
                                    # 如果是字符串日期，尝试解析
                                    try:
                                        date_obj = datetime.strptime(transaction_date, '%Y-%m-%d')
                                        date_str = date_obj.strftime('%Y-%m-%d')
                                    except ValueError:
                                        # 如果解析失败，使用当前日期
                                        date_str = datetime.now().strftime('%Y-%m-%d')
                                else:
                                    # 如果没有有效的日期数据，使用当前日期
                                    date_str = datetime.now().strftime('%Y-%m-%d')
                            except (ValueError, TypeError, OSError) as e:
                                print(f"处理transactionDate时出错: {e}, 原始值: {transaction_date}")
                                date_str = datetime.now().strftime('%Y-%m-%d')
                            
                        if date_str not in organized_data:
                            organized_data[date_str] = []
                        organized_data[date_str].append(item)
            
            # 保存到本地文件
            data_file = os.path.join(data_dir, f"{ticker}_data_formatted.json")
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(organized_data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ {data_type} 数据已保存到: {data_file}")
            return organized_data
            
        else:
            print(f"❌ Finnhub API请求失败: {response.status_code} - {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ 下载{data_type}数据时出错: {str(e)}")
        return {}
