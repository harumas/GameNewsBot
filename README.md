# Discord Game News Bot 🎮

AIを活用してゲーム業界のニュースを収集・分類し、Discordチャンネルに自動配信する高機能Botです。

## 特徴 ✨

- **AIによる自動分類**: 記事内容をAIが分析し、「新作」「セール」「技術」「ビジネス」などのカテゴリに自動分類
- **非ゲーム情報の除外**: ゲームに関係のない漫画セールやアニメ情報などをAIが自動でフィルタリング
- **AIポエム**: その日のニュースを要約したポエムをLlama 3が生成して投稿
- **マルチソース対応**: 4Gamer, Automaton, Unity Japan, CGWORLD, GameBusinessなど主要サイトをカバー
- **見やすいフォーマット**: DiscordのEmbedとMarkdownを活用した視認性の高いレイアウト

## セットアップ 🛠️

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーして設定を行います:

```bash
cp .env.example .env
```

`.env` ファイルを編集して、Discord Webhook URLとGroq APIキー（AI機能用）を設定してください:

```ini
# Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url

# Groq API Key (https://console.groq.com/keys で取得)
GROQ_API_KEY=gsk_...

# 投稿スケジュール
MORNING_POST_TIME=09:00
# EVENING_POST_TIME=20:00 (現在は使用していません)
```

> [!NOTE]
> `GROQ_API_KEY` が設定されていない場合、AI機能（ポエム・詳細分類）はスキップされ、簡易モードで動作します。

## 使い方 🚀

### スケジューラーを起動（常駐モード）

```bash
python main.py
```

指定した時間（デフォルト: 09:00）に自動でニュースを配信します。

### テストコマンド

```bash
# 今すぐニュースを取得して投稿（設定確認用）
python main.py --test

# ニュースを取得して表示するだけ（投稿なし）
python main.py --fetch-only

# Webhookの導通テスト
python main.py --test-webhook
```

## 自動分類カテゴリ 📂

AIが以下のカテゴリに記事を分類します：

- 🎮　**新作・リリース** (Release)
- 💰　**セール・キャンペーン** (Sale)
- 🔧　**アップデート・DLC** (Update)
- ⚙️　**技術・開発** (Tech/Dev)
- 🎨　**CG・アート** (CG/Art)
- 💼　**ビジネス** (Business)
- 📢　**業界ニュース** (Industry)
- 🏆　**eスポーツ・配信** (eSports)
- 📰　**その他** (Other)

## カスタマイズ ⚙️

`config.py` を編集してフィードや挙動をカスタマイズできます。

```python
RSS_FEEDS = [
    {
        "name": "サイト名",
        "url": "https://example.com/rss/",
        "max_articles": 5,  # 1回の投稿で取得する最大記事数
        "enabled": True,
    },
    # ...
]
```

## ファイル構成 📁

```
NewsBot/
├── main.py           # メインスクリプト（スケジューラー）
├── config.py         # 設定管理
├── rss_parser.py     # RSS取得・正規化
├── discord_poster.py # Discord投稿・フォーマット作成
├── categorizer.py    # AIカテゴリ分類・フィルタリング
├── poem_generator.py # AIポエム生成
├── requirements.txt  # 依存ライブラリ
└── data/
    └── posted_articles.json  # 投稿済み記事管理（重複防止）
```
