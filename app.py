import os
import json
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI, APIStatusError, APIConnectionError
from dotenv import load_dotenv

# ----------------------------------------
# .envから環境変数を読み込む
# ----------------------------------------
load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

# ----------------------------------------
# OpenRouter APIキーの取得
# ----------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SITE_URL = os.getenv("YOUR_SITE_URL", "http://localhost:5000")
APP_NAME = os.getenv("YOUR_APP_NAME", "MenuAdvisor")
CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-4o-mini")

# ----------------------------------------
# OpenAIクライアント（OpenRouter経由）
# ----------------------------------------
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": SITE_URL,
        "X-Title": APP_NAME,
    }
)

# ----------------------------------------
# プロンプト定義
# ----------------------------------------
SYSTEM_PROMPT = """
あなたは栄養士兼料理研究家のAIアシスタントです。

ユーザーが指定した食材と嗜好条件から、以下の2種類の献立を提案してください:

1. 今ある食材だけで作る献立 (plan_without_budget)
2. 予算が指定されている場合、追加食材を考慮した献立 (plan_with_budget)
   - 栄養や彩りを改善するために新しい食材を提案すること
   - ただし予算内で有効な提案が難しい場合は「予算内で追加できる献立はありません」とすること

必ず次のJSONフォーマットで返答してください:
{
  "menu_title": "献立タイトル",
  "plan_without_budget": {
    "dishes": [
      {
        "name": "料理名",
        "ingredients": [...],
        "steps": [...],
        "calories": 数値,
        "nutrition": {"たんぱく質": g, "脂質": g, "炭水化物": g}
      }
    ],
    "total_calories": 数値,
    "notes": "補足説明"
  },
  "plan_with_budget": {
    "dishes": [... または空配列 ...],
    "total_calories": 数値 または 0,
    "notes": "補足説明 または '予算内で追加できる献立はありません。'"
  }
}
"""

# ----------------------------------------
# ルート
# Vue.jsのindex.htmlを返す
# ----------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# ----------------------------------------
# メインAPI: 献立生成
# ----------------------------------------
@app.route("/generate_menu", methods=["POST"])
def generate_menu():
    data = request.get_json()

    if not data or not isinstance(data.get("ingredients"), list) or not data.get("ingredients"):
        return jsonify({"error": "Missing 'ingredients' in request body"}), 400

    ingredients = data["ingredients"]
    budget = data.get("budget")
    preference = data.get("preference")

    # --- AIに投げるプロンプト ---
    user_prompt = f"""
    食材: {ingredients}
    追加予算: {budget if budget else "なし"}
    ユーザーの嗜好・条件: {preference if preference else "特になし"}
    JSON形式で献立を返してください。
    """

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        ai_response_text = response.choices[0].message.content

        try:
            menu_data = json.loads(ai_response_text)
        except json.JSONDecodeError:
            return jsonify({
                "error": "AI response was not valid JSON despite requesting JSON format.",
                "raw": ai_response_text
            }), 500

        return jsonify(menu_data)

    except APIStatusError as e:
        return jsonify({"error": f"OpenRouter API error: {e.status_code} {e.response.text}"}), e.status_code
    except APIConnectionError as e:
        return jsonify({"error": f"Failed to connect to OpenRouter API: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": f"API call failed: {str(e)}"}), 500

# ----------------------------------------
# サーバ起動
# ----------------------------------------
if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("⚠️ 警告: OPENROUTER_API_KEY が設定されていません。API呼び出しは失敗します。")
    app.run(debug=True, host="0.0.0.0", port=5000)