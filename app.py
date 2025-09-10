# このファイルは、献立生成アプリケーションのバックエンド（サーバーサイド）のロジックを定義します。
# Flaskフレームワークを使用し、フロントエンドからのリクエストを受け付け、
# OpenRouter経由でAIモデルに問い合わせ、結果を返します。
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI, APIStatusError, APIConnectionError
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT

# --- 1. 初期設定 ---

# .envファイルから環境変数を読み込む
load_dotenv()

# Flaskアプリケーションのインスタンスを作成
# static_folder="static": 'static'ディレクトリを静的ファイル（HTML, JS, CSS）の置き場所として指定
# static_url_path="": URLのルートパス（例: /index.html）で静的ファイルにアクセスできるようにする
app = Flask(__name__, static_folder="static", static_url_path="")

# 環境変数から設定値を取得。見つからない場合はデフォルト値を使用。
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SITE_URL = os.getenv("YOUR_SITE_URL", "http://localhost:5000")
APP_NAME = os.getenv("YOUR_APP_NAME", "MenuAdvisor")
CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-4o-mini")

# --- 2. 外部サービスクライアントの初期化 ---

# OpenAIライブラリを使用してOpenRouter APIに接続するためのクライアントを作成
# base_url: 通信先をOpenAIではなくOpenRouterに指定
# api_key: 認証に使用するAPIキー
# default_headers: OpenRouterが推奨するリクエストヘッダー。利用状況の追跡などに使われる。
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": SITE_URL,
        "X-Title": APP_NAME,
    }
)

# --- 3. ルーティング定義 ---

# ルートURL ("/") にアクセスがあった場合に、フロントエンドのメインページを返す
@app.route("/")
def index():
    # staticフォルダ内のindex.htmlをクライアントに送信する
    return send_from_directory(app.static_folder, "index.html")

# 献立生成のためのAPIエンドポイント
@app.route("/generate_menu", methods=["POST"])
def generate_menu():
    app.logger.info("'/generate_menu' endpoint called.")
    # フロントエンドから送信されたJSONデータを取得
    data = request.get_json()

    # バリデーション: 'ingredients' が存在し、空のリストでないことを確認
    if not data or not isinstance(data.get("ingredients"), list) or not data.get("ingredients"):
        app.logger.warning("Invalid request: 'ingredients' are missing or not a list.")
        return jsonify({"error": "ingredients are required and must be a list."}), 400

    # リクエストデータから各値を取得
    ingredients = data["ingredients"]
    budget = data.get("budget")
    preference = data.get("preference")

    # --- AIに投げるプロンプト ---
    # ユーザーからの入力をもとに、AIへの指示（ユーザープロンプト）を作成
    user_prompt = f"""
    食材: {ingredients}
    追加予算: {budget if budget else "なし"}
    ユーザーの嗜好・条件: {preference if preference else "特になし"}
    JSON形式で献立を返してください。
    """

    # 外部API呼び出しとエラーハンドリング
    try:
        app.logger.info(f"Requesting menu from OpenRouter model: {CHAT_MODEL}")
        # OpenRouter APIにリクエストを送信
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}, # AIの役割を定義するシステムプロンプト
                {"role": "user", "content": user_prompt},     # ユーザーからの具体的な指示
            ],
            temperature=0.7, # 応答の多様性を設定 (0に近いほど決定的になる)
            response_format={"type": "json_object"}, # 応答形式をJSONに指定
        )

        # AIからの応答テキストを取得
        ai_response_text = response.choices[0].message.content

        # AIの応答が本当にJSON形式かを確認（パース試行）
        try:
            menu_data = json.loads(ai_response_text)
            app.logger.info("Successfully parsed JSON response from AI.")
        except json.JSONDecodeError:
            # JSONとしてパースできなかった場合のエラー処理
            app.logger.error(f"Failed to parse JSON from AI response. Raw response: {ai_response_text}")
            return jsonify({
                "error": "AI response was not valid JSON despite requesting JSON format.",
                "raw": ai_response_text
            }), 500

        # 成功した場合、パースしたJSONデータをフロントエンドに返す
        app.logger.info("Successfully generated menu. Sending response to client.")
        return jsonify(menu_data)

    # --- エラーハンドリング ---
    except APIStatusError as e:
        # OpenRouter APIがエラーレスポンスを返した場合 (例: 認証エラー, 4xx/5xx)
        app.logger.error(f"OpenRouter API error. Status: {e.status_code}, Response: {e.response.text}")
        return jsonify({"error": f"OpenRouter API error: {e.status_code} {e.response.text}"}), e.status_code
    except APIConnectionError as e:
        # OpenRouter APIに接続できなかった場合 (例: ネットワーク問題)
        app.logger.error(f"Failed to connect to OpenRouter API: {str(e)}")
        return jsonify({"error": f"Failed to connect to OpenRouter API: {str(e)}"}), 503
    except Exception as e:
        # 上記以外の予期せぬエラーが発生した場合
        app.logger.error(f"An unexpected error occurred in generate_menu: {str(e)}", exc_info=True)
        return jsonify({"error": f"An unexpected internal error occurred."}), 500

# --- 4. サーバーの起動 ---

# このファイルが直接実行された場合にのみ以下のコードを実行
if __name__ == "__main__":
    # 起動時にAPIキーが設定されているかチェック
    if not OPENROUTER_API_KEY:
        print("⚠️ 警告: OPENROUTER_API_KEY が設定されていません。API呼び出しは失敗します。")
    # Flaskの開発サーバーを起動
    # debug=True: コード変更時に自動でリロードし、詳細なエラーページを表示
    # host="0.0.0.0": ローカルネットワーク内の他のデバイスからアクセス可能にする
    # port=5000: 5000番ポートで待ち受ける
    app.run(debug=True, host="0.0.0.0", port=5000)