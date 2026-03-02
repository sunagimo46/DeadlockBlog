// @ts-check
import { defineConfig } from "astro/config"
import react from "@astrojs/react"
import mdx from "@astrojs/mdx"
import sitemap from "@astrojs/sitemap"
import tailwindcss from "@tailwindcss/vite"
import remarkBreaks from "remark-breaks"

// https://astro.build/config
export default defineConfig({
  site: "https://deadlocktimes.jp",
  integrations: [react(), mdx(), sitemap()],
  markdown: {
    remarkPlugins: [remarkBreaks],
  },
  vite: {
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        "@components": "/src/components",
      },
    },
  },
})
