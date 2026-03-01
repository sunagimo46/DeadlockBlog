/** 全カテゴリスラッグの一覧 */
export const ALL_CATEGORIES = [
  "hero-guide",
  "patch-notes",
  "meta",
  "item-guide",
  "tips",
] as const

/** カテゴリスラッグの型 */
export type Category = (typeof ALL_CATEGORIES)[number]

/** カテゴリのスラッグ -> 日本語ラベルのマッピング */
export const CATEGORY_LABELS: Record<Category, string> = {
  "hero-guide": "ヒーロー攻略",
  "patch-notes": "パッチノート",
  meta: "メタ考察",
  "item-guide": "アイテムガイド",
  tips: "Tips",
}

/** カテゴリのスラッグ -> カラークラスのマッピング */
export const CATEGORY_COLORS: Record<Category, string> = {
  "hero-guide": "text-hero-guide",
  "patch-notes": "text-patch-notes",
  meta: "text-meta",
  "item-guide": "text-item-guide",
  tips: "text-tips",
}

/** カテゴリのスラッグ -> 説明文のマッピング */
export const CATEGORY_DESCRIPTIONS: Record<Category, string> = {
  "hero-guide": "各ヒーローの立ち回り、ビルド、スキル解説などの攻略情報",
  "patch-notes": "最新パッチノートの解説と環境変化への影響分析",
  meta: "現在の環境における最強構成や戦略の考察",
  "item-guide": "アイテムの効果、購入タイミング、おすすめビルドの解説",
  tips: "初心者から上級者まで使えるテクニックやコツの紹介",
}

/** 1ページあたりの記事数 */
export const POSTS_PER_PAGE = 12

/** サイト共通定数 */
export const SITE_URL = "https://deadlock-guide.netlify.app"
export const SITE_NAME = "Deadlock攻略ブログ"
export const SITE_DESCRIPTION =
  "Valveの新作ヒーローシューター「Deadlock」の攻略情報、最新メタ、ヒーローガイド、パッチノート解説"
