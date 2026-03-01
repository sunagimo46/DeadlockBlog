"""YouTube動画の字幕をローカルファイルに保存するスクリプト

使用方法:
    cd scripts
    python fetch_transcript.py --url https://www.youtube.com/watch?v=xxx
    python fetch_transcript.py --url https://youtu.be/xxx --output-dir ../transcripts

事前準備:
    pip install yt-dlp
"""

import argparse
import io
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Windows 環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# scripts/ ディレクトリからの相対インポート
sys.path.insert(0, str(str(Path(__file__).parent)))
from sources.youtube import _extract_video_id

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "transcripts"


def _parse_vtt(vtt_text: str) -> str:
    """WebVTT テキストから重複なしの字幕テキストを抽出する"""
    seen: set[str] = set()
    result_lines: list[str] = []
    for line in vtt_text.split("\n"):
        # タイムスタンプ行・ヘッダー行をスキップ
        if re.match(r"\d{2}:\d{2}", line):
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "align:", "position:")):
            continue
        # HTML タグを除去
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line and line not in seen:
            seen.add(line)
            result_lines.append(line)
    return " ".join(result_lines)


def fetch_transcript(video_url: str) -> tuple[str, str]:
    """yt-dlp を使って字幕とタイトルを取得する。(title, transcript) を返す"""
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        raise RuntimeError(
            "yt-dlp が見つかりません。以下のコマンドでインストールしてください:\n"
            "    pip install yt-dlp"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-auto-sub",
                "--write-sub",
                "--sub-lang", "en",
                "--sub-format", "vtt",
                "--skip-download",
                "--print", "%(title)s",
                "-o", f"{tmpdir}/%(id)s",
                video_url,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp の実行に失敗しました:\n{result.stderr.strip()}")

        title = result.stdout.strip().split("\n")[0] or _extract_video_id(video_url) or video_url

        vtt_files = list(Path(tmpdir).glob("*.vtt"))
        if not vtt_files:
            raise RuntimeError(
                "字幕ファイルが生成されませんでした。\n"
                "この動画には英語の字幕（手動・自動生成）がない可能性があります。"
            )

        transcript = _parse_vtt(vtt_files[0].read_text(encoding="utf-8"))
        return title, transcript


def save_transcript(url: str, output_dir: Path) -> Path:
    """字幕を取得して Markdown ファイルに保存する。保存したファイルパスを返す"""
    video_id = _extract_video_id(url)
    if not video_id:
        raise ValueError(f"有効なYouTube URLではありません: {url}")

    print(f"動画ID: {video_id}")
    print("字幕を取得中（yt-dlp）...")
    title, transcript_text = fetch_transcript(url)
    print(f"タイトル: {title}")
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
    parser = argparse.ArgumentParser(description="YouTube動画の字幕をローカルファイルに保存（yt-dlp使用）")
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
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
