# みんなの献立アドバイザー - 生成AI活用サンプルアプリ

## 1. 概要

このアプリケーションは、Python (Flask) と Vue.js を用いて作られた、生成AI活用Webアプリケーションのサンプルです。
冷蔵庫にある食材や追加予算、好みを入力すると、AIが栄養バランスを考慮した2パターンの献立を提案してくれます。

## 2. 主な機能

- **入力**:
  - 今ある食材（カンマ区切り）
  - 追加購入に使える予算（任意）
  - 料理の嗜好や条件（任意）
- **出力**:
  - **① 今ある食材だけで作る献立**: 追加購入なしで作成可能な献立
  - **② 予算を使った献立**: 予算内で食材を追加購入し、栄養や彩りを改善した献立
  - 各料理の材料、手順、概算カロリー、栄養素（PFC）
  - **買い物リスト**: 追加購入が必要な食材を一覧表示（コピー機能付き）
  - **使用調味料リスト**: 献立全体で使う調味料を一覧表示

## 3. 技術スタック

| 分類         | 技術・ライブラリ |
|--------------|------------------|
| フロントエンド | Vue.js (CDN), Bootstrap 5 |
| バックエンド  | Python, Flask |
| AI連携       | OpenRouter API (openai-pythonライブラリ経由) |
| データベース   | なし (状態は保持しない) |

## 4. ファイル構成

```
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3 -e --source winget
winget install --id Microsoft.VisualStudioCode -e --source winget
```

- vscodeを起動し、アクティビティバーの拡張機能から、以下のプラグインをインストールしてください。

  - Gemini Code Assist
  - Python
  - Vue.js Extension Pack

# 環境セットアップ

- [OpenRouter](https://openrouter.ai/)にアカウントを作成します。

- OpenRouterで、Keys → Create API Keys を選択、適当なキー名を付けて作成し、キー文字列をメモ帳等に保存しておきます。

- Python ライブラリインストール

  以下のコマンドでPythonの利用ライブラリをインストールします。

  ``` pip install -r requrements.txt ```

# 実行方法

- example.envを.envにリネームして、OpenRouterのキーを記載してください。

- 以下のコマンドでサーバを起動します。

  ``` python app.py ```

- ブラウザで以下のURLにアクセスしてみてください。

  ``` http://localhost:5000 ```

# 開発の参考資料

- vscodeのGemini Code Assist を起動して修正を依頼すると、コードを修正したり解説してくれます。

# 参考リンク

- [Flask](https://flask.palletsprojects.com/en/stable/)

  - Python で書かれた Webアプリケーションサーバ

- [Vue.js](https://vuejs.org/)

  - JavaScript製製のWebフロントエンド フレームワーク

- [Vue.js Tutorial](https://ja.vuejs.org/tutorial/)

  - Vue.jsの入門用チュートリアル
  
- [OpenAI API](https://github.com/openai/openai-python)

  - Pythonから、OpenAI APIを呼び出すライブラリ
