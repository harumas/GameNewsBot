"""
Discord Game News Bot - Main Entry Point
ゲーム業界のニュースを収集してDiscordチャンネルに配信
"""

import argparse
import sys
import time
from datetime import datetime

import schedule

from config import MORNING_POST_TIME, EVENING_POST_TIME
from generate_news_json import generate_news_json
from discord_poster import post_test_message
from rss_parser import fetch_news

def run_news_job(is_morning: bool = True):
    """ニュース取得・JSON生成・Discord通知の一連のジョブを実行"""
    time_label = "朝" if is_morning else "夜"
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {time_label}のニュース配信を開始")
    print(f"{'='*50}")
    
    # サイト生成とDiscord投稿を同時に実行するUnified Pipelineを呼び出す
    try:
        generate_news_json()
    except Exception as e:
        print(f"[ERROR] ジョブ実行中にエラーが発生しました: {e}")


def morning_job():
    """朝のニュース配信"""
    run_news_job(is_morning=True)


def evening_job():
    """夜のニュース配信"""
    run_news_job(is_morning=False)


def setup_schedule():
    """スケジュールを設定"""
    schedule.every().day.at(MORNING_POST_TIME).do(morning_job)
    # schedule.every().day.at(EVENING_POST_TIME).do(evening_job)
    
    print(f"[INFO] スケジュール設定完了:")
    print(f"  - 朝のニュース: {MORNING_POST_TIME}")


def main():
    parser = argparse.ArgumentParser(
        description="Discord Game News Bot - ゲームニュース配信Bot"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード: すぐにニュースを投稿して終了"
    )
    parser.add_argument(
        "--test-webhook",
        action="store_true",
        help="Webhookテスト: テストメッセージを送信"
    )
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="取得のみ: ニュースを取得して表示（投稿しない）"
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="即時投稿: ニュースを取得して投稿（GitHub Actions用）"
    )
    
    args = parser.parse_args()
    
    print("="*50)
    print("🎮 Discord Game News Bot")
    print("="*50)
    
    if args.test_webhook:
        print("\n[MODE] Webhookテスト")
        success = post_test_message()
        sys.exit(0 if success else 1)
    
    if args.fetch_only:
        print("\n[MODE] ニュース取得テスト（投稿なし）")
        articles = fetch_news()
        print(f"\n📰 {len(articles)}件の新着記事:\n")
        for i, article in enumerate(articles, 1):
            published = ""
            if article.get("published"):
                published = article["published"].strftime("%m/%d %H:%M")
            print(f"{i}. [{article['source']}] {article['title']}")
            print(f"   {article['url']}")
            if published:
                print(f"   📅 {published}")
            print()
        sys.exit(0)
    
    if args.post:
        print("\n[MODE] 即時投稿（GitHub Actions）")
        # 時間帯によって朝/夜を判定
        current_hour = datetime.now().hour
        is_morning = current_hour < 12
        run_news_job(is_morning=is_morning)
        sys.exit(0)
    
    if args.test:
        print("\n[MODE] テスト投稿")
        run_news_job(is_morning=True)
        sys.exit(0)
    
    # 通常モード: スケジューラーを起動
    print("\n[MODE] スケジューラー起動")
    setup_schedule()
    print("\n[INFO] Botを起動しました。Ctrl+C で終了。")
    print("[INFO] 次の実行を待機中...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    except KeyboardInterrupt:
        print("\n[INFO] Botを終了します。")
        sys.exit(0)


if __name__ == "__main__":
    main()
