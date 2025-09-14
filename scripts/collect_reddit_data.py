#!/usr/bin/env python3
"""
Reddit数据收集脚本
使用环境变量中配置的Reddit API凭据收集数据
"""

import os
import json
import praw
from datetime import datetime, timedelta
import time
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class RedditDataCollector:
    def __init__(self):
        """初始化Reddit API客户端"""
        # 从环境变量读取配置
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'TradingAgents:v1.0.0')
        
        if not client_id or not client_secret:
            raise ValueError("请确保已设置 REDDIT_CLIENT_ID 和 REDDIT_CLIENT_SECRET 环境变量")
        
        print(f"初始化Reddit客户端...")
        print(f"Client ID: {client_id}")
        print(f"User Agent: {user_agent}")
        
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # 确保只读模式
        self.reddit.read_only = True
        
        # 验证连接
        try:
            print("✅ Reddit API连接成功!")
        except Exception as e:
            print(f"❌ Reddit API连接失败: {e}")
            raise

    def collect_subreddit_posts(self, subreddit_name: str, limit: int = 50, 
                              time_filter: str = 'week') -> List[Dict]:
        """收集指定subreddit的帖子"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            print(f"📰 正在收集 r/{subreddit_name} 的帖子...")
            
            for submission in subreddit.top(time_filter=time_filter, limit=limit):
                post_data = {
                    'created_utc': int(submission.created_utc),
                    'title': submission.title,
                    'selftext': submission.selftext,
                    'url': submission.url,
                    'ups': submission.ups,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'id': submission.id,
                    'subreddit': str(submission.subreddit)
                }
                posts.append(post_data)
                
                # 遵守API限制：每秒最多1个请求
                time.sleep(1)
            
            print(f"✅ 收集完成：{len(posts)} 个帖子")
            return posts
            
        except Exception as e:
            print(f"❌ 收集 r/{subreddit_name} 时出错: {e}")
            return []

    def save_to_jsonl(self, posts: List[Dict], filepath: str):
        """保存帖子数据为.jsonl格式"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for post in posts:
                f.write(json.dumps(post, ensure_ascii=False) + '\n')
        
        print(f"💾 数据已保存到: {filepath}")

def main():
    """主函数：收集Reddit数据"""
    try:
        collector = RedditDataCollector()
        
        # 全球新闻subreddits（用于新闻分析师）
        print("\n🌍 开始收集全球新闻数据...")
        global_news_subreddits = ['worldnews', 'economics', 'business']
        
        for subreddit in global_news_subreddits:
            posts = collector.collect_subreddit_posts(subreddit, limit=30, time_filter='week')
            if posts:
                filepath = f'data/reddit_data/global_news/{subreddit}.jsonl'
                collector.save_to_jsonl(posts, filepath)
        
        # 股票相关subreddits（用于社交媒体分析师）  
        print("\n📈 开始收集股票新闻数据...")
        stock_subreddits = ['stocks', 'investing', 'SecurityAnalysis']
        
        for subreddit in stock_subreddits:
            posts = collector.collect_subreddit_posts(subreddit, limit=30, time_filter='week')
            if posts:
                filepath = f'data/reddit_data/company_news/{subreddit}.jsonl'
                collector.save_to_jsonl(posts, filepath)
        
        print("\n🎉 Reddit数据收集完成！")
        print("现在可以在TradingAgents中使用Reddit工具了。")
        
    except Exception as e:
        print(f"\n❌ 收集过程出错: {e}")
        print("请检查网络连接和API配置。")

if __name__ == "__main__":
    main()
