"""scripts/sources/youtube.py の字幕取得機能のテスト"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from scripts.sources.youtube import (
    TRANSCRIPT_MAX_CHARS,
    _extract_video_id,
    fetch_recent_videos,
    fetch_transcript,
    search_videos,
)


# ---------------------------------------------------------------------------
# _extract_video_id
# ---------------------------------------------------------------------------


class TestExtractVideoId:
    """_extract_video_id: 各種URLフォーマットから動画IDを抽出する"""

    def test_standard_watch_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_youtu_be_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PLxxx"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self):
        url = "https://www.youtube.com/v/dQw4w9WgXcQ"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url_returns_none(self):
        assert _extract_video_id("https://example.com/video") is None

    def test_empty_string_returns_none(self):
        assert _extract_video_id("") is None

    def test_plain_text_returns_none(self):
        assert _extract_video_id("not a url at all") is None


# ---------------------------------------------------------------------------
# fetch_transcript
# ---------------------------------------------------------------------------


class TestFetchTranscript:
    """fetch_transcript: 字幕テキストの取得"""

    def _make_snippet(self, text: str) -> dict:
        return {"text": text, "start": 0.0, "duration": 1.0}

    @patch("scripts.sources.youtube.YouTubeTranscriptApi")
    def test_returns_transcript_text(self, mock_api):
        """字幕が正常に取得できる場合、連結したテキストを返す"""
        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [
            self._make_snippet("Hello "),
            self._make_snippet("world"),
        ]
        mock_list = MagicMock()
        mock_list.find_transcript.return_value = mock_transcript
        mock_api.list_transcripts.return_value = mock_list

        result = fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert result == "Hello  world"

    @patch("scripts.sources.youtube.YouTubeTranscriptApi")
    def test_truncates_long_transcript(self, mock_api):
        """TRANSCRIPT_MAX_CHARS を超える字幕は省略記号付きでトリムされる"""
        long_text = "a" * (TRANSCRIPT_MAX_CHARS + 100)
        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [self._make_snippet(long_text)]
        mock_list = MagicMock()
        mock_list.find_transcript.return_value = mock_transcript
        mock_api.list_transcripts.return_value = mock_list

        result = fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert len(result) == TRANSCRIPT_MAX_CHARS + len("…（以下省略）")
        assert result.endswith("…（以下省略）")

    @patch("scripts.sources.youtube.YouTubeTranscriptApi")
    def test_fallback_to_generated_transcript(self, mock_api):
        """手動字幕が見つからない場合、自動生成字幕にフォールバックする"""
        from youtube_transcript_api._errors import NoTranscriptFound

        mock_generated = MagicMock()
        mock_generated.fetch.return_value = [self._make_snippet("auto caption")]
        mock_list = MagicMock()
        mock_list.find_transcript.side_effect = NoTranscriptFound("vid", [], [])
        mock_list.find_generated_transcript.return_value = mock_generated
        mock_api.list_transcripts.return_value = mock_list

        result = fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert result == "auto caption"

    @patch("scripts.sources.youtube.YouTubeTranscriptApi")
    def test_fallback_to_first_available(self, mock_api):
        """自動生成字幕も見つからない場合、最初に利用できる字幕を使う"""
        from youtube_transcript_api._errors import NoTranscriptFound

        mock_fallback = MagicMock()
        mock_fallback.fetch.return_value = [self._make_snippet("fallback")]
        mock_list = MagicMock()
        mock_list.find_transcript.side_effect = NoTranscriptFound("vid", [], [])
        mock_list.find_generated_transcript.side_effect = NoTranscriptFound(
            "vid", [], []
        )
        mock_list.__iter__ = MagicMock(return_value=iter([mock_fallback]))
        mock_api.list_transcripts.return_value = mock_list

        result = fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert result == "fallback"

    @patch("scripts.sources.youtube.YouTubeTranscriptApi")
    def test_no_transcript_available_returns_empty(self, mock_api):
        """どの字幕も存在しない場合は空文字を返す"""
        from youtube_transcript_api._errors import NoTranscriptFound

        mock_list = MagicMock()
        mock_list.find_transcript.side_effect = NoTranscriptFound("vid", [], [])
        mock_list.find_generated_transcript.side_effect = NoTranscriptFound(
            "vid", [], []
        )
        mock_list.__iter__ = MagicMock(return_value=iter([]))
        mock_api.list_transcripts.return_value = mock_list

        result = fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert result == ""

    @patch("scripts.sources.youtube.YouTubeTranscriptApi")
    def test_transcripts_disabled_returns_empty(self, mock_api):
        """字幕が無効な動画の場合は空文字を返す"""
        from youtube_transcript_api._errors import TranscriptsDisabled

        mock_api.list_transcripts.side_effect = TranscriptsDisabled("vid")

        result = fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert result == ""

    def test_invalid_url_returns_empty(self):
        """動画IDを抽出できないURLの場合は空文字を返す（APIを呼ばない）"""
        result = fetch_transcript("https://example.com/not-a-video")
        assert result == ""

    @patch("scripts.sources.youtube.YouTubeTranscriptApi")
    def test_unexpected_exception_returns_empty(self, mock_api):
        """想定外の例外が発生した場合も空文字を返す"""
        mock_api.list_transcripts.side_effect = RuntimeError("network error")

        result = fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert result == ""


# ---------------------------------------------------------------------------
# fetch_recent_videos
# ---------------------------------------------------------------------------


class TestFetchRecentVideos:
    """fetch_recent_videos: 直近の動画一覧取得"""

    def _make_entry(self, title: str, days_ago: int = 1):
        """feedparser エントリのスタブを生成する"""
        from datetime import timedelta

        published = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
        entry = MagicMock()
        entry.title = title
        entry.link = f"https://www.youtube.com/watch?v={'X' * 11}"
        entry.published_parsed = published.timetuple()[:6]
        return entry

    @patch("scripts.sources.youtube.feedparser")
    def test_returns_videos_within_days(self, mock_feedparser):
        """期間内の動画が正しく返される"""
        mock_feed = MagicMock()
        mock_feed.entries = [self._make_entry("Recent Video", days_ago=1)]
        mock_feedparser.parse.return_value = mock_feed

        result = fetch_recent_videos(days=3)

        assert len(result) > 0
        assert result[0]["title"] == "Recent Video"
        assert result[0]["source"] == "YouTube"

    @patch("scripts.sources.youtube.feedparser")
    def test_excludes_old_videos(self, mock_feedparser):
        """期間外の動画は含まれない"""
        mock_feed = MagicMock()
        mock_feed.entries = [self._make_entry("Old Video", days_ago=10)]
        mock_feedparser.parse.return_value = mock_feed

        result = fetch_recent_videos(days=3)

        assert result == []

    @patch("scripts.sources.youtube.feedparser")
    def test_handles_fetch_error_gracefully(self, mock_feedparser):
        """チャンネル取得時にエラーが起きても他のチャンネルを処理する"""
        mock_feedparser.parse.side_effect = Exception("connection error")

        result = fetch_recent_videos(days=3)

        assert result == []

    @patch("scripts.sources.youtube.feedparser")
    def test_result_has_required_keys(self, mock_feedparser):
        """取得結果に必要なキーが全て含まれる"""
        mock_feed = MagicMock()
        mock_feed.entries = [self._make_entry("Video", days_ago=1)]
        mock_feedparser.parse.return_value = mock_feed

        result = fetch_recent_videos(days=3)

        required_keys = {"source", "channel", "title", "url", "published", "transcript"}
        for video in result:
            assert required_keys.issubset(video.keys())

    @patch("scripts.sources.youtube.feedparser")
    def test_transcript_is_empty_string(self, mock_feedparser):
        """fetch_recent_videos では字幕は取得せず空文字のまま"""
        mock_feed = MagicMock()
        mock_feed.entries = [self._make_entry("Video", days_ago=1)]
        mock_feedparser.parse.return_value = mock_feed

        result = fetch_recent_videos(days=3)

        for video in result:
            assert video["transcript"] == ""


# ---------------------------------------------------------------------------
# search_videos
# ---------------------------------------------------------------------------


class TestSearchVideos:
    """search_videos: キーワード検索と字幕取得"""

    def _make_entry(self, title: str, days_ago: int = 10):
        from datetime import timedelta

        published = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
        entry = MagicMock()
        entry.title = title
        entry.link = f"https://www.youtube.com/watch?v={'Y' * 11}"
        entry.published_parsed = published.timetuple()[:6]
        return entry

    @patch("scripts.sources.youtube.fetch_transcript", return_value="dummy transcript")
    @patch("scripts.sources.youtube.feedparser")
    def test_matches_keyword_in_title(self, mock_feedparser, mock_transcript):
        """クエリに一致するタイトルの動画が返される"""
        mock_feed = MagicMock()
        mock_feed.entries = [self._make_entry("Deadlock guide for beginners")]
        mock_feedparser.parse.return_value = mock_feed

        result = search_videos("deadlock", days=90)

        assert len(result) > 0
        assert "Deadlock" in result[0]["title"]

    @patch("scripts.sources.youtube.fetch_transcript", return_value="dummy transcript")
    @patch("scripts.sources.youtube.feedparser")
    def test_fetches_transcript_for_matched_video(self, mock_feedparser, mock_transcript):
        """一致した動画の字幕が取得される"""
        mock_feed = MagicMock()
        mock_feed.entries = [self._make_entry("Deadlock tips")]
        mock_feedparser.parse.return_value = mock_feed

        result = search_videos("deadlock", days=90)

        for video in result:
            assert video["transcript"] == "dummy transcript"

    @patch("scripts.sources.youtube.fetch_transcript", return_value="")
    @patch("scripts.sources.youtube.feedparser")
    def test_excludes_non_matching_titles(self, mock_feedparser, mock_transcript):
        """クエリに一致しないタイトルの動画は含まれない"""
        mock_feed = MagicMock()
        mock_feed.entries = [self._make_entry("Totally unrelated video")]
        mock_feedparser.parse.return_value = mock_feed

        result = search_videos("deadlock", days=90)

        assert result == []

    @patch("scripts.sources.youtube.fetch_transcript", return_value="")
    @patch("scripts.sources.youtube.feedparser")
    def test_multiple_keywords_or_match(self, mock_feedparser, mock_transcript):
        """カンマ区切りのキーワードはOR条件で検索される"""
        mock_feed = MagicMock()
        mock_feed.entries = [
            self._make_entry("Dynamo guide"),
            self._make_entry("Mo & Krill tips"),
            self._make_entry("Unrelated content"),
        ]
        mock_feedparser.parse.return_value = mock_feed

        result = search_videos("dynamo, krill", days=90)

        titles = [v["title"] for v in result]
        assert "Dynamo guide" in titles
        assert "Mo & Krill tips" in titles
        assert "Unrelated content" not in titles

    @patch("scripts.sources.youtube.feedparser")
    def test_handles_search_error_gracefully(self, mock_feedparser):
        """検索中にエラーが起きても例外を外部に伝播しない"""
        mock_feedparser.parse.side_effect = Exception("timeout")

        result = search_videos("deadlock", days=90)

        assert result == []
