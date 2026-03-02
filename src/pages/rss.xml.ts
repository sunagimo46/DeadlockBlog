import rss from "@astrojs/rss"
import type { APIRoute } from "astro"
import { getPublishedPosts, sortPostsByDate, getSlug } from "../lib/posts"
import { SITE_NAME, SITE_DESCRIPTION, SITE_URL } from "../lib/constants"

export const GET: APIRoute = async (context) => {
  const posts = await getPublishedPosts()
  const sortedPosts = sortPostsByDate(posts)

  return rss({
    title: SITE_NAME,
    description: SITE_DESCRIPTION,
    site: context.site?.toString() ?? SITE_URL,
    items: sortedPosts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      link: `/blog/${getSlug(post.id)}`,
      categories: [post.data.category, ...post.data.tags],
    })),
    customData: "<language>ja</language>",
  })
}
