"""
Discord Webhook Poster Module
Discord Webhookを使ってニュースを投稿する
"""

from collections import defaultdict
import requests

from config import DISCORD_WEBHOOK_URL
from poem_generator import generate_poem


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
    
    # 1. まずポエムを生成して送信
    poem = generate_poem(articles, is_morning)
    if poem:
        if not _send_message(poem, suppress_embeds=False):
            print("[WARNING] Failed to send poem message.")
    
    # 2. ニュースリンクをソースごとにグループ化して送信
    by_source = defaultdict(list)
    for article in articles:
        by_source[article["source"]].append(article)
    
    # メッセージを分割して送信（2000文字制限対策）
    messages = []
    current_message = ""
    
    for source, source_articles in by_source.items():
        source_block = f"\n📰 **{source}**\n"
        for article in source_articles:
            source_block += f"   • **[{article['title'][:80]}]({article['url']})**\n"
        
        if len(current_message) + len(source_block) > 1900:
            if current_message:
                messages.append(current_message)
            current_message = source_block
        else:
            current_message += source_block
    
    if current_message:
        messages.append(current_message)
    
    # 各メッセージを送信
    success = True
    for message in messages:
        if not _send_message(message):
            success = False
    
    if success:
        print(f"[SUCCESS] Posted {len(articles)} articles to Discord.")
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
