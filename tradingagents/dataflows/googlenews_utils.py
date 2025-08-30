import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
)


def is_rate_limited(response):
    """Check if the response indicates rate limiting (status code 429)"""
    return response.status_code == 429


@retry(
    retry=(retry_if_result(is_rate_limited)),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
)
def make_request(url, headers):
    """Make a request with retry logic for rate limiting"""
    # Random delay before each request to avoid detection
    time.sleep(random.uniform(2, 6))
    response = requests.get(url, headers=headers)
    return response


def getNewsData(query, start_date, end_date):
    """
    Scrape Google News search results for a given query and date range.
    query: str - search query
    start_date: str - start date in the format yyyy-mm-dd or mm/dd/yyyy
    end_date: str - end date in the format yyyy-mm-dd or mm/dd/yyyy
    """
    if "-" in start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = start_date.strftime("%m/%d/%Y")
    if "-" in end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date.strftime("%m/%d/%Y")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.54 Safari/537.36"
        )
    }

    news_results = []
    page = 0
    while True:
        offset = page * 10
        url = (
            f"https://www.google.com/search?q={query}"
            f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"
            f"&tbm=nws&start={offset}"
        )

        try:
            response = make_request(url, headers)
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"HTTP错误 {response.status_code}，跳过此页面")
                break
                
            soup = BeautifulSoup(response.content, "html.parser")
            results_on_page = soup.select("div.SoaBEf")

            if not results_on_page:
                print("未找到新闻结果，可能是HTML结构发生变化或被反爬虫")
                break  # No more results found

            for el in results_on_page:
                try:
                    # 安全获取链接
                    link_element = el.find("a")
                    if not link_element or "href" not in link_element.attrs:
                        continue
                    link = link_element["href"]
                    
                    # 安全获取标题
                    title_element = el.select_one("div.MBeuO")
                    if not title_element:
                        continue
                    title = title_element.get_text()
                    
                    # 安全获取摘要
                    snippet_element = el.select_one(".GI74Re")
                    snippet = snippet_element.get_text() if snippet_element else ""
                    
                    # 安全获取日期
                    date_element = el.select_one(".LfVVr")
                    date = date_element.get_text() if date_element else ""
                    
                    # 安全获取来源
                    source_element = el.select_one(".NUnG9d span")
                    source = source_element.get_text() if source_element else ""
                    
                    news_results.append(
                        {
                            "link": link,
                            "title": title,
                            "snippet": snippet,
                            "date": date,
                            "source": source,
                        }
                    )
                except Exception as e:
                    print(f"Error processing result: {e}")
                    # If one of the fields is not found, skip this result
                    continue

            print(f"成功获取 {len(news_results)} 条新闻（第{page+1}页）")

            # Check for the "Next" link (pagination)
            next_link = soup.find("a", id="pnnext")
            if not next_link:
                break

            page += 1

        except Exception as e:
            print(f"抓取新闻时发生错误: {e}")
            break

    print(f"Google新闻抓取完成，共获取 {len(news_results)} 条新闻")
    return news_results
