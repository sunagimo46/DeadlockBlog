"""YouTube動画の字幕をローカルファイルに保存するスクリプト

使用方法:
    cd scripts
    python fetch_transcript.py --url https://www.youtube.com/watch?v=xxx
    python fetch_transcript.py --url https://youtu.be/xxx --output-dir ../transcripts
"""

import argparse
import io
import sys
from datetime import datetime
from pathlib import Path

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

# Windows 環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# scripts/ ディレクトリからの相対インポート
sys.path.insert(0, str(Path(__file__).parent))
from sources.youtube import TRANSCRIPT_LANGUAGES, _extract_video_id

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "transcripts"


def fetch_video_title(video_id: str) -> str:
    """YouTubeページからog:titleを取得する。失敗時は動画IDを返す"""
    try:
        response = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=10,
        )
        # og:title または meta[name=title] からタイトルを抽出
        import re
        match = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
        if not match:
            match = re.search(r'<title>([^<]+)</title>', response.text)
        if match:
            title = match.group(1)
            # YouTubeページの場合 " - YouTube" サフィックスを除去
            title = re.sub(r"\s*-\s*YouTube\s*$", "", title)
            return title.strip()
    except Exception as e:
        print(f"  タイトル取得に失敗（スキップ）: {e}")
    return video_id


def fetch_full_transcript(video_id: str) -> str:
    """全文字幕を取得する（文字数制限なし）"""
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)

    # 優先言語順に字幕を取得
    transcript = None
    for lang in TRANSCRIPT_LANGUAGES:
        try:
            transcript = transcript_list.find_transcript([lang])
            break
        except NoTranscriptFound:
            continue

    # 手動字幕がなければ自動生成字幕を試みる
    if transcript is None:
        try:
            transcript = transcript_list.find_generated_transcript(TRANSCRIPT_LANGUAGES)
        except NoTranscriptFound:
            # それでもなければ最初に見つかるものを使う
            transcript = next(iter(transcript_list), None)

    if transcript is None:
        raise NoTranscriptFound(video_id, TRANSCRIPT_LANGUAGES, [])

    snippets = transcript.fetch()

    def get_text(s: object) -> str:
        return s.text if hasattr(s, "text") else s["text"]  # type: ignore[attr-defined]

    return " ".join(get_text(s) for s in snippets)


def save_transcript(url: str, output_dir: Path) -> Path:
    """字幕を取得してMarkdownファイルに保存する。保存したファイルパスを返す"""
    video_id = _extract_video_id(url)
    if not video_id:
        raise ValueError(f"有効なYouTube URLではありません: {url}")

    print(f"動画ID: {video_id}")
    print("タイトルを取得中...")
    title = fetch_video_title(video_id)
    print(f"タイトル: {title}")

    print("字幕を取得中...")
    transcript_text = fetch_full_transcript(video_id)
    print(f"字幕取得完了: {len(transcript_text)} 文字")

    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{date_str}-{video_id}.md"
    output_path = output_dir / filename

    content = f"""# YouTube字幕: {title}

**URL**: {url}
**動画ID**: `{video_id}`
**取得日時**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 字幕テキスト

{transcript_text}
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube動画の字幕をローカルファイルに保存")
    parser.add_argument("--url", required=True, help="YouTube動画のURL")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"出力先ディレクトリ（デフォルト: {DEFAULT_OUTPUT_DIR}）",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    try:
        output_path = save_transcript(args.url, output_dir)
        print(f"\n保存完了: {output_path}")
        print("\n--- 次のステップ ---")
        print("Claude Code で以下のように記事作成を依頼できます:")
        print(f'  "{output_path.name} の字幕をもとにDeadlock攻略記事を作成してください"')
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except TranscriptsDisabled:
        print(f"エラー: この動画は字幕が無効になっています", file=sys.stderr)
        sys.exit(1)
    except NoTranscriptFound:
        print(f"エラー: 字幕が見つかりませんでした（英語・日本語字幕が存在しない可能性があります）", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
