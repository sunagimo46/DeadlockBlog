"""Deadlock 攻略ブログ — 記事リクエストIssueの参考URLコンテンツ取得スクリプト

Issue 本文の「### 参考情報」セクションから URL を抽出し、
各 URL のコンテンツ（YouTube 字幕、Reddit 投稿、Wiki ページ）を取得して
Issue にリサーチ結果コメントとして投稿する。

/fetch-refs スラッシュコマンドで実行する。失敗時は再度コマンドを実行することで
リトライできる。
"""

import argparse
import io
import subprocess
import sys
from pathlib import Path

# Windows 環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# generate_article.py の関数を再利用
sys.path.insert(0, str(Path(__file__).parent))
from generate_article import extract_reference_urls, fetch_reference_contents


def fetch_issue_body(issue_number: int) -> str:
    """gh CLI で Issue 本文を取得する"""
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--json", "body", "-q", ".body"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Issue 取得に失敗: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def fetch_issue_topic(issue_number: int) -> str:
    """gh CLI で Issue 本文からトピックを取得する"""
    body = fetch_issue_body(issue_number)

    # 「### 記事のトピック」セクションを抽出
    import re
    m = re.search(r"###\s*記事のトピック\s*\n\n(.+)", body)
    if m:
        return m.group(1).strip()

    # フォールバック: Issue タイトル
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--json", "title", "-q", ".title"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    return f"Issue #{issue_number}"


def build_comment_body(topic: str, reference_content: str) -> str:
    """リサーチ結果コメントを組み立てる"""
    parts = [
        f"## リサーチ結果: {topic}",
        "",
        "Issue の参考情報URLからコンテンツを取得しました。",
        "記事を生成するには `/generate` とコメントしてください。",
        "",
        reference_content,
    ]
    return "\n".join(parts)


def post_issue_comment(issue_number: int, body: str) -> None:
    """gh CLI で Issue にコメントを投稿する"""
    result = subprocess.run(
        [
            "gh", "issue", "comment",
            str(issue_number),
            "--body", body,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"Issue #{issue_number} にコメントを投稿しました")
    else:
        print(f"コメント投稿に失敗: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="記事リクエストIssueの参考URLコンテンツ取得スクリプト")
    parser.add_argument(
        "--issue-number",
        type=int,
        required=True,
        help="対象 Issue 番号",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Issue 投稿せずにコンソール出力のみ",
    )
    args = parser.parse_args()

    print(f"=== 参考URLコンテンツ取得開始: Issue #{args.issue_number} ===\n")

    # Issue 本文を取得
    print("Issue 本文を取得中...")
    issue_body = fetch_issue_body(args.issue_number)

    # 参考URLを抽出
    print("参考URLを抽出中...")
    reference_urls = extract_reference_urls(issue_body)

    total_urls = sum(len(v) for v in reference_urls.values())
    print(f"  → {total_urls} 件のURLを発見")
    for category, urls in reference_urls.items():
        if urls:
            print(f"    - {category}: {len(urls)} 件")

    if total_urls == 0:
        message = (
            "## 参考情報URLが見つかりませんでした\n\n"
            "Issue 本文の「### 参考情報」セクションにURLが記載されていないか、"
            "認識できる形式ではありませんでした。\n\n"
            "対応しているURLの形式:\n"
            "- YouTube: `https://www.youtube.com/watch?v=...` または `https://youtu.be/...`\n"
            "- Reddit: `https://www.reddit.com/r/.../comments/.../`\n"
            "- Deadlock Wiki: `https://deadlock.wiki/wiki/...`"
        )
        if args.dry_run:
            print("\n=== DRY RUN: コメント内容 ===\n")
            print(message)
            return
        post_issue_comment(args.issue_number, message)
        return

    # 各URLのコンテンツを取得
    print("\n参照コンテンツを取得中...")
    reference_content = fetch_reference_contents(reference_urls)

    if not reference_content:
        message = (
            "## 参考情報URLのコンテンツ取得に失敗しました\n\n"
            "URLは見つかりましたが、コンテンツの取得に失敗しました。\n"
            "しばらく待ってから `/fetch-refs` を再実行してください。\n\n"
            f"対象URL数: {total_urls} 件"
        )
        if args.dry_run:
            print("\n=== DRY RUN: コメント内容 ===\n")
            print(message)
            return
        post_issue_comment(args.issue_number, message)
        return

    # トピックを取得
    topic = fetch_issue_topic(args.issue_number)

    # コメント本文を組み立て
    body = build_comment_body(topic, reference_content)

    if args.dry_run:
        print("\n=== DRY RUN: コメント内容 ===\n")
        print(body)
        return

    post_issue_comment(args.issue_number, body)
    print(f"\n=== 完了 ===")


if __name__ == "__main__":
    main()
