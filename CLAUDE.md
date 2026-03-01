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
| `tactics` | 立ち回り考察 |

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

## ローカル字幕ベース記事作成ルール

`transcripts/*.md` ファイルが渡された場合:

- ファイルの「## 字幕テキスト」セクションを参考情報として活用する
- YouTube字幕特有のノイズ（フィラーワード、重複表現）は除去して情報を整理する
- 字幕テキストのみでは不足する情報はDeadlock Wikiで補完する
- フロントマターの `category` と `hero` はユーザーに確認するか、内容から推測して設定する
- 参考元のYouTube URLは記事末尾「## 参考リンク」セクションに記載する
- 動画の元タイトルを参考に、日本語の記事タイトルを考案する

**字幕ファイルの取得方法:**
```bash
cd scripts
python fetch_transcript.py --url https://www.youtube.com/watch?v=xxx
```

## リサーチベース記事作成ルール

Issueに「リサーチ結果」コメントがある場合:

- リサーチ結果のYouTube動画、Reddit投稿、Wiki記事の内容を参考にする
- 複数ソースの情報を統合し、独自の視点でまとめる
- 参考元のURLは記事末尾に「## 参考リンク」セクションとしてまとめる
- 情報の優先度: Wiki（正確性）> Reddit（実戦知見）> YouTube（最新メタ）
- Issueの「カテゴリ」チェックを確認し、適切なcategoryをフロントマターに設定する
