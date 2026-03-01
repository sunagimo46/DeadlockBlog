"""scripts/sources/reddit.py の fetch_post_by_url 機能のテスト"""

from unittest.mock import MagicMock, patch

import pytest

from scripts.sources.reddit import fetch_post_by_url


class TestFetchPostByUrl:
    """fetch_post_by_url: Reddit 投稿 URL から本文を取得する"""

    def _make_response(self, title: str, selftext: str) -> list:
        """Reddit JSON API のレスポンス形式のスタブを生成する"""
        return [
            {
                "data": {
                    "children": [
                        {
                            "data": {
                                "title": title,
                                "selftext": selftext,
                            }
                        }
                    ]
                }
            }
        ]

    @patch("scripts.sources.reddit.requests.get")
    def test_returns_post_content(self, mock_get):
        """正常な Reddit 投稿 URL から本文を取得できる"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._make_response("テストタイトル", "本文テスト")
        mock_get.return_value = mock_resp

        result = fetch_post_by_url(
            "https://www.reddit.com/r/DeadlockTheGame/comments/abc123/test_post/"
        )

        assert "テストタイトル" in result
        assert "本文テスト" in result

    @patch("scripts.sources.reddit.requests.get")
    def test_truncates_long_content(self, mock_get):
        """1000 文字を超えるコンテンツは省略記号付きでトリムされる"""
        long_text = "a" * 1100
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._make_response("title", long_text)
        mock_get.return_value = mock_resp

        result = fetch_post_by_url(
            "https://www.reddit.com/r/DeadlockTheGame/comments/abc123/test/"
        )

        assert len(result) == 1000 + len("…（以下省略）")
        assert result.endswith("…（以下省略）")

    def test_invalid_url_no_comments_returns_empty(self):
        """/comments/ を含まない URL は空文字を返す（API を呼ばない）"""
        result = fetch_post_by_url("https://www.reddit.com/r/DeadlockTheGame/")
        assert result == ""

    def test_non_reddit_url_returns_empty(self):
        """reddit.com を含まない URL は空文字を返す"""
        result = fetch_post_by_url("https://example.com/r/test/comments/abc/post/")
        assert result == ""

    @patch("scripts.sources.reddit.requests.get")
    def test_api_error_returns_empty(self, mock_get):
        """API エラー時は空文字を返す"""
        mock_get.side_effect = Exception("connection error")

        result = fetch_post_by_url(
            "https://www.reddit.com/r/DeadlockTheGame/comments/abc123/test/"
        )

        assert result == ""

    @patch("scripts.sources.reddit.requests.get")
    def test_http_error_returns_empty(self, mock_get):
        """HTTP エラー (4xx/5xx) 時は空文字を返す"""
        import requests as req

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req.HTTPError("404")
        mock_get.return_value = mock_resp

        result = fetch_post_by_url(
            "https://www.reddit.com/r/DeadlockTheGame/comments/abc123/test/"
        )

        assert result == ""

    @patch("scripts.sources.reddit.requests.get")
    def test_empty_selftext_returns_title_only(self, mock_get):
        """selftext が空の場合はタイトルのみ返す"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._make_response("タイトルのみ", "")
        mock_get.return_value = mock_resp

        result = fetch_post_by_url(
            "https://www.reddit.com/r/DeadlockTheGame/comments/abc123/test/"
        )

        assert result == "タイトルのみ"
