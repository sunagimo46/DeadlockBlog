# Deadlock 攻略ブログ

Valve の新作ヒーローシューター「Deadlock」の攻略情報を発信するブログです。
YouTube・Reddit・Deadlock Wiki から話題を自動収集し、Claude Code が記事を自動生成します。

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| フレームワーク | Astro 5.x + React 19.x |
| スタイリング | Tailwind CSS v4 |
| コンテンツ管理 | Content Collections (glob loader) |
| 記事生成 | Anthropic Python SDK (claude-sonnet-4-6) |
| データ収集 | Python 3.11+ |
| CI/CD | GitHub Actions |
| ホスティング | Netlify |

---

## ローカル開発

### 必要な環境

- Node.js 20+
- Python 3.11+

### セットアップ

```bash
# 依存パッケージをインストール
npm install

# 開発サーバーを起動（http://localhost:4321）
npm run dev

# ビルド
npm run build

# ビルド結果をプレビュー
npm run preview
```

---

## 記事の書き方

### 手動で記事を作成する

`src/data/blog/` 配下に Markdown ファイルを作成します。

**ファイル名:** `YYYY-MM-DD-slug.md`（slug は英数字とハイフンのみ）

```markdown
---
title: "記事タイトル"
description: "記事の概要（120文字程度）"
pubDate: 2026-03-01
tags: ["タグ1", "タグ2"]
category: "hero-guide"
draft: false
---

## 見出し（h2 から開始）

本文...
```

### カテゴリ一覧

| カテゴリ値 | 表示名 | 説明 |
|-----------|--------|------|
| `hero-guide` | ヒーロー攻略 | 各ヒーローの立ち回り・ビルド・スキル解説 |
| `patch-notes` | パッチノート解説 | 最新パッチノートの解説と環境分析 |
| `tactics` | 立ち回り考察 | 現在の環境における戦術・立ち回り・構成分析 |

### フロントマターのオプションフィールド

- `hero`: 関連ヒーロー名（ヒーロー攻略記事の場合）
- `updatedDate`: 記事を更新した日付
- `draft: true`: 本番環境で非表示にする

---

## Claude API による記事自動生成

記事生成には `anthropics/claude-code-action` の代わりに Anthropic Python SDK を直接利用しています。
`scripts/generate_article.py` が Claude API (`claude-sonnet-4-6`) を呼び出して記事を生成します。

### 方法 1: 話題トピック Issue に /generate でコメント

毎日 JST 9:00 に GitHub Actions が自動で「本日の話題トピック」Issue を作成します。
書いてほしいトピックの Issue に以下のようにコメントするだけで記事が生成されます。

```
/generate
```

記事が生成されて PR が自動作成されます。PR をレビューしてマージすると Netlify に自動デプロイされます。

### 方法 2: 記事作成リクエスト Issue を手動作成

GitHub の Issue テンプレート **「記事作成リクエスト」** を使って Issue を作成します。

1. GitHub の Issues タブ → **New issue** → **記事作成リクエスト** を選択
2. トピック・カテゴリ・参考情報（URL）を記入して Issue を作成（`article-request` ラベルが自動付与）
3. Issue に `/fetch-refs` とコメントして参考情報 URL のコンテンツを取得
4. コンテンツがコメントに追加されたら `/generate` とコメント
5. PR が自動作成されるのでレビュー → マージ

> **`/fetch-refs` で参考情報URLのコンテンツを取得**
>
> Issue の **「参考情報」** 欄に YouTube・Reddit・Deadlock Wiki の URL を記載し、
> `/fetch-refs` を実行するとコンテンツ（字幕・投稿本文・Wikiテキスト）が Issue にコメントされます。
> その後 `/generate` を実行すると、取得済みコンテンツが記事生成のプロンプトに自動的に組み込まれます。
> 取得に失敗した場合は `/fetch-refs` を再実行できます。
>
> ```
> ### 参考情報
> https://www.youtube.com/watch?v=xxxx   ← 字幕を自動取得
> https://www.reddit.com/r/DeadlockTheGame/comments/xxxx/  ← 本文を自動取得
> https://deadlock.wiki/wiki/McGinnis    ← Wikiテキストを自動取得
> ```
>
> 対応する URL の種類:
> | URL | 取得内容 | 上限 |
> |-----|---------|------|
> | `youtube.com/watch`, `youtu.be/` | 動画の字幕テキスト | 5,000 文字 |
> | `reddit.com/r/.../comments/...` | 投稿タイトル + 本文 | 1,000 文字 |
> | `deadlock.wiki/wiki/...` | ページの Wikitext | 2,000 文字 |

### 方法 4: ローカル字幕取得 → Claude Code で記事生成

GitHub Actions を使わずにローカルで完結する方法です。YouTube字幕の取得が GitHub Actions 環境で難しい場合に有効です。

1. **字幕をローカルに保存**

```bash
cd scripts
python fetch_transcript.py --url https://www.youtube.com/watch?v=xxxx
```

実行すると `transcripts/YYYYMMDD-{動画ID}.md` に字幕ファイルが保存されます。

2. **Claude Code で記事を作成**

Claude Code（このターミナル）に以下のように依頼します。

```
transcripts/20260301-abc123.md の字幕をもとにDeadlock攻略記事を作成してください
```

Claude Code が字幕テキストを読み込んで `src/data/blog/` に記事ファイルを生成します。

### 方法 3: リサーチ → 記事生成（2ステップ）

詳細な参考情報が必要な場合は、リサーチを先に実行します。

1. **リサーチリクエスト Issue を作成**
   - Issue テンプレート **「リサーチリクエスト」** を選択
   - トピック・検索キーワード（英語）・カテゴリを記入
   - Issue 作成と同時にリサーチが自動実行され、YouTube・Reddit・Wiki の情報がコメントに追加されます

2. **リサーチ結果をもとに記事生成**
   - リサーチ結果が追加されたら同 Issue に以下のようにコメント
   ```
   /generate
   ```

---

## GitHub Actions ワークフロー

| ワークフロー | トリガー | 内容 |
|-------------|---------|------|
| `collect-topics.yml` | 毎日 JST 9:00（手動実行も可） | YouTube・Reddit・Wiki から話題トピックを収集し Issue を作成 |
| `claude.yml` | `article-request` ラベル付き Issue に `/generate` コメント | Anthropic Python SDK で記事を生成して PR を作成 |
| `research-topic.yml` (`research` job) | `research-request` ラベルが付いた Issue 作成時、または `/research` コメント | トピックをキーワード検索してリサーチ結果を Issue にコメント |
| `research-topic.yml` (`fetch-references` job) | `article-request` ラベル付き Issue に `/fetch-refs` コメント | 参考情報 URL からコンテンツを取得して Issue にコメント |

---

## GitHub Secrets の設定

リポジトリの **Settings → Secrets and variables → Actions** で以下を設定してください。

| Secret 名 | 説明 |
|-----------|------|
| `ANTHROPIC_API_KEY` | Anthropic API キー |
| `GITHUB_TOKEN` | 自動付与されるため設定不要 |

### `ANTHROPIC_API_KEY` の取得方法

1. [console.anthropic.com](https://console.anthropic.com) にログイン
2. **API Keys** → **Create Key** で新しい API キーを発行
3. 発行したキーをリポジトリの Secrets に `ANTHROPIC_API_KEY` として登録

---

## データ収集スクリプト（ローカル実行）

```bash
# 依存パッケージをインストール
pip install -r scripts/requirements.txt

# トピック収集のみ実行（Issue は作成しない確認用）
python scripts/collect.py

# 特定トピックのリサーチを実行
cd scripts
python research.py --topic "Viscous攻略" --keywords "Viscous guide,build" --issue-number 0

# 記事リクエスト Issue の参考URLコンテンツをローカルで確認
cd scripts
python fetch_references.py --issue-number 123 --dry-run

# YouTube 字幕をローカルファイルに保存
cd scripts
python fetch_transcript.py --url https://www.youtube.com/watch?v=xxxx
# → transcripts/YYYYMMDD-{動画ID}.md に保存される

# テスト実行
python -m pytest scripts/tests/ -v
```

---

## ディレクトリ構成

```
Deadlock攻略ブログ/
├── CLAUDE.md                    # Claude Code への記事作成ガイドライン
├── .github/
│   ├── workflows/
│   │   ├── collect-topics.yml   # 定期データ収集 → Issue 作成
│   │   ├── claude.yml           # /generate コメントで記事生成
│   │   └── research-topic.yml  # トピックリサーチ
│   └── ISSUE_TEMPLATE/
│       ├── article-request.md  # 記事作成リクエスト用テンプレート
│       └── research-request.md # リサーチリクエスト用テンプレート
├── transcripts/                 # ローカル字幕ファイル（gitignore 対象）
├── scripts/
│   ├── collect.py               # データ収集メインスクリプト
│   ├── research.py              # トピックリサーチスクリプト（research-request 用）
│   ├── fetch_references.py      # 参考URLコンテンツ取得スクリプト（article-request 用）
│   ├── fetch_transcript.py      # YouTube字幕ローカル取得スクリプト（方法4用）
│   ├── generate_article.py      # Claude API 記事生成スクリプト
│   ├── sources/
│   │   ├── youtube.py           # YouTube RSS 取得・字幕取得
│   │   ├── reddit.py            # Reddit JSON API 取得・投稿本文取得
│   │   └── wiki.py              # MediaWiki API 取得・ページ本文取得
│   ├── tests/
│   │   ├── test_youtube.py      # youtube.py のテスト
│   │   ├── test_reddit.py       # reddit.py のテスト
│   │   ├── test_wiki.py         # wiki.py のテスト
│   │   └── test_generate_article.py  # generate_article.py のテスト
│   └── requirements.txt
└── src/
    ├── content.config.ts        # Content Collections スキーマ
    ├── data/blog/               # 記事ファイル（.md）
    ├── components/              # Astro / React コンポーネント
    ├── layouts/                 # ベース・記事レイアウト
    ├── pages/                   # ルーティング
    ├── lib/                     # ユーティリティ関数・定数
    └── styles/global.css        # Tailwind CSS エントリポイント
```

---

## 日常の運用フロー

**話題トピックから記事生成（方法 1）:**
```
毎日 JST 9:00（自動）
  → 「本日の話題トピック」Issue が作成される

ユーザー（随時）
  → Issue を確認
  → 書いてほしいトピックに /generate とコメント

GitHub Actions（自動）
  → generate_article.py が Claude API で記事を生成して PR を作成

ユーザー（随時）
  → PR をレビュー、必要なら修正依頼
  → マージ → Netlify が自動デプロイ
```

**記事リクエストから記事生成（方法 2）:**
```
ユーザー
  → 「記事作成リクエスト」Issue を作成（参考情報URLを記載）

ユーザー
  → /fetch-refs とコメント

GitHub Actions（自動）
  → fetch_references.py が参考URLのコンテンツを取得してコメント

ユーザー
  → 内容を確認後、/generate とコメント

GitHub Actions（自動）
  → generate_article.py が参考コンテンツを活用して記事を生成して PR を作成

ユーザー
  → PR をレビュー → マージ → Netlify が自動デプロイ
```

**ローカル字幕から記事生成（方法 4）:**
```
ユーザー（ローカルで実行）
  → python scripts/fetch_transcript.py --url https://youtu.be/xxx
  → transcripts/YYYYMMDD-{動画ID}.md に字幕保存

ユーザー（Claude Code に依頼）
  → 「transcripts/xxxx.md の字幕をもとに記事を書いて」

Claude Code（自動）
  → src/data/blog/ に記事ファイルを生成

ユーザー
  → 記事を確認・修正 → git push → Netlify が自動デプロイ
```

---

## 参考情報源

- [Deadlock Wiki](https://deadlock.wiki/)
- [Reddit r/DeadlockTheGame](https://www.reddit.com/r/DeadlockTheGame/)
- YouTube: [Eidorian](https://www.youtube.com/@Eidorian510) / [Deathy](https://www.youtube.com/@Deathy) / [MastYT](https://www.youtube.com/@MastYT) / [Midknighttxt](https://www.youtube.com/@Midknighttxt) / [poshypop](https://www.youtube.com/@poshypop)
