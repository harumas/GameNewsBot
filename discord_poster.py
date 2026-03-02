"""
Discord Webhook Poster Module
Discord Webhookを使ってニュースを投稿する
"""

from collections import defaultdict
import requests

from config import DISCORD_WEBHOOK_URL
from poem_generator import generate_poem
from categorizer import categorize_articles, get_category_label, CATEGORIES


def _send_message(content: str, suppress_embeds: bool = True) -> bool:
    """単一メッセージを送信"""
    payload = {"content": content}
    if suppress_embeds:
        payload["flags"] = 4  # SUPPRESS_EMBEDS
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=30
        )
        return response.status_code == 204
    except requests.exceptions.RequestException:
        return False


def post_news(articles: list[dict], is_morning: bool = True) -> bool:
    """
    ニュース記事をDiscordに投稿
    
    Args:
        articles: 投稿する記事リスト
        is_morning: 朝の投稿かどうか
    
    Returns:
        bool: 投稿成功したかどうか
    """
    if not DISCORD_WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL is not set!")
        return False
    
    if not articles:
        print("[INFO] No articles to post.")
        return True
    
    # 1. AIでカテゴリ分類（ゲームに関係ない記事を除外）
    categorized_articles, excluded = categorize_articles(articles)
    
    if excluded:
        print(f"[INFO] Excluded {len(excluded)} non-game articles.")
    
    if not categorized_articles:
        print("[INFO] No game-related articles to post after filtering.")
        return True
        
    # 2. 重要度でソートし、サイトごとの件数制限を適用
    # まずサイトごとにグループ化
    by_source = defaultdict(list)
    for article in categorized_articles:
        source_name = article.get("source", "")
        by_source[source_name].append(article)
    
    final_articles = []
    from datetime import datetime # 日付ソート用
    
    for source, source_articles in by_source.items():
        # 重要度（high > normal）と日付（新しい順）でソート
        # importanceが入っていない場合はnormal扱い
        source_articles.sort(
            key=lambda x: (x.get("importance") == "high", x.get("published") or datetime.min),
            reverse=True
        )
        
        # サイトごとの上限（デフォルト5）
        limit = 5
        if source_articles:
            limit = source_articles[0].get("max_articles", 5)
        
        final_articles.extend(source_articles[:limit])
    
    # フィルタリング後の記事リストを使用
    categorized_articles = final_articles

    # 3. ポエムを生成（送信は後でまとめて行う）
    poem = generate_poem(categorized_articles, is_morning)
    
    # 4. メッセージを構築
    message = ""
    if is_morning:
        message += "🌅 **おはようございます！朝のゲームニュースです**\n\n"
    else:
        message += "🌙 **お疲れ様です！夜のゲームニュースです**\n\n"

    if poem:
        message += f"{poem}\n\n"

    message += "🔽 本日の詳細なゲームニュース一覧は以下のWebサイトからご確認ください！\n"
    message += "🔗 https://harumas.github.io/GameNewsBot/\n"
    
    messages = [message]
    
    # 各メッセージを送信
    success = True
    for i, message in enumerate(messages):
        # デバッグ: メッセージサイズ確認
        # print(f"[DEBUG] Sending message {i+1}/{len(messages)} (len: {len(message)})")
        if not _send_message(message):
            print(f"[ERROR] Failed to send message part {i+1}")
            success = False
    
    if success:
        print(f"[SUCCESS] Posted {len(categorized_articles)} articles to Discord.")
    return success


def post_test_message() -> bool:
    """テストメッセージを投稿"""
    if not DISCORD_WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL is not set in .env file!")
        return False
    
    payload = {
        "content": "🤖 **Game News Bot テスト投稿**\nBotが正常に動作しています！"
    }
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 204:
            print("[SUCCESS] Test message posted successfully!")
            return True
        else:
            print(f"[ERROR] Failed to post: {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error: {e}")
        return False


if __name__ == "__main__":
    print("Posting test message...")
    post_test_message()
