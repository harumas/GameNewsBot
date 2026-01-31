"""
Discord News Bot - 設定ファイル
RSSフィードやフィルタリング設定をカスタマイズできます
"""

import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Discord設定
# =============================================================================
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# =============================================================================
# Gemini API設定（ポエム生成用 - 現在未使用）
# =============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# =============================================================================
# Groq API設定（ポエム生成用）
# =============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# 投稿スケジュール（24時間形式）
MORNING_POST_TIME = os.getenv("MORNING_POST_TIME", "08:00")
EVENING_POST_TIME = os.getenv("EVENING_POST_TIME", "20:00")

# =============================================================================
# RSSフィード設定
# enabled: False にするとそのフィードを無効化
# max_articles: 1回の投稿で取得する最大記事数
# =============================================================================
RSS_FEEDS = [
    {
        "name": "4Gamer.net",
        "url": "https://www.4gamer.net/rss/index.xml",
        "max_articles": 5,
        "enabled": True,
    },
    {
        "name": "ファミ通.com",
        "url": "https://www.famitsu.com/feed/",
        "max_articles": 3,
        "enabled": False,  # RSSフィードが現在利用不可
    },
    {
        "name": "IGN Japan",
        "url": "https://jp.ign.com/feed.xml",
        "max_articles": 5,
        "enabled": True,
    },
    {
        "name": "Automaton",
        "url": "https://automaton-media.com/feed/",
        "max_articles": 5,
        "enabled": True,
    },
    {
        "name": "ゲームメーカーズ",
        "url": "https://gamemakers.jp/feed/",
        "max_articles": 5,
        "enabled": True,
    },
    {
        "name": "電ファミニコゲーマー",
        "url": "https://news.denfaminicogamer.jp/feed",
        "max_articles": 5,
        "enabled": True,
    },
    # ===== 技術・CG系 =====
    {
        "name": "Unity Japan",
        "url": "https://blog.unity.com/ja/feed",
        "max_articles": 5,
        "enabled": True,
    },
    {
        "name": "CGWORLD",
        "url": "https://cgworld.jp/atom.xml",
        "max_articles": 5,
        "enabled": True,
    },
    # ===== ビジネス系 =====
    {
        "name": "GameBusiness.jp",
        "url": "https://www.gamebusiness.jp/rss/index.rdf",
        "max_articles": 5,
        "enabled": True,
    },
    # ===== 英語サイト（無効化中） =====
    {
        "name": "80.lv",
        "url": "https://80.lv/feed/",
        "max_articles": 3,
        "enabled": False,  # 英語サイト
    },
    {
        "name": "Game Developer",
        "url": "https://www.gamedeveloper.com/rss.xml",
        "max_articles": 3,
        "enabled": False,  # 英語サイト
    },
]

# =============================================================================
# フィルタリング設定
# =============================================================================
FILTER_SETTINGS = {
    # これらのキーワードを含む記事のみ取得（空リストなら全て取得）
    "keywords_include": [],
    
    # これらのキーワードを含む記事を除外
    "keywords_exclude": ["PR", "広告", "Sponsored"],
    
    # 重複記事を何日間記憶するか
    "duplicate_memory_days": 7,
}

# =============================================================================
# 表示設定
# =============================================================================
DISPLAY_SETTINGS = {
    # Embedの色（16進数）
    "embed_color": 0x7289DA,  # Discord Blurple
    
    # 投稿時のタイトル
    "morning_title": "🌅 おはようございます！朝のゲームニュース",
    "evening_title": "🌙 お疲れ様です！夜のゲームニュース",
    
    # フッターテキスト
    "footer_text": "Game News Bot",
}
