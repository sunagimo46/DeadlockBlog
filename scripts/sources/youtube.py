"""YouTube RSS フィードからDeadlock関連動画を取得するモジュール"""

import re
from datetime import datetime, timedelta, timezone

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

CHANNELS = {
    "Eidorian": "UCLS1nZT0SEqZcEWKYAllFRg",
    "Deathy": "UCj929zzQbCYGBAUX0Tod4Eg",
    "MastYT": "UCU0oLTV2RO-l4uUkQVy2TvA",
    "Midknighttxt": "UCPAdg0t1CEuMRTzbzRHMCXw",
    "poshypop": "UCrZR30NWLNLJfswlYA_mOrA",
}

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

# 字幕の取得言語の優先順位
TRANSCRIPT_LANGUAGES = ["en", "en-US", "en-GB", "ja"]

# 字幕を要約する文字数の上限（Claude に渡す量を制限）
TRANSCRIPT_MAX_CHARS = 3000


def _extract_video_id(url: str) -> str | None:
    """YouTube URL から動画 ID を抽出する"""
    match = re.search(r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def fetch_transcript(video_url: str) -> str:
    """動画の字幕テキストを取得して結合する。取得できない場合は空文字を返す"""
    video_id = _extract_video_id(video_url)
    if not video_id:
        return ""

    try:
        # youtube-transcript-api 1.0+ はインスタンスメソッド api.list() を使用
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # 優先言語順に字幕を試みる
        transcript = None
        for lang in TRANSCRIPT_LANGUAGES:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        # 見つからない場合は自動生成字幕を使う
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(TRANSCRIPT_LANGUAGES)
            except NoTranscriptFound:
                # それでも見つからなければ最初に見つかるものを使う
                transcript = next(iter(transcript_list), None)

        if transcript is None:
            return ""

        snippets = transcript.fetch()
        # 1.0+ はオブジェクト(snippet.text)、旧版はdict(snippet["text"])を返す
        def _get_text(s: object) -> str:
            return s.text if hasattr(s, "text") else s["text"]  # type: ignore[attr-defined]

        full_text = " ".join(_get_text(s) for s in snippets)

        # 上限文字数でトリム
        if len(full_text) > TRANSCRIPT_MAX_CHARS:
            full_text = full_text[:TRANSCRIPT_MAX_CHARS] + "…（以下省略）"

        return full_text

    except (TranscriptsDisabled, NoTranscriptFound):
        return ""
    except Exception as e:
        print(f"[YouTube] 字幕取得エラー ({video_url}): {e}")
        return ""


def fetch_recent_videos(days: int = 3) -> list[dict]:
    """各チャンネルから指定日数以内の動画を取得する"""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    videos = []

    for name, channel_id in CHANNELS.items():
        try:
            feed = feedparser.parse(RSS_URL.format(channel_id=channel_id))
            for entry in feed.entries:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if published < cutoff:
                    continue
                videos.append({
                    "source": "YouTube",
                    "channel": name,
                    "title": entry.title,
                    "url": entry.link,
                    "published": published.isoformat(),
                    "transcript": "",
                })
        except Exception as e:
            print(f"[YouTube] {name} の取得に失敗: {e}")

    return videos


def search_videos(query: str, days: int = 90) -> list[dict]:
    """各チャンネルのRSSフィードからキーワードに一致する動画を検索し、字幕も取得する"""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    keywords = [kw.strip().lower() for kw in query.split(",") if kw.strip()]
    videos = []

    for name, channel_id in CHANNELS.items():
        try:
            feed = feedparser.parse(RSS_URL.format(channel_id=channel_id))
            for entry in feed.entries:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if published < cutoff:
                    continue
                title_lower = entry.title.lower()
                if any(kw in title_lower for kw in keywords):
                    print(f"  [YouTube] 字幕取得中: {entry.title}")
                    transcript = fetch_transcript(entry.link)
                    videos.append({
                        "source": "YouTube",
                        "channel": name,
                        "title": entry.title,
                        "url": entry.link,
                        "published": published.isoformat(),
                        "transcript": transcript,
                    })
        except Exception as e:
            print(f"[YouTube] {name} の検索に失敗: {e}")

    return videos
