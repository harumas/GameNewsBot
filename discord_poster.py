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


def post_discord_notice(poem: str, is_morning: bool = True, article_count: int = 0) -> bool:
    """
    サマリーとポエムのみをDiscordに投稿（Webサイト連携用）
    """
    if not DISCORD_WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL is not set!")
        return False
        
    if article_count == 0:
        print("[INFO] No articles to post.")
        return True

    # メッセージを構築
    message = ""
    if is_morning:
        message += "🌅 **おはようございます！朝のゲームニュースです**\n\n"
    else:
        message += "🌙 **お疲れ様です！夜のゲームニュースです**\n\n"

    if poem:
        message += f"{poem}\n\n"

    message += "🔽 本日の詳細なゲームニュース一覧は以下のWebサイトからご確認ください！\n"
    message += "🔗 https://harumas.github.io/GameNewsBot/\n"
    
    success = _send_message(message)
    
    if success:
        print(f"[SUCCESS] Posted notice to Discord ({article_count} articles).")
    else:
        print("[ERROR] Failed to send Discord notice.")
        
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
