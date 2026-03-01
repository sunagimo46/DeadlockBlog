/** Markdownの記号を除去してプレーンテキストを抽出する */
function stripMarkdown(markdown: string): string {
  return markdown
    .replace(/^---[\s\S]*?---/m, "")
    .replace(/!\[.*?\]\(.*?\)/g, "")
    .replace(/\[([^\]]*)\]\(.*?\)/g, "$1")
    .replace(/#{1,6}\s/g, "")
    .replace(/[*_~`>-]/g, "")
    .replace(/\n{2,}/g, "\n")
    .trim()
}

/** 日本語テキストの読了時間（分）を算出する */
export function calculateReadingTime(markdown: string): number {
  const CHARS_PER_MINUTE = 500
  const plainText = stripMarkdown(markdown)
  const minutes = Math.ceil(plainText.length / CHARS_PER_MINUTE)
  return Math.max(1, minutes)
}
