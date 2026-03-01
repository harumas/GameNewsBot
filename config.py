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
MORNING_POST_TIME = os.getenv("MORNING_POST_TIME", "09:00")
EVENING_POST_TIME = os.getenv("EVENING_POST_TIME", "20:00")  # 現在はmain.pyで無効化されています

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

    # 記事の最大経過時間（時間単位） - これより古い記事は除外
    # 毎日配信なら24時間 + マージンで30時間程度が目安
    "max_age_hours": 48,
}

# =============================================================================
# 注目記事（Featured）判定設定
# スコアが高い記事が優先的に表示（最大3件の中）に残ります
# =============================================================================
FEATURED_SETTINGS = {
    # タイトルに含まれるとスコアが加算されるキーワード（各+2点）
    "high_value_keywords": [
        "発表", "発売決定", "大ヒット", "売上", "ミリオン", 
        "世界初", "インタビュー", "レビュー", "プレイレポート", 
        "無料配布", "アップデート", "映像公開"
    ],
    # 元サイト側で「Featured」等のタグがついている場合の加算点（+3点）
    "tag_bonus": 3,
    # 特定のサイトからのニュースを少し優先度のベースラインを上げる（各+1点）
    # 例：公式情報や超大手メディア
    "source_bonus": {
        "Unity Japan": 1,
        "4Gamer.net": 1,
        "ファミ通.com": 1
    }
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
