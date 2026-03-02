import { getCollection } from "astro:content"
import type { CollectionEntry } from "astro:content"

export interface AdjacentPost {
  slug: string
  title: string
}

/** ファイルパス形式のidからスラッグ（ファイル名部分）を取得する（例: "2026/03/blog-name" → "blog-name"） */
export function getSlug(id: string): string {
  return id.split("/").pop() ?? id
}

/** 公開済み記事のみ取得（開発環境ではdraft記事も含む） */
export async function getPublishedPosts(): Promise<CollectionEntry<"blog">[]> {
  return getCollection("blog", ({ data }) => {
    return import.meta.env.PROD ? data.draft !== true : true
  })
}

/** 記事を公開日の降順でソート（元配列を変更しない） */
export function sortPostsByDate(
  posts: CollectionEntry<"blog">[],
): CollectionEntry<"blog">[] {
  return [...posts].sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf(),
  )
}

/** 現在の記事の前後にある記事を取得（日付降順で前=新しい、次=古い） */
export function getAdjacentPosts(
  currentPost: CollectionEntry<"blog">,
  allPosts: readonly CollectionEntry<"blog">[],
): { prev: AdjacentPost | undefined; next: AdjacentPost | undefined } {
  const sorted = sortPostsByDate([...allPosts])
  const currentIndex = sorted.findIndex((p) => p.id === currentPost.id)

  if (currentIndex === -1) {
    return { prev: undefined, next: undefined }
  }

  const prevEntry = currentIndex > 0 ? sorted[currentIndex - 1] : undefined
  const nextEntry =
    currentIndex < sorted.length - 1 ? sorted[currentIndex + 1] : undefined

  return {
    prev: prevEntry
      ? { slug: getSlug(prevEntry.id), title: prevEntry.data.title }
      : undefined,
    next: nextEntry
      ? { slug: getSlug(nextEntry.id), title: nextEntry.data.title }
      : undefined,
  }
}
