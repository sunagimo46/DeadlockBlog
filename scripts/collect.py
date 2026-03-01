"""Deadlock 攻略ブログ — トピック収集メインスクリプト

YouTube / Reddit / Wiki から話題のトピックを収集し、
GitHub Issue として作成する。
"""

import io
import subprocess
import sys
from datetime import datetime, timezone

# Windows 環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from sources.reddit import fetch_hot_posts
from sources.wiki import fetch_recent_changes
from sources.youtube import fetch_recent_videos


def format_youtube_section(videos: list[dict]) -> str:
    """YouTube セクションをMarkdown形式に整形する"""
    if not videos:
        return ""

    lines = ["## YouTube 新着動画\n"]
    for v in videos:
        lines.append(f"- **[{v['title']}]({v['url']})** ({v['channel']})")
    return "\n".join(lines)


def format_reddit_section(posts: list[dict]) -> str:
    """Reddit セクションをMarkdown形式に整形する"""
    if not posts:
        return ""

    lines = ["## Reddit ホット投稿\n"]
    for p in posts:
        lines.append(
            f"- **[{p['title']}]({p['url']})** "
            f"(Score: {p['score']}, Comments: {p['comments']})"
        )
    return "\n".join(lines)


def format_wiki_section(changes: list[dict]) -> str:
    """Wiki セクションをMarkdown形式に整形する"""
    if not changes:
        return ""

    lines = ["## Deadlock Wiki 更新ページ\n"]
    for c in changes:
        lines.append(f"- **[{c['title']}]({c['url']})**")
    return "\n".join(lines)


def build_issue_body(
    videos: list[dict],
    posts: list[dict],
    changes: list[dict],
) -> str:
    """Issue本文を組み立てる"""
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    sections = [
        f"# 本日の話題トピック ({today})\n",
        "以下のトピックから記事にしたいものがあれば、コメントで `@claude ○○の記事を書いて` と指示してください。\n",
    ]

    youtube_section = format_youtube_section(videos)
    reddit_section = format_reddit_section(posts)
    wiki_section = format_wiki_section(changes)

    if youtube_section:
        sections.append(youtube_section)
    if reddit_section:
        sections.append(reddit_section)
    if wiki_section:
        sections.append(wiki_section)

    if not any([youtube_section, reddit_section, wiki_section]):
        sections.append("本日は新しいトピックが見つかりませんでした。")

    return "\n\n".join(sections)


def create_github_issue(title: str, body: str) -> None:
    """gh CLI で GitHub Issue を作成する"""
    result = subprocess.run(
        [
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
            "--label", "topic-collection",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"Issue を作成しました: {result.stdout.strip()}")
    else:
        print(f"Issue の作成に失敗しました: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    print("=== Deadlock トピック収集開始 ===\n")

    print("[1/3] YouTube RSS フィード取得中...")
    videos = fetch_recent_videos(days=3)
    print(f"  → {len(videos)} 件の動画を取得\n")

    print("[2/3] Reddit ホット投稿取得中...")
    posts = fetch_hot_posts(limit=15)
    print(f"  → {len(posts)} 件の投稿を取得\n")

    print("[3/3] Wiki 更新ページ取得中...")
    changes = fetch_recent_changes(days=3)
    print(f"  → {len(changes)} 件の更新を取得\n")

    body = build_issue_body(videos, posts, changes)
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    title = f"本日の話題トピック ({today})"

    # --dry-run モード: Issue作成せずに本文を表示
    if "--dry-run" in sys.argv:
        print("=== Issue プレビュー ===\n")
        print(f"Title: {title}\n")
        print(body)
        return

    create_github_issue(title, body)


if __name__ == "__main__":
    main()
