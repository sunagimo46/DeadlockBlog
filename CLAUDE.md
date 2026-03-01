# Deadlock 攻略ブログ - Claude Code ガイドライン

## プロジェクト構成

- フレームワーク: Astro 5.x + React 19.x
- スタイル: Tailwind CSS v4
- コンテンツ: Content Collections (glob loader)
- 記事格納先: `src/data/blog/`

## 記事作成ルール

### ファイル命名規則

`src/data/blog/YYYY-MM-DD-slug.md`

- `slug` は英数字とハイフンのみ使用
- 日付は記事の公開日

### 必須フロントマター

```yaml
---
title: "記事タイトル"
description: "記事の概要（120文字程度）"
pubDate: YYYY-MM-DD
tags: ["タグ1", "タグ2"]
category: "カテゴリ"
draft: false
---
```

### カテゴリ一覧

| カテゴリ値 | 表示名 |
|-----------|--------|
| `hero-guide` | ヒーロー攻略 |
| `patch-notes` | パッチノート解説 |
| `meta` | メタ考察 |
| `item-guide` | アイテムガイド |
| `tips` | Tips & テクニック |

### オプションフィールド

- `hero`: 関連ヒーロー名（ヒーロー攻略記事の場合）
- `updatedDate`: 更新日
- `draft`: true にすると本番では非表示

## 執筆ガイドライン

- **言語**: 日本語で執筆すること
- **対象読者**: 初心者〜中級者
- **文体**: ですます調、分かりやすく実戦的な内容
- **見出し**: h2（##）から開始、h1 は使わない（タイトルが h1）
- **情報源**: Deadlock Wiki、Reddit、YouTube の情報を参考に
- **品質**: フロントマターの必須項目を必ず含める

## 参考情報源

- Deadlock Wiki: https://deadlock.wiki/
- Reddit: https://www.reddit.com/r/DeadlockTheGame/
- YouTube チャンネル: Eidorian, Deathy, MastYT, Midknighttxt, poshypop
