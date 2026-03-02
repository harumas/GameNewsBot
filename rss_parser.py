"""
RSS Feed Parser Module
RSSフィードからニュース記事を取得し、フィルタリングする
"""

import json
import os
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional
import feedparser
import requests

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


def _normalize_title(title: str) -> str:
    """タイトルを正規化して比較しやすくする"""
    t = title.lower()
    # 『』「」【】を除去
    t = re.sub(r'[『』「」【】\[\]()（）]', '', t)
    # 記号・空白を除去
    t = re.sub(r'[\s\u3000・:：,、。.!！?？―─—–\-]+', '', t)
    return t


def _titles_are_similar(title_a: str, title_b: str, threshold: float = 0.65) -> bool:
    """2つのタイトルが類似しているかを判定"""
    norm_a = _normalize_title(title_a)
    norm_b = _normalize_title(title_b)

    # 完全一致
    if norm_a == norm_b:
        return True

    # 短いほうが長いほうに含まれていたら重複
    if len(norm_a) > 5 and len(norm_b) > 5:
        if norm_a in norm_b or norm_b in norm_a:
            return True

    # SequenceMatcherで類似度チェック
    ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    return ratio >= threshold


def _deduplicate_articles(articles: list[dict]) -> list[dict]:
    """
    類似タイトルの記事を重複排除する。
    先に出現した（＝新しい順ソート済みなので新しい）記事を優先。
    """
    unique = []
    for article in articles:
        is_dup = False
        for kept in unique:
            if _titles_are_similar(article["title"], kept["title"]):
                is_dup = True
                break
        if not is_dup:
            unique.append(article)
        else:
            print(f"[DEDUP] 重複を除外: {article['title']}  (← {article['source']})")
    return unique


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


def _clean_image_url(url: str) -> str:
    """画像のURLから縮小版サフィックス（-150x150など）を取り除き、オリジナル高画質版のURLを返す"""
    if not url:
        return url
    # WordPress等の縮小画像パターン（例: -150x150.jpg, -1024x576.png）を削除
    return re.sub(r'-\d+x\d+(?=\.(?:jpg|jpeg|png|webp|gif)$)', '', url, flags=re.IGNORECASE)


def _extract_image(entry) -> Optional[str]:
    """RSSエントリからサムネイル画像URLを抽出する"""
    # 1. media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            url = media.get('url', '')
            media_type = media.get('type', '')
            if url and ('image' in media_type or url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))):
                return _clean_image_url(url)
    
    # 2. media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for thumb in entry.media_thumbnail:
            url = thumb.get('url', '')
            if url:
                return _clean_image_url(url)
    
    # 3. enclosure (image type)
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            url = enc.get('href', enc.get('url', ''))
            enc_type = enc.get('type', '')
            if url and 'image' in enc_type:
                return _clean_image_url(url)
    
    # 4. HTML content 内の <img> タグ
    content_html = ''
    if hasattr(entry, 'content') and entry.content:
        content_html = entry.content[0].get('value', '')
    elif hasattr(entry, 'summary'):
        content_html = entry.summary or ''
    
    if content_html:
        img_match = re.search(r'<img[^>]+src=["\']([^"\'>]+)["\']', content_html)
        if img_match:
            img_url = img_match.group(1)
            # data: URI はスキップ
            if not img_url.startswith('data:'):
                return _clean_image_url(img_url)
    
    return None


def _calculate_importance_score(entry, title: str, source: str) -> int:
    """設定に基づいて記事の注目度（スコア）を計算する"""
    score = 0
    from config import FEATURED_SETTINGS
    
    # 1. タイトルキーワードによる加点
    for kw in FEATURED_SETTINGS.get("high_value_keywords", []):
        if kw.lower() in title.lower():
            score += 2
            
    # 2. タグ/カテゴリによる加点 (Featured, Pickup等)
    if hasattr(entry, 'tags'):
        for tag in entry.tags:
            tag_term = tag.get('term', '').lower()
            if 'feature' in tag_term or 'pickup' in tag_term:
                score += FEATURED_SETTINGS.get("tag_bonus", 3)
                break
                
    # 3. ニュースソースによるベースライン加点
    source_bonus = FEATURED_SETTINGS.get("source_bonus", {})
    if source in source_bonus:
        score += source_bonus[source]
        
    return score


def _fetch_og_image(url: str, timeout: float = 5) -> Optional[str]:
    """記事ページからog:image を取得する（フォールバック用）"""
    try:
        resp = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        if resp.status_code != 200:
            return None
        # og:image メタタグを検索
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\'>]+)["\']',
            resp.text[:10000]  # ヘッダー部分のみ検索
        )
        if not match:
            # content が先に来るパターン
            match = re.search(
                r'<meta[^>]+content=["\']([^"\'>]+)["\'][^>]+property=["\']og:image["\']',
                resp.text[:10000]
            )
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def _fill_missing_images(articles: list[dict]) -> list[dict]:
    """画像がない記事のOGP画像を取得する"""
    missing = [a for a in articles if not a.get('image')]
    if not missing:
        return articles
    
    print(f"[INFO] {len(missing)}件の記事のOGP画像を取得中...")
    filled = 0
    for article in missing:
        img = _fetch_og_image(article['url'])
        if img:
            article['image'] = img
            filled += 1
    
    if filled:
        print(f"[INFO] {filled}件のOGP画像を取得しました")
    return articles


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
            fetch_limit = max_articles * 3  # 重要記事選定のために多めに取得
            
            for entry in feed.entries:
                if count >= fetch_limit:
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
                
                # 日時によるフィルタリング（古い記事を除外）
                if published:
                    max_age_hours = FILTER_SETTINGS.get("max_age_hours", 30)
                    # タイムゾーン情報がある場合は削除して比較（簡易的対応）
                    # published_parsed は通常UTCなので、比較対象もUTCにする
                    published_naive = published.replace(tzinfo=None)
                    time_diff = datetime.utcnow() - published_naive
                    
                    if time_diff.total_seconds() > max_age_hours * 3600:
                        # print(f"[DEBUG] Skipped old article: {title} ({time_diff.total_seconds() / 3600:.1f} hours ago)")
                        continue
                
                # 重要度スコアを計算
                importance_score = _calculate_importance_score(entry, title, feed_config["name"])
                
                all_articles.append({
                    "title": title,
                    "url": url,
                    "source": feed_config["name"],
                    "published": published,
                    "max_articles": max_articles,  # 元の制限数を保存
                    "description": description[:200] if description else "",
                    "image": _extract_image(entry),
                    "importance_score": importance_score,
                })
                
                count += 1
        
        except Exception as e:
            print(f"[ERROR] Error fetching {feed_config['name']}: {e}")
    
    # 公開日時でソート（新しい順）
    all_articles.sort(
        key=lambda x: x["published"] or datetime.min,
        reverse=True
    )

    # 重複記事を排除
    before_count = len(all_articles)
    all_articles = _deduplicate_articles(all_articles)
    dedup_count = before_count - len(all_articles)
    if dedup_count > 0:
        print(f"[INFO] {dedup_count}件の重複記事を除外しました")

    # OGP画像のフォールバック取得
    all_articles = _fill_missing_images(all_articles)

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
