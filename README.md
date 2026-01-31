# Discord Game News Bot

ゲーム業界のニュースをRSSフィードから収集し、Discordチャンネルに自動配信するBotです。

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーして、Webhook URLを設定:

```bash
cp .env.example .env
```

`.env` ファイルを編集:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/あなたのWebhook URL
MORNING_POST_TIME=08:00
EVENING_POST_TIME=20:00
```

## 使い方

### スケジューラーを起動（通常モード）

```bash
python main.py
```

朝8時と夜20時に自動でニュースを配信します。

### テストコマンド

```bash
# Webhookが正しく設定されているかテスト
python main.py --test-webhook

# ニュースを取得して表示（投稿しない）
python main.py --fetch-only

# 今すぐニュースを投稿
python main.py --test
```

## カスタマイズ

`config.py` を編集してカスタマイズできます:

### RSSフィードの追加・削除

```python
RSS_FEEDS = [
    {
        "name": "サイト名",
        "url": "https://example.com/rss/",
        "max_articles": 3,  # 取得する最大記事数
        "enabled": True,    # False で無効化
    },
    # ...
]
```

### フィルタリング設定

```python
FILTER_SETTINGS = {
    # これらを含む記事のみ取得（空なら全て）
    "keywords_include": ["PS5", "Nintendo"],
    
    # これらを含む記事を除外
    "keywords_exclude": ["PR", "広告"],
}
```

## ファイル構成

```
NewsBot/
├── main.py           # メインスクリプト
├── config.py         # 設定ファイル
├── rss_parser.py     # RSSフィード取得
├── discord_poster.py # Discord投稿
├── requirements.txt  # 依存パッケージ
├── .env.example      # 環境変数サンプル
├── .env              # 環境変数（要作成）
└── data/
    └── posted_articles.json  # 投稿済み記事
```
