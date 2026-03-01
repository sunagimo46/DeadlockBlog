"""Deadlock 攻略ブログ — トピック指定型リサーチスクリプト

指定されたトピックに関連する YouTube 動画、Reddit 投稿、Wiki 記事を
検索し、結果を Markdown 形式で出力する。
--issue-number を指定すると GitHub Issue にコメントとして投稿する。
"""

import argparse
import io
import subprocess
import sys

# Windows 環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from sources.reddit import search_posts
from sources.wiki import search_pages
from sources.youtube import search_videos


def format_youtube_section(videos: list[dict]) -> str:
    """YouTube セクションを整形する"""
    if not videos:
        return ""

    lines = ["### YouTube 関連動画\n"]
    for v in videos:
        header = f"- **[{v['title']}]({v['url']})** ({v['channel']}, {v['published'][:10]})"
        lines.append(header)
        transcript = v.get("transcript", "")
        if transcript:
            lines.append(f"  > **字幕（抜粋）**: {transcript}")
    return "\n".join(lines)


def format_reddit_section(posts: list[dict]) -> str:
    """Reddit セクションを整形する"""
    if not posts:
        return ""

    lines = ["### Reddit 関連投稿\n"]
    for p in posts:
        line = (
            f"- **[{p['title']}]({p['url']})** "
            f"(Score: {p['score']}, Comments: {p['comments']})"
        )
        if p.get("selftext"):
            line += f"\n  > {p['selftext']}"
        lines.append(line)
    return "\n".join(lines)


def format_wiki_section(pages: list[dict]) -> str:
    """Wiki セクションを整形する"""
    if not pages:
        return ""

    lines = ["### Deadlock Wiki 関連ページ\n"]
    for page in pages:
        line = f"- **[{page['title']}]({page['url']})**"
        if page.get("snippet"):
            line += f"\n  > {page['snippet']}"
        lines.append(line)
    return "\n".join(lines)


def build_research_body(
    topic: str,
    keywords: str,
    videos: list[dict],
    posts: list[dict],
    pages: list[dict],
) -> str:
    """リサーチ結果をMarkdown形式に組み立てる"""
    sections = [
        f"## リサーチ結果: {topic}\n",
        (
            "以下の参考情報を元に記事を作成できます。\n"
            f"記事を生成するには `@claude この参考情報をもとに「{topic}」の記事を書いて` "
            "とコメントしてください。\n"
        ),
    ]

    youtube_section = format_youtube_section(videos)
    reddit_section = format_reddit_section(posts)
    wiki_section = format_wiki_section(pages)

    if youtube_section:
        sections.append(youtube_section)
    if reddit_section:
        sections.append(reddit_section)
    if wiki_section:
        sections.append(wiki_section)

    if not any([youtube_section, reddit_section, wiki_section]):
        sections.append("関連する情報が見つかりませんでした。キーワードを変えて再度お試しください。")

    sections.append(f"---\n検索キーワード: `{keywords}`")

    return "\n\n".join(sections)


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
        print(f"Issue #{issue_number} にリサーチ結果を投稿しました")
    else:
        print(f"コメント投稿に失敗: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="トピック指定型リサーチスクリプト")
    parser.add_argument("--topic", required=True, help="リサーチテーマ（日本語）")
    parser.add_argument(
        "--keywords",
        default="",
        help="検索キーワード（カンマ区切り、英語検索用）。未指定時は --topic を使用",
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        default=None,
        help="結果をコメントとして投稿する Issue 番号",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Issue 投稿せずにコンソール出力のみ",
    )
    args = parser.parse_args()

    keywords = args.keywords if args.keywords else args.topic

    print(f"=== リサーチ開始: {args.topic} ===\n")
    print(f"検索キーワード: {keywords}\n")

    print("[1/3] YouTube 動画を検索中...")
    videos = search_videos(keywords)
    print(f"  → {len(videos)} 件の関連動画を発見\n")

    print("[2/3] Reddit 投稿を検索中...")
    posts = search_posts(keywords)
    print(f"  → {len(posts)} 件の関連投稿を発見\n")

    print("[3/3] Wiki ページを検索中...")
    pages = search_pages(keywords)
    print(f"  → {len(pages)} 件の関連ページを発見\n")

    body = build_research_body(args.topic, keywords, videos, posts, pages)

    if args.dry_run or args.issue_number is None:
        print("=== リサーチ結果プレビュー ===\n")
        print(body)
        return

    post_issue_comment(args.issue_number, body)


if __name__ == "__main__":
    main()
