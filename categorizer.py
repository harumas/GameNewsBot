"""
AI Categorizer Module
Groq APIを使ってニュース記事をカテゴリ分類し、ゲーム業界に関係ない記事を除外する
"""

import json
import requests
from config import GROQ_API_KEY


# カテゴリ定義
CATEGORIES = {
    "release": "🎮 新作・リリース",
    "sale": "💰 セール・キャンペーン",
    "update": "🔧 アップデート・DLC",
    "industry": "📢 業界ニュース",
    "esports": "🏆 eスポーツ・配信",
    "other": "📰 その他",
}


def categorize_articles(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    記事をカテゴリ分類し、ゲーム業界に関係ない記事を除外する
    
    Args:
        articles: ニュース記事のリスト
    
    Returns:
        tuple: (カテゴリ分類された記事リスト, 除外された記事リスト)
    """
    if not GROQ_API_KEY:
        print("[WARNING] GROQ_API_KEY is not set. Skipping categorization.")
        for article in articles:
            article["category"] = "other"
        return articles, []
    
    if not articles:
        return [], []
    
    # 記事タイトルのリストを作成
    titles_with_index = [
        f"{i}. {article['title']}"
        for i, article in enumerate(articles)
    ]
    titles_text = "\n".join(titles_with_index)
    
    prompt = f"""以下のニュース記事タイトルを分析して、各記事を分類してください。

# 記事タイトル
{titles_text}

# 分類カテゴリ
- release: ゲームの新作発表、発売日、リリース情報
- sale: ゲームのセール、割引、無料配布
- update: ゲームのアップデート、パッチ、DLC
- industry: ゲーム会社の動向、買収、ゲームイベント
- esports: ゲームのeスポーツ、大会、ゲーム配信者
- other: 上記に当てはまらないがゲーム関連のニュース
- exclude: ゲームに関係ない記事

# excludeの例（これらは必ずexcludeにする）
- 漫画・コミックのセールや連載情報（Kindleセールを含む）
- アニメの放送・配信・円盤情報
- 小説・ライトノベルの発売
- 電子書籍のセール（ゲーム攻略本以外）
- 映画・ドラマの情報
- 音楽・アーティストの情報

# 出力形式
JSON配列で出力。例: [{{"id": 0, "category": "release"}}, {{"id": 1, "category": "exclude"}}]
JSON配列のみを出力し、他の説明は不要です。"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            result_text = data["choices"][0]["message"]["content"].strip()
            
            # JSONをパース（マークダウンコードブロックを除去）
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            categories_result = json.loads(result_text)
            
            # 結果を記事に適用
            categorized = []
            excluded = []
            
            for item in categories_result:
                idx = item["id"]
                category = item["category"]
                
                if idx < len(articles):
                    article = articles[idx].copy()
                    
                    if category == "exclude":
                        excluded.append(article)
                    else:
                        article["category"] = category if category in CATEGORIES else "other"
                        categorized.append(article)
            
            print(f"[SUCCESS] Categorized {len(categorized)} articles, excluded {len(excluded)}.")
            return categorized, excluded
        
        else:
            print(f"[WARNING] Groq API error: {response.status_code}. Skipping categorization.")
            for article in articles:
                article["category"] = "other"
            return articles, []
    
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Categorization failed: {e}")
        for article in articles:
            article["category"] = "other"
        return articles, []


def get_category_label(category: str) -> str:
    """カテゴリコードからラベルを取得"""
    return CATEGORIES.get(category, CATEGORIES["other"])


if __name__ == "__main__":
    # テスト用
    test_articles = [
        {"title": "『FF7 リバース』PC版が2月発売決定"},
        {"title": "Steam週末セール開催中、人気タイトルが最大80%オフ"},
        {"title": "『そらのおとしもの』が1冊99円で買えるセールがKindleで開催中"},
        {"title": "人気漫画『チェンソーマン』新章連載開始"},
        {"title": "『Apex Legends』シーズン20アップデート配信"},
    ]
    
    categorized, excluded = categorize_articles(test_articles)
    
    print("\n=== カテゴリ分類結果 ===")
    for article in categorized:
        label = get_category_label(article["category"])
        print(f"{label}: {article['title']}")
    
    print("\n=== 除外された記事 ===")
    for article in excluded:
        print(f"❌ {article['title']}")
