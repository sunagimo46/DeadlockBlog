import type { CollectionEntry } from "astro:content"

interface ScoredPost {
  readonly post: CollectionEntry<"blog">
  readonly score: number
}

/** 関連記事をスコアリングして上位N件を返す */
export function getRelatedPosts(
  currentPost: CollectionEntry<"blog">,
  allPosts: readonly CollectionEntry<"blog">[],
  maxCount: number = 3,
): CollectionEntry<"blog">[] {
  const scored: ScoredPost[] = allPosts
    .filter((post) => post.id !== currentPost.id)
    .map((post) => {
      const categoryScore =
        post.data.category === currentPost.data.category ? 2 : 0
      const tagScore = post.data.tags.filter((tag) =>
        currentPost.data.tags.includes(tag),
      ).length
      return { post, score: categoryScore + tagScore }
    })

  return [...scored]
    .filter((item) => item.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score
      return b.post.data.pubDate.valueOf() - a.post.data.pubDate.valueOf()
    })
    .slice(0, maxCount)
    .map((item) => item.post)
}
