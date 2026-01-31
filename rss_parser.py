"""
RSS Feed Parser Module
RSSフィードからニュース記事を取得し、フィルタリングする
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
import feedparser

from config import RSS_FEEDS, FILTER_SETTINGS


# 投稿済み記事を保存するファイルパス
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
POSTED_ARTICLES_FILE = os.path.join(DATA_DIR, "posted_articles.json")


def _ensure_data_dir():
    """データディレクトリが存在しない場合は作成"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _load_posted_articles() -> dict:
    """投稿済み記事のURLと日時を読み込む"""
    _ensure_data_dir()
    if os.path.exists(POSTED_ARTICLES_FILE):
        try:
            with open(POSTED_ARTICLES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_posted_articles(articles: dict):
    """投稿済み記事を保存"""
    _ensure_data_dir()
    with open(POSTED_ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def _cleanup_old_articles(articles: dict) -> dict:
    """古い記事を削除（メモリ節約）"""
    memory_days = FILTER_SETTINGS.get("duplicate_memory_days", 7)
    cutoff_date = datetime.now() - timedelta(days=memory_days)
    cutoff_str = cutoff_date.isoformat()
    
    return {
        url: date for url, date in articles.items()
        if date > cutoff_str
    }


def _matches_filter(title: str, description: str = "") -> bool:
    """フィルタリング条件に一致するかチェック"""
    text = f"{title} {description}".lower()
    
    # 除外キーワードチェック
    exclude_keywords = FILTER_SETTINGS.get("keywords_exclude", [])
    for keyword in exclude_keywords:
        if keyword.lower() in text:
            return False
    
    # 複合パターンによる除外（漫画・小説のリリース情報など）
    # これらのパターンはゲームタイトルには通常含まれない
    exclude_patterns = [
        # 漫画・コミック関連
        ("漫画", "連載"),
        ("マンガ", "連載"),
        ("コミック", "発売"),
        ("コミック", "刊行"),
        ("コミカライズ", ""),
        # 小説・ライトノベル関連
        ("小説", "発売"),
        ("小説", "刊行"),
        ("ライトノベル", "発売"),
        ("ノベライズ", ""),
        # 書籍関連
        ("書籍", "発売"),
        ("単行本", "発売"),
        ("文庫", "発売"),
    ]
    
    for pattern in exclude_patterns:
        keyword1, keyword2 = pattern
        if keyword1.lower() in text:
            # keyword2が空ならkeyword1だけでマッチ
            if not keyword2 or keyword2.lower() in text:
                return False
    
    # 必須キーワードチェック（空なら全て許可）
    include_keywords = FILTER_SETTINGS.get("keywords_include", [])
    if include_keywords:
        return any(keyword.lower() in text for keyword in include_keywords)
    
    return True


def _parse_published_date(entry) -> Optional[datetime]:
    """記事の公開日時をパース"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6])
        except (TypeError, ValueError):
            pass
    return None


def fetch_news() -> list[dict]:
    """
    全ての有効なRSSフィードからニュースを取得
    
    Returns:
        list[dict]: ニュース記事のリスト
            - title: 記事タイトル
            - url: 記事URL
            - source: ソースサイト名
            - published: 公開日時（datetime or None）
            - description: 記事の説明（あれば）
    """
    posted_articles = _load_posted_articles()
    posted_articles = _cleanup_old_articles(posted_articles)
    
    all_articles = []
    
    for feed_config in RSS_FEEDS:
        if not feed_config.get("enabled", True):
            continue
        
        try:
            feed = feedparser.parse(feed_config["url"])
            
            if feed.bozo and not feed.entries:
                print(f"[WARNING] Failed to parse feed: {feed_config['name']}")
                continue
            
            count = 0
            max_articles = feed_config.get("max_articles", 5)
            
            for entry in feed.entries:
                if count >= max_articles:
                    break
                
                url = entry.get("link", "")
                title = entry.get("title", "No Title")
                description = entry.get("summary", entry.get("description", ""))
                
                # 既に投稿済みの記事はスキップ
                if url in posted_articles:
                    continue
                
                # フィルタリング
                if not _matches_filter(title, description):
                    continue
                
                published = _parse_published_date(entry)
                
                all_articles.append({
                    "title": title,
                    "url": url,
                    "source": feed_config["name"],
                    "published": published,
                    "description": description[:200] if description else "",
                })
                
                count += 1
        
        except Exception as e:
            print(f"[ERROR] Error fetching {feed_config['name']}: {e}")
    
    # 公開日時でソート（新しい順）
    all_articles.sort(
        key=lambda x: x["published"] or datetime.min,
        reverse=True
    )
    
    return all_articles


def mark_as_posted(articles: list[dict]):
    """記事を投稿済みとしてマーク"""
    posted_articles = _load_posted_articles()
    posted_articles = _cleanup_old_articles(posted_articles)
    
    now = datetime.now().isoformat()
    for article in articles:
        posted_articles[article["url"]] = now
    
    _save_posted_articles(posted_articles)


if __name__ == "__main__":
    # テスト用
    print("Fetching news...")
    news = fetch_news()
    print(f"Found {len(news)} new articles:")
    for article in news[:5]:
        print(f"  - [{article['source']}] {article['title']}")
