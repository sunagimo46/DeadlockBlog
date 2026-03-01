/** 全カテゴリスラッグの一覧 */
export const ALL_CATEGORIES = [
  "hero-guide",
  "patch-notes",
  "tactics",
] as const

/** カテゴリスラッグの型 */
export type Category = (typeof ALL_CATEGORIES)[number]

/** カテゴリのスラッグ -> 日本語ラベルのマッピング */
export const CATEGORY_LABELS: Record<Category, string> = {
  "hero-guide": "ヒーロー攻略",
  "patch-notes": "パッチノート",
  tactics: "立ち回り考察",
}

/** カテゴリのスラッグ -> カラークラスのマッピング */
export const CATEGORY_COLORS: Record<Category, string> = {
  "hero-guide": "text-hero-guide",
  "patch-notes": "text-patch-notes",
  tactics: "text-tactics",
}

/** カテゴリのスラッグ -> 説明文のマッピング */
export const CATEGORY_DESCRIPTIONS: Record<Category, string> = {
  "hero-guide": "各ヒーローの立ち回り、ビルド、スキル解説などの攻略情報",
  "patch-notes": "最新パッチノートの解説と環境変化への影響分析",
  tactics: "立ち回りの基礎から応用まで、勝利につながる戦術・考察を解説",
}

/** 1ページあたりの記事数 */
export const POSTS_PER_PAGE = 12

/** サイト共通定数 */
export const SITE_URL = "https://deadlock-guide.netlify.app"
export const SITE_NAME = "Deadlock攻略ブログ"
export const SITE_DESCRIPTION =
  "Valveの新作ヒーローシューター「Deadlock」の攻略情報、最新メタ、ヒーローガイド、パッチノート解説"
