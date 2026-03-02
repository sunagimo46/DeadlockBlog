import { defineCollection, z } from "astro:content"
import { glob } from "astro/loaders"

const blog = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/data/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()),
    category: z.enum([
      "hero-guide",
      "patch-notes",
      "tactics",
    ]),
    hero: z.string().optional(),
    draft: z.boolean().default(false),
  }),
})

export const collections = { blog }
