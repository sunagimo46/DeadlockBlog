"""Deadlock 攻略ブログ — Claude API を使った記事生成スクリプト

GitHub Issue の情報とリサーチ結果を元に Claude API で記事を生成し、
PR を作成して Issue に通知する。

環境変数:
    ANTHROPIC_API_KEY  : Claude API 認証キー
    GH_TOKEN           : GitHub API 操作トークン（GITHUB_TOKEN から自動取得）
    GITHUB_REPOSITORY  : リポジトリ名（例: username/repo）
    ISSUE_NUMBER       : 対象 Issue 番号
    EVENT_NAME         : トリガーイベント種別
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import anthropic
import requests
import yaml

from sources.youtube import fetch_transcript
from sources.reddit import fetch_post_by_url
from sources.wiki import fetch_page_by_url


# --- バリデーション ---

def validate_repo_name(repo: str) -> str:
    """リポジトリ名が owner/repo 形式であることを検証する"""
    if not re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", repo):
        raise ValueError(f"無効なリポジトリ名です: {repo}")
    return repo


def is_authorized_user(issue: dict, repo: str, token: str) -> bool:
    """Issue 作成者がリポジトリのコラボレーターかどうか確認する"""
    author = issue.get("user", {}).get("login", "")
    if not author:
        return False
    url = f"https://api.github.com/repos/{repo}/collaborators/{author}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers, timeout=30)
    return response.status_code == 204


def sanitize_pub_date(pub_date_value) -> str:
    """pubDate を YYYY-MM-DD 形式の文字列に正規化する。不正な値は今日の日付にフォールバック。"""
    if hasattr(pub_date_value, "isoformat"):
        pub_date_str = pub_date_value.isoformat()
    else:
        pub_date_str = str(pub_date_value)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", pub_date_str):
        return date.today().isoformat()
    return pub_date_str


# --- Issue / コメント取得 ---

def fetch_issue_data(repo: str, issue_number: int, token: str) -> dict:
    """GitHub API で Issue の詳細を取得する"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_issue_comments(repo: str, issue_number: int, token: str) -> list[dict]:
    """GitHub API で Issue のコメント一覧を取得する"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


# --- プロンプト構築 ---

def load_claude_md() -> str:
    """CLAUDE.md をプロジェクトルートから読み込む"""
    claude_md_path = Path(__file__).parent.parent / "CLAUDE.md"
    if claude_md_path.exists():
        return claude_md_path.read_text(encoding="utf-8")
    return ""


def extract_research_comments(comments: list[dict]) -> str:
    """「## リサーチ結果:」ヘッダーを含むコメントを抽出・結合する"""
    research_parts = []
    for comment in comments:
        body = comment.get("body", "")
        if "## リサーチ結果:" in body:
            research_parts.append(body)
    return "\n\n---\n\n".join(research_parts)


def extract_reference_urls(issue_body: str) -> dict[str, list[str]]:
    """Issue 本文の「### 参考情報」セクションから URL を抽出して分類する"""
    result: dict[str, list[str]] = {"youtube": [], "reddit": [], "wiki": [], "other": []}

    # 「### 参考情報」セクションを切り出す
    if "### 参考情報" not in issue_body:
        return result

    section = issue_body.split("### 参考情報", 1)[1]
    # 次の「### 」が出るまでのテキストのみ対象
    next_section = re.search(r"\n###\s+", section)
    if next_section:
        section = section[: next_section.start()]

    # URL を抽出
    urls = re.findall(r"https?://[^\s\)\]>」。、]+", section)

    for url in urls:
        if "youtube.com/watch" in url or "youtu.be/" in url:
            result["youtube"].append(url)
        elif "reddit.com/r/" in url and "/comments/" in url:
            result["reddit"].append(url)
        elif "deadlock.wiki/wiki/" in url:
            result["wiki"].append(url)
        else:
            result["other"].append(url)

    return result


def fetch_reference_contents(urls: dict[str, list[str]]) -> str:
    """各 URL のコンテンツを取得して Markdown 形式で結合する"""
    parts: list[str] = []

    for url in urls.get("youtube", []):
        content = fetch_transcript(url)
        if content:
            parts.append(f"### YouTube 動画の字幕\n\nURL: {url}\n\n{content}")

    for url in urls.get("reddit", []):
        content = fetch_post_by_url(url)
        if content:
            parts.append(f"### Reddit 投稿\n\nURL: {url}\n\n{content}")

    for url in urls.get("wiki", []):
        content = fetch_page_by_url(url)
        if content:
            parts.append(f"### Deadlock Wiki ページ\n\nURL: {url}\n\n{content}")

    if urls.get("other"):
        other_urls = "\n".join(f"- {url}" for url in urls["other"])
        parts.append(f"### その他の参考 URL\n\n{other_urls}")

    return "\n\n---\n\n".join(parts)


def build_prompt(
    issue: dict,
    comments: list[dict],
    claude_md: str,
) -> str:
    """Claude API へのプロンプトを構築する"""
    issue_title = issue.get("title", "")
    issue_body = issue.get("body", "") or ""
    issue_labels = [label["name"] for label in issue.get("labels", [])]

    # リサーチ結果コメントを抽出
    research_content = extract_research_comments(comments)

    # Issue 本文の参照 URL からコンテンツを取得
    print("参照コンテンツを取得中...")
    reference_urls = extract_reference_urls(issue_body)
    reference_content = fetch_reference_contents(reference_urls)

    # ユーザーの指示コメント（@claude を含む）を収集
    instruction_comments = [
        c["body"] for c in comments if "@claude" in c.get("body", "")
    ]

    prompt_parts = [
        "# 記事生成指示",
        "",
        "以下のプロジェクトガイドラインと Issue 情報を元に、Deadlock 攻略ブログの記事を生成してください。",
        "",
        "## プロジェクトガイドライン (CLAUDE.md)",
        "",
        claude_md,
        "",
        "## Issue 情報",
        "",
        f"**タイトル**: {issue_title}",
        f"**ラベル**: {', '.join(issue_labels) if issue_labels else 'なし'}",
        "",
        "**Issue 本文**:",
        issue_body,
    ]

    if instruction_comments:
        prompt_parts += [
            "",
            "## ユーザーからの指示",
            "",
        ]
        for i, comment in enumerate(instruction_comments, 1):
            prompt_parts += [f"### 指示 {i}", comment, ""]

    if reference_content:
        prompt_parts += [
            "",
            "## 参照コンテンツ",
            "",
            reference_content,
        ]

    if research_content:
        prompt_parts += [
            "",
            "## リサーチ結果（参考情報）",
            "",
            research_content,
        ]
    elif not reference_content:
        prompt_parts += [
            "",
            "## リサーチ結果",
            "",
            "リサーチ結果はありません。Issue 本文とユーザー指示のみを参考にして記事を作成してください。",
        ]

    prompt_parts += [
        "",
        "## 出力フォーマット",
        "",
        "最初の行にスラッグを出力してください（コードブロックなし、この行は記事本文には含めない）:",
        "SLUG: <英数字とハイフンのみ、例: mcginnis-hero-guide>",
        "",
        "その後、以下のフロントマターと記事本文をそのまま出力してください（コードブロックで囲まない）:",
        "",
        "---",
        "title: \"記事タイトル\"",
        "description: \"記事の概要（120文字程度）\"",
        "pubDate: YYYY-MM-DD",
        "tags: [\"タグ1\", \"タグ2\"]",
        "category: \"カテゴリ値\"",
        "draft: false",
        "---",
        "",
        "記事本文...",
        "",
        "**注意事項**:",
        "- pubDate は本日の日付を使用してください",
        "- category は hero-guide / patch-notes / tactics のいずれかを使用",
        "- ヒーロー攻略記事の場合は hero フィールドも追加",
        "- 見出しは h2（##）から開始し、h1 は使わない",
        "- ですます調で日本語で記載",
        "- 初心者〜中級者向けの実戦的な内容",
        "- コードブロック（```）で出力全体を囲まないこと",
        f"- 今日の日付: {date.today().isoformat()}",
    ]

    return "\n".join(prompt_parts)


# --- 記事生成 ---

def strip_code_fences(text: str) -> str:
    """Claude 出力から Markdown コードフェンスを除去する"""
    text = text.strip()
    text = re.sub(r"^```(?:markdown)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text


def generate_article(prompt: str, api_key: str) -> str:
    """Claude API を呼び出して記事を生成する"""
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16384,
        messages=[{"role": "user", "content": prompt}],
    )
    if message.stop_reason == "max_tokens":
        raise RuntimeError(
            "Claude API の出力がトークン上限に達しました。生成された記事が不完全です。"
        )
    return message.content[0].text


# --- フロントマター処理 ---

def extract_slug(raw_text: str) -> tuple[str, str]:
    """先頭行の SLUG: <value> を抽出し、残りのテキストを返す"""
    lines = raw_text.strip().splitlines()

    slug = ""
    start_index = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("SLUG:"):
            slug = stripped.removeprefix("SLUG:").strip()
            # 英数字とハイフンのみに正規化
            slug = re.sub(r"[^a-zA-Z0-9-]", "-", slug).strip("-").lower()
            start_index = i + 1
            break

    remaining = "\n".join(lines[start_index:]).strip()
    return slug, remaining


def parse_frontmatter(article_text: str) -> dict:
    """記事テキストからフロントマターを解析する"""
    match = re.match(r"^---\n(.*?)\n---", article_text, re.DOTALL)
    if not match:
        return {}

    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def validate_frontmatter(frontmatter: dict) -> list[str]:
    """フロントマターの必須項目とカテゴリ値を検証し、不足項目リストを返す"""
    required_fields = ["title", "description", "pubDate", "tags", "category", "draft"]
    valid_categories = {"hero-guide", "patch-notes", "tactics"}

    errors = []
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"必須フィールド '{field}' が不足しています")

    if "category" in frontmatter and frontmatter["category"] not in valid_categories:
        errors.append(
            f"カテゴリ '{frontmatter['category']}' は無効です。"
            f"有効値: {', '.join(valid_categories)}"
        )

    return errors


def add_draft_to_frontmatter(article_text: str) -> str:
    """フロントマターに draft: true を追加する（draft フィールドが存在しない場合）"""
    match = re.match(r"^(---\n)(.*?)(\n---)", article_text, re.DOTALL)
    if match:
        return (
            f"{match.group(1)}{match.group(2)}\ndraft: true"
            f"{match.group(3)}{article_text[match.end():]}"
        )
    return article_text


def apply_draft_fallback(article_text: str) -> str:
    """draft フラグが false の場合は true に変更し、存在しない場合は追加する"""
    if "draft:" in article_text:
        return re.sub(r"(draft:\s*)false", r"\1true", article_text)
    return add_draft_to_frontmatter(article_text)


# --- ファイル書き込み ---

def write_article_file(article_text: str, slug: str, pub_date: str) -> Path:
    """src/data/blog/YYYY-MM-DD-slug.md に記事を書き込む"""
    blog_dir = Path(__file__).parent.parent / "src" / "data" / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)

    # スラッグとファイル名のパストラバーサル防御
    safe_slug = re.sub(r"[^a-zA-Z0-9-]", "", slug) or f"article"
    safe_date = pub_date if re.match(r"^\d{4}-\d{2}-\d{2}$", pub_date) else date.today().isoformat()

    filename = f"{safe_date}-{safe_slug}.md"
    file_path = blog_dir / filename
    file_path.write_text(article_text, encoding="utf-8")
    print(f"記事ファイルを作成しました: {file_path}")
    return file_path


# --- PR 作成 ---

def create_pr(
    file_path: Path,
    issue_number: int,
    issue_title: str,
    slug: str,
) -> str:
    """git commit + push + gh pr create で PR を作成し、PR URL を返す"""
    branch_name = f"article/{slug}-issue-{issue_number}"

    # リモートブランチが残っている場合は削除（再実行時の競合対策）
    _run_git_optional(["push", "origin", "--delete", branch_name])

    # ブランチ作成
    _run_git(["checkout", "-b", branch_name])

    # ファイルをステージング
    _run_git(["add", str(file_path)])

    # コミット
    commit_message = f"feat: {issue_title} (Issue #{issue_number})"
    _run_git(["commit", "-m", commit_message])

    # プッシュ
    _run_git(["push", "-u", "origin", branch_name])

    # PR 作成
    pr_title = f"feat: {issue_title}"
    pr_body = (
        f"## 概要\n\n"
        f"Issue #{issue_number} の記事を生成しました。\n\n"
        f"## 変更ファイル\n\n"
        f"- `{file_path.relative_to(Path(__file__).parent.parent)}`\n\n"
        f"## 確認事項\n\n"
        f"- [ ] フロントマターの必須項目が揃っているか\n"
        f"- [ ] 記事内容が正確か\n"
        f"- [ ] 日本語が自然か\n\n"
        f"Closes #{issue_number}"
    )

    result = subprocess.run(
        ["gh", "pr", "create", "--title", pr_title, "--body", pr_body],
        capture_output=True,
        text=True,
        check=True,
    )
    pr_url = result.stdout.strip()
    print(f"PR を作成しました: {pr_url}")
    return pr_url


def _run_git(args: list[str]) -> None:
    """git コマンドを実行する（失敗時は CalledProcessError を raise）"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            ["git"] + args,
            result.stdout,
            result.stderr,
        )
    if result.stdout:
        print(f"git {args[0]}: {result.stdout.strip()}")


def _run_git_optional(args: list[str]) -> None:
    """git コマンドを実行する（失敗しても無視する）"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(f"git {args[0]}: {result.stdout.strip()}")


# --- Issue コメント通知 ---

def post_issue_comment(
    repo: str,
    issue_number: int,
    body: str,
    token: str,
) -> None:
    """GitHub API で Issue にコメントを投稿する"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.post(url, headers=headers, json={"body": body}, timeout=30)
    response.raise_for_status()
    print(f"Issue #{issue_number} にコメントを投稿しました")


# --- メイン処理 ---

def main() -> None:
    parser = argparse.ArgumentParser(description="Claude API を使った記事生成スクリプト")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ファイル書き込み・PR 作成・Issue コメントをスキップして内容を確認する",
    )
    args = parser.parse_args()

    # 環境変数の読み込み
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    token = os.environ.get("GH_TOKEN", "")
    repo_raw = os.environ.get("GITHUB_REPOSITORY", "")
    issue_number_str = os.environ.get("ISSUE_NUMBER", "")

    # 必須パラメータの検証
    missing = []
    if not api_key:
        missing.append("ANTHROPIC_API_KEY")
    if not token:
        missing.append("GH_TOKEN")
    if not repo_raw:
        missing.append("GITHUB_REPOSITORY")
    if not issue_number_str:
        missing.append("ISSUE_NUMBER")

    if missing:
        print(f"エラー: 必須環境変数が未設定です: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # リポジトリ名の形式検証
    try:
        repo = validate_repo_name(repo_raw)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    # Issue 番号の整数変換
    try:
        issue_number = int(issue_number_str)
    except ValueError:
        print(
            f"エラー: ISSUE_NUMBER '{issue_number_str}' は有効な整数ではありません",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        # Issue データの取得
        print(f"Issue #{issue_number} の情報を取得中...")
        issue = fetch_issue_data(repo, issue_number, token)
        comments = fetch_issue_comments(repo, issue_number, token)
        print(f"  タイトル: {issue.get('title', '')}")
        print(f"  コメント数: {len(comments)}")

        # 権限チェック（dry-run 時はスキップ）
        if not args.dry_run and not is_authorized_user(issue, repo, token):
            print(
                "権限のないユーザーからの Issue です。処理をスキップします。",
                file=sys.stderr,
            )
            sys.exit(0)

        # CLAUDE.md の読み込み
        claude_md = load_claude_md()

        # プロンプト構築
        print("プロンプトを構築中...")
        prompt = build_prompt(issue, comments, claude_md)

        if args.dry_run:
            print("\n=== DRY RUN: プロンプト内容 ===\n")
            print(prompt[:2000] + ("..." if len(prompt) > 2000 else ""))
            print("\n=== DRY RUN 終了（記事生成をスキップ）===")
            return

        # 記事生成
        print("Claude API で記事を生成中...")
        raw_output = generate_article(prompt, api_key)

        # コードフェンスを除去してからスラッグ抽出
        cleaned_output = strip_code_fences(raw_output)
        slug, article_text = extract_slug(cleaned_output)
        if not slug:
            slug = f"article-issue-{issue_number}"
            print(f"スラッグが取得できなかったためデフォルト値を使用: {slug}")

        # フロントマター検証
        frontmatter = parse_frontmatter(article_text)
        validation_errors = validate_frontmatter(frontmatter)

        pub_date = sanitize_pub_date(frontmatter.get("pubDate", date.today()))

        if validation_errors:
            print("フロントマターに問題があります（draft: true として続行）:")
            for error in validation_errors:
                print(f"  - {error}")
            article_text = apply_draft_fallback(article_text)

        # ファイル書き込み
        file_path = write_article_file(article_text, slug, pub_date)

        # PR 作成
        issue_title = issue.get("title", f"Issue #{issue_number}")
        pr_url = create_pr(file_path, issue_number, issue_title, slug)

        # 成功通知
        success_message = (
            f"## 記事生成が完了しました\n\n"
            f"**ファイル**: `{file_path.name}`\n"
            f"**PR**: {pr_url}\n\n"
        )
        if validation_errors:
            success_message += (
                "**注意**: フロントマターに問題があったため `draft: true` で保存しました。\n"
                "PR でご確認の上、修正してください。\n\n"
                "問題の詳細:\n"
                + "\n".join(f"- {e}" for e in validation_errors)
            )

        post_issue_comment(repo, issue_number, success_message, token)

    except requests.HTTPError as e:
        # エラー詳細はログのみに出力し、Issue への通知は概要のみ
        print(f"GitHub API エラー詳細: {e}", file=sys.stderr)
        error_message = (
            "## 記事生成に失敗しました\n\n"
            "**エラー種別**: GitHub API エラー\n"
            "詳細は GitHub Actions のログを確認してください。\n"
        )
        _try_post_error(repo, issue_number, error_message, token)
        sys.exit(1)

    except anthropic.APIError as e:
        print(f"Claude API エラー詳細: {e}", file=sys.stderr)
        error_message = (
            "## 記事生成に失敗しました\n\n"
            "**エラー種別**: Claude API エラー\n"
            "詳細は GitHub Actions のログを確認してください。\n"
        )
        _try_post_error(repo, issue_number, error_message, token)
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"Git / PR 作成エラー詳細: {e}\nstderr: {e.stderr}", file=sys.stderr)
        error_message = (
            "## 記事生成に失敗しました\n\n"
            "**エラー種別**: Git / PR 作成エラー\n"
            "詳細は GitHub Actions のログを確認してください。\n"
        )
        _try_post_error(repo, issue_number, error_message, token)
        sys.exit(1)

    except RuntimeError as e:
        print(f"実行時エラー詳細: {e}", file=sys.stderr)
        error_message = (
            "## 記事生成に失敗しました\n\n"
            "**エラー種別**: 実行時エラー\n"
            "詳細は GitHub Actions のログを確認してください。\n"
        )
        _try_post_error(repo, issue_number, error_message, token)
        sys.exit(1)


def _try_post_error(
    repo: str,
    issue_number: int,
    message: str,
    token: str,
) -> None:
    """エラー時に Issue コメント投稿を試みる（失敗しても終了させない）"""
    try:
        post_issue_comment(repo, issue_number, message, token)
    except Exception as e:
        print(f"Issue コメント投稿も失敗しました: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
