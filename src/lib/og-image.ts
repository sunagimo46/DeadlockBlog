import satori from "satori"
import { Resvg } from "@resvg/resvg-js"
import { SITE_NAME, CATEGORY_LABELS } from "./constants"
import type { Category } from "./constants"

interface OgImageOptions {
  readonly title: string
  readonly category: Category
}

/** Google Fonts API から Noto Sans JP のフォントデータを取得する */
async function loadFont(weight: number): Promise<ArrayBuffer> {
  const url = `https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@${weight}&display=swap`
  const css = await fetch(url).then((res) => res.text())

  const fontUrlMatch = css.match(/src:\s*url\(([^)]+)\)/)
  if (!fontUrlMatch) {
    throw new Error(`フォントURLの取得に失敗: weight=${weight}`)
  }

  return fetch(fontUrlMatch[1]).then((res) => res.arrayBuffer())
}

/** OGP画像をPNG形式で生成する */
export async function generateOgImage(
  options: OgImageOptions,
): Promise<Buffer> {
  const { title, category } = options
  const categoryLabel = CATEGORY_LABELS[category] ?? category

  const [fontRegular, fontBold] = await Promise.all([
    loadFont(400),
    loadFont(700),
  ])

  const svg = await satori(
    {
      type: "div",
      props: {
        style: {
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          backgroundColor: "#0f0f13",
          padding: "60px",
        },
        children: [
          {
            type: "div",
            props: {
              style: {
                display: "flex",
                flexDirection: "column",
                gap: "20px",
              },
              children: [
                {
                  type: "span",
                  props: {
                    style: {
                      color: "#c49a6c",
                      fontSize: "24px",
                      fontWeight: 400,
                    },
                    children: categoryLabel,
                  },
                },
                {
                  type: "h1",
                  props: {
                    style: {
                      color: "#e8e6e3",
                      fontSize: title.length > 30 ? "40px" : "48px",
                      fontWeight: 700,
                      lineHeight: 1.4,
                      margin: 0,
                    },
                    children: title,
                  },
                },
              ],
            },
          },
          {
            type: "div",
            props: {
              style: {
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderTop: "2px solid #2e2e3a",
                paddingTop: "24px",
              },
              children: [
                {
                  type: "span",
                  props: {
                    style: {
                      color: "#c49a6c",
                      fontSize: "28px",
                      fontWeight: 700,
                    },
                    children: SITE_NAME,
                  },
                },
                {
                  type: "span",
                  props: {
                    style: {
                      color: "#6b7280",
                      fontSize: "20px",
                    },
                    children: "deadlock-guide.netlify.app",
                  },
                },
              ],
            },
          },
        ],
      },
    },
    {
      width: 1200,
      height: 630,
      fonts: [
        { name: "Noto Sans JP", data: fontRegular, weight: 400, style: "normal" as const },
        { name: "Noto Sans JP", data: fontBold, weight: 700, style: "normal" as const },
      ],
    },
  )

  const resvg = new Resvg(svg, {
    fitTo: { mode: "width" as const, value: 1200 },
  })
  const pngData = resvg.render()
  return pngData.asPng()
}
