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
          return;
        }

        // --- APIリクエストの準備と送信 ---
        // Fetch APIを使用してバックエンドの'/generate_menu'エンドポイントにPOSTリクエストを送信
        const res = await fetch("/generate_menu", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ingredients: ingredients,
            budget: this.budget ? parseInt(this.budget) : null,
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
    <div class="card mb-3">
      <div class="card-body">
        <h5 class="card-title">{{ dish.name }}</h5>
        <p><strong>材料:</strong> {{ dish.ingredients.join(", ") }}</p>
        <p><strong>手順:</strong></p>
        <ol>
          <li v-for="(step, i) in dish.steps" :key="i">{{ step }}</li>
        </ol>
        <p><strong>カロリー:</strong> {{ dish.calories }} kcal</p>
        <p v-if="dish.nutrition">
          <strong>栄養素:</strong>
          たんぱく質 {{ dish.nutrition["たんぱく質"] }} /
          脂質 {{ dish.nutrition["脂質"] }} /
          炭水化物 {{ dish.nutrition["炭水化物"] }}
        </p>
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
  template: `
    <div class="mb-4">
      <h4>{{ title }}</h4>
      <!-- planデータがあり、料理リスト(dishes)に1つ以上の料理が含まれている場合に表示 -->
      <div v-if="plan && plan.dishes && plan.dishes.length > 0">
        <!-- 料理リストをループして、各料理を'dish-card'コンポーネントで表示 -->
        <dish-card v-for="(dish, idx) in plan.dishes" :key="idx" :dish="dish"></dish-card>
        <p><strong>合計カロリー:</strong> {{ plan.total_calories }} kcal</p>
        <p><em>{{ plan.notes }}</em></p>
      </div>
      <!-- 料理リストが空の場合でも、planデータ自体は存在する場合 (例: 予算内で提案なし) -->
      <div v-else-if="plan">
        <p><em>{{ plan.notes }}</em></p>
      </div>
    </div>
  `,
});

// --- 4. アプリケーションのマウント ---
// 作成したVueアプリケーションのインスタンスを、HTMLの特定の要素に紐付けます。
// これにより、その要素内でVueの機能が有効になります。
app.mount("#app");