"""
Poem Generator Module
Groq APIを使ってゲーム業界の動向ポエムを生成する
"""

import requests
from config import GROQ_API_KEY


def generate_poem(articles: list[dict], is_morning: bool = True) -> str:
    """
    記事の内容からゲーム業界の動向ポエムを生成
    
    Args:
        articles: ニュース記事のリスト
        is_morning: 朝の投稿かどうか
    
    Returns:
        str: 生成されたポエム（失敗時は空文字）
    """
    if not GROQ_API_KEY:
        print("[WARNING] GROQ_API_KEY is not set. Skipping poem generation.")
        return ""
    
    # 記事タイトルからコンテキストを作成
    titles = [article["title"] for article in articles[:15]]
    titles_text = "\n".join(f"- {title}" for title in titles)
    
    time_greeting = "おはようございます" if is_morning else "お疲れ様です"
    
    prompt = f"""あなたはゲーム業界に詳しいフレンドリーなニュースキャスターです。
以下の今日のゲームニュースの見出しを見て、短い挨拶とゲーム業界の動向をまとめた「ポエム風」のコメントを書いてください。

# 今日のニュース見出し
{titles_text}

# ルール
- 「{time_greeting}！」から始めてください
- 2〜3行で簡潔にまとめる
- 絵文字を1〜2個使う
- ポジティブなトーンで
- 特に注目のニュースがあれば軽く触れる
- 最後は「それでは今日のニュースをどうぞ！」で締める"""

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
                "temperature": 0.8,
                "max_tokens": 300,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            print("[SUCCESS] Poem generated successfully.")
            return text.strip()
        elif response.status_code == 429:
            print("[WARNING] Groq API rate limited. Skipping poem.")
            return ""
        else:
            print(f"[WARNING] Groq API error: {response.status_code}. Skipping poem.")
            return ""
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error during poem generation: {e}")
        return ""
    except (KeyError, IndexError) as e:
        print(f"[ERROR] Failed to parse Groq response: {e}")
        return ""


if __name__ == "__main__":
    # テスト用
    test_articles = [
        {"title": "『FF7 リバース』PC版が発表"},
        {"title": "Nintendo Switch 2の詳細が判明"},
        {"title": "Steam新作セールが開始"},
    ]
    poem = generate_poem(test_articles, is_morning=True)
    print(f"\n生成されたポエム:\n{poem}")
