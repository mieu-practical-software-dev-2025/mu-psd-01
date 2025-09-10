// このファイルは、フロントエンドのVue.jsアプリケーションのロジックを定義します。
// ユーザーの入力を管理し、バックエンドAPIと通信して結果を表示します。

// Vue.jsの`createApp`関数をインポート
const { createApp } = Vue;

// Vueアプリケーションのインスタンスを作成
const app = createApp({
  // --- 1. データプロパティ ---
  // アプリケーションの状態を管理するデータを定義します。
  data() {
    return {
      // --- ユーザー入力 ---
      ingredientsText: "",
      budget: "",
      preference: "",

      // --- アプリケーションの状態 ---
      menu: null,
      loading: false,
      error: null,
    };
  },

  // --- 2. メソッド ---
  // ユーザーのアクションに応じて実行される関数を定義します。
  methods: {
    // '献立を作成'ボタンがクリックされたときに実行される非同期関数
    async generateMenu() {
      // 既にリクエスト処理中の場合は何もしない
      if (this.loading) return;

      // --- 処理開始前の状態リセット ---
      this.loading = true;
      this.error = null;
      this.menu = null;

      // --- フロントエンドでの入力チェック強化 ---
      // 予算が入力されていて、かつ0未満の数値である場合はエラー
      if (this.budget && this.budget < 0) {
        this.error = "予算には0以上の数値を入力してください。";
        this.loading = false; // ローディングを解除
        return;
      }

      try {
        // --- 入力値の整形とバリデーション ---
        // 入力された食材テキストをカンマで分割し、各要素の空白を除去し、空の要素をフィルタリング
        const ingredients = this.ingredientsText
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);

        // 食材が1つも入力されていない場合はエラーメッセージを設定して処理を中断
        if (ingredients.length === 0) {
          this.error = "食材を1つ以上入力してください。";
          this.loading = false; // ローディングを解除
          return;
        }

        // --- APIリクエストの準備と送信 ---
        // Fetch APIを使用してバックエンドの'/generate_menu'エンドポイントにPOSTリクエストを送信
        const res = await fetch("/generate_menu", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ingredients: ingredients,
            budget: (this.budget === '' || this.budget === null) ? null : this.budget,
            preference: this.preference || null,
          }),
        });

        // --- レスポンスの処理 ---
        const data = await res.json();
        // レスポンスが正常でない場合 (HTTPステータスが2xx以外)
        if (!res.ok) {
          this.error = data.error || "不明なエラーが発生しました。";
        } else {
          // 正常な場合は、取得した献立データを'menu'プロパティにセット
          this.menu = data;
        }
      } catch (err) {
        // --- エラーハンドリング ---
        // ネットワークエラーなどでfetch自体が失敗した場合
        this.error = "通信エラーが発生しました。サーバーが起動しているか確認してください。";
        console.error(err);
      } finally {
        // --- 処理終了時の共通処理 ---
        // 成功・失敗にかかわらず、ローディング状態をOFFにする
        this.loading = false;
      }
    },
  },
});

// --- 3. グローバルコンポーネントの定義 ---
// アプリケーション全体で再利用可能なUI部品を定義します。

// 料理一品分の情報を表示するカードコンポーネント
app.component("dish-card", {
  // 親コンポーネントから受け取るデータ ('props')
  props: {
    // 'dish'という名前のプロパティを受け取る。型はObjectで、必須。
    dish: { type: Object, required: true },
  },
  // コンポーネントのHTML構造
  template: `
    <div class="card mb-3 shadow-sm">
      <div class="card-header bg-primary bg-opacity-75 text-white">
        <h5 class="card-title mb-0">{{ dish.name }}</h5>
      </div>
      <div class="card-body">
        <p><strong>材料:</strong> {{ dish.ingredients.join(", ") }}</p>
        <p class="mb-1"><strong>手順:</strong></p>
        <ol class="ps-3">
          <li v-for="(step, i) in dish.steps" :key="i">{{ step }}</li>
        </ol>
      </div>
      <div class="card-footer bg-light">
        <small class="text-muted">
          <strong>カロリー:</strong> {{ dish.calories }} kcal
          <span v-if="dish.nutrition" class="ms-3">
            <strong>栄養素:</strong>
            P: {{ dish.nutrition["たんぱく質"] }} /
            F: {{ dish.nutrition["脂質"] }} /
            C: {{ dish.nutrition["炭水化物"] }}
          </span>
        </small>
      </div>
    </div>
  `,
});

// 献立プラン（複数の料理カードを含む）を表示するコンポーネント
app.component("menu-plan", {
  props: {
    // 'title': 献立プランのタイトル (例: "今ある食材だけで作る献立")
    title: { type: String, required: true },
    // 'plan': 献立プランのデータオブジェクト
    plan: { type: Object, required: true },
  },
  // コンポーネント自身の状態を管理するデータ
  data() {
    return {
      copied: false, // 「コピーしました！」のフィードバック表示用
    };
  },
  methods: {
    // 買い物リストをクリップボードにコピーするメソッド
    copyShoppingList() {
      if (!this.plan.shopping_list || this.copied) return;
      // リストの各項目を改行で連結してテキストを作成
      const listText = this.plan.shopping_list.join('\n');
      // クリップボードへの書き込み
      navigator.clipboard.writeText(listText).then(() => {
        this.copied = true; // 成功したら表示を切り替え
        // 2秒後に表示を元に戻す
        setTimeout(() => {
          this.copied = false;
        }, 2000);
      });
    }
  },
  template: `
    <div class="mb-5">
      <h4 class="plan-title mb-4">{{ title }}</h4>
      <!-- planデータがあり、料理リスト(dishes)に1つ以上の料理が含まれている場合に表示 -->
      <div v-if="plan && plan.dishes && plan.dishes.length > 0">
        <!-- 料理リストをループして、各料理を'dish-card'コンポーネントで表示 -->
        <dish-card v-for="(dish, idx) in plan.dishes" :key="idx" :dish="dish"></dish-card>

        <div class="alert alert-success mt-4">
          <p class="mb-1"><strong>合計カロリー:</strong> {{ plan.total_calories }} kcal</p>
          <hr>
          <p class="mb-0"><em>{{ plan.notes }}</em></p>
        </div>

        <!-- 買い物リストのカード -->
        <div v-if="plan.shopping_list && plan.shopping_list.length > 0" class="card mt-4">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">買い物リスト</h5>
            <button class="btn btn-sm btn-outline-primary" @click="copyShoppingList" :disabled="copied">
              <span v-if="!copied">リストをコピー</span>
              <span v-else>コピーしました！</span>
            </button>
          </div>
          <ul class="list-group list-group-flush">
            <li v-for="item in plan.shopping_list" :key="item" class="list-group-item">
              {{ item }}
            </li>
          </ul>
        </div>
      </div>
      <!-- 料理リストが空の場合でも、planデータ自体は存在する場合 (例: 予算内で提案なし) -->
      <div v-else-if="plan">
        <div class="alert alert-secondary"><em>{{ plan.notes }}</em></div>
      </div>
    </div>
  `,
});

// --- 4. アプリケーションのマウント ---
// 作成したVueアプリケーションのインスタンスを、HTMLの特定の要素に紐付けます。
// これにより、その要素内でVueの機能が有効になります。
app.mount("#app");