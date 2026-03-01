import type { APIRoute, GetStaticPaths } from "astro"
import { getCollection } from "astro:content"
import { generateOgImage } from "../../lib/og-image"
import type { Category } from "../../lib/constants"

export const getStaticPaths: GetStaticPaths = async () => {
  const posts = await getCollection("blog", ({ data }) => {
    return import.meta.env.PROD ? data.draft !== true : true
  })

  return posts.map((post) => ({
    params: { id: post.id },
    props: { post },
  }))
}

export const GET: APIRoute = async ({ props }) => {
  const { post } = props as { post: { data: { title: string; category: Category } } }

  const png = await generateOgImage({
    title: post.data.title,
    category: post.data.category,
  })

  return new Response(png, {
    headers: { "Content-Type": "image/png" },
  })
}
