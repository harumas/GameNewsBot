"""
Generate News JSON for Website
RSSから記事を取得し、AI分類後にJSONファイルとして出力する
GitHub Actionsまたはローカルで実行
"""

import json
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from rss_parser import fetch_news, mark_as_posted
from categorizer import categorize_articles
from poem_generator import generate_poem
from collections import defaultdict


def generate_news_json(output_dir: str = None):
    """
    ニュースを取得・分類し、JSONファイルに出力する
    
    Args:
        output_dir: 出力先ディレクトリ（デフォルト: docs/data/）
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "docs", "data")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("[INFO] ニュースを取得中...")
    articles = fetch_news()
    print(f"[INFO] {len(articles)}件の新着記事を取得しました")
    
    if not articles:
        print("[INFO] 新着記事がないため、空のJSONを生成します")
        data = {
            "generated_at": datetime.now().isoformat(),
            "poem": "",
            "articles": [],
        }
    else:
        # AI分類
        print("[INFO] AIで記事を分類中...")
        categorized, excluded = categorize_articles(articles)
        
        if excluded:
            print(f"[INFO] {len(excluded)}件の非ゲーム記事を除外しました")
        
        # サイトごとの件数制限と重要度判定
        by_source = defaultdict(list)
        for article in categorized:
            # スコアに基づいて重要度を判定 (2点以上でhigh扱い)
            score = article.get("importance_score", 0)
            if score >= 2:
                article["importance"] = "high"
                
            by_source[article.get("source", "")].append(article)
        
        final_articles = []
        for source, source_articles in by_source.items():
            # 1. importance_scoreが高い順  2. importanceフラグ  3. 日付順 でソート
            source_articles.sort(
                key=lambda x: (x.get("importance_score", 0), x.get("importance") == "high", x.get("published") or datetime.min),
                reverse=True
            )
            limit = source_articles[0].get("max_articles", 5) if source_articles else 5
            final_articles.extend(source_articles[:limit])
        
        # ポエム生成
        print("[INFO] AIポエムを生成中...")
        current_hour = datetime.now().hour
        is_morning = current_hour < 12
        poem = generate_poem(final_articles, is_morning=is_morning)
        
        # JSONデータを構築
        json_articles = []
        for article in final_articles:
            published = article.get("published")
            json_articles.append({
                "title": article["title"],
                "url": article["url"],
                "source": article.get("source", ""),
                "category": article.get("category", "other"),
                "importance": article.get("importance", "normal"),
                "published": published.isoformat() if published else None,
                "image": article.get("image"),
            })
        
        data = {
            "generated_at": datetime.now().isoformat(),
            "poem": poem,
            "articles": json_articles,
        }
        
        # 投稿済みとしてマークする前にDiscordに通知
        from discord_poster import post_discord_notice
        print("[INFO] Discordへ通知を送信中...")
        post_discord_notice(poem, is_morning, len(final_articles))
        
        # 投稿済みとしてマーク
        mark_as_posted(articles)
    
    # JSONファイルに書き出し
    output_path = os.path.join(output_dir, "news.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[SUCCESS] {len(data['articles'])}件の記事を {output_path} に出力しました")
    return data


if __name__ == "__main__":
    generate_news_json()
