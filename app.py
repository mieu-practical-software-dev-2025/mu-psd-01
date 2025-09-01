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
ユーザーが指定した食材と、必要なら予算内での追加食材を使い、
栄養バランスの良い夕食の献立を提案してください。

必ず次のJSONフォーマットで返答してください:
{
  "menu_title": "献立タイトル",
  "dishes": [
    {
      "name": "料理名",
      "ingredients": ["食材A", "食材B"],
      "steps": ["手順1", "手順2"],
      "calories": 数値,
      "nutrition": {"たんぱく質": g, "脂質": g, "炭水化物": g}
    }
  ],
  "total_calories": 数値,
  "notes": "補足説明"
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
# POST /generate_menu
# 入力JSON例:
# {
#   "ingredients": ["じゃがいも", "玉ねぎ", "鶏肉"],
#   "budget": 500
# }
# 出力JSON例:
# {
#   "menu_title": "鶏肉と野菜の和定食",
#   "dishes": [
#       {"name": "鶏肉の照り焼き", "ingredients": ["鶏肉","醤油"], "steps":["焼く","味付け"], "calories":320, "nutrition":{"たんぱく質":25,"脂質":15,"炭水化物":12}},
#       {"name": "味噌汁", "ingredients": ["玉ねぎ","味噌"], "steps":["煮る","味噌を溶かす"], "calories":120, "nutrition":{"たんぱく質":3,"脂質":2,"炭水化物":18}}
#   ],
#   "total_calories": 440,
#   "notes": "不足栄養素を補うために小鉢を追加するとさらに良いです。"
# }
# ----------------------------------------
@app.route("/generate_menu", methods=["POST"])
def generate_menu():
    data = request.get_json()

    # --- 入力チェック ---
    if not data or not isinstance(data.get("ingredients"), list) or not data.get("ingredients"):
        return jsonify({"error": "Missing 'ingredients' in request body"}), 400

    ingredients = data["ingredients"]
    budget = data.get("budget")  # 予算は任意

    # --- AIに投げるプロンプト ---
    user_prompt = f"""
    食材: {ingredients}
    追加予算: {budget if budget else "なし"}
    JSON形式で献立を返してください。
    """

    try:
        # --- OpenRouter API呼び出し ---
        # response_formatでJSONモードを有効化
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

        # --- JSONとしてパース ---
        # JSONモードでも稀に失敗する可能性を考慮し、エラーハンドリングは残す
        try:
            menu_data = json.loads(ai_response_text)
        except json.JSONDecodeError:
            return jsonify({"error": "AI response was not valid JSON despite requesting JSON format.", "raw": ai_response_text}), 500

        return jsonify(menu_data)

    except APIStatusError as e:
        # APIからのエラーステータス（認証エラー、リクエストエラーなど）
        return jsonify({"error": f"OpenRouter API error: {e.status_code} {e.response.text}"}), e.status_code
    except APIConnectionError as e:
        # ネットワーク関連のエラー
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