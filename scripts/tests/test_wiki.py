"""scripts/sources/wiki.py の fetch_page_by_url 機能のテスト"""

from unittest.mock import MagicMock, patch

import pytest

from scripts.sources.wiki import fetch_page_by_url


class TestFetchPageByUrl:
    """fetch_page_by_url: Deadlock Wiki ページ URL からページ本文を取得する"""

    def _make_response(self, wikitext: str) -> dict:
        """MediaWiki API のレスポンス形式のスタブを生成する"""
        return {
            "parse": {
                "wikitext": {
                    "*": wikitext,
                }
            }
        }

    @patch("scripts.sources.wiki.requests.get")
    def test_returns_wikitext(self, mock_get):
        """正常な Wiki URL からウィキテキストを取得できる"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._make_response("== ヒーロー解説 ==\nテスト本文")
        mock_get.return_value = mock_resp

        result = fetch_page_by_url("https://deadlock.wiki/wiki/McGinnis")

        assert "ヒーロー解説" in result
        assert "テスト本文" in result

    @patch("scripts.sources.wiki.requests.get")
    def test_truncates_long_wikitext(self, mock_get):
        """2000 文字を超えるウィキテキストは省略記号付きでトリムされる"""
        long_text = "w" * 2100
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._make_response(long_text)
        mock_get.return_value = mock_resp

        result = fetch_page_by_url("https://deadlock.wiki/wiki/SomePage")

        assert len(result) == 2000 + len("…（以下省略）")
        assert result.endswith("…（以下省略）")

    def test_non_wiki_url_returns_empty(self):
        """deadlock.wiki/wiki/ を含まない URL は空文字を返す"""
        result = fetch_page_by_url("https://example.com/wiki/Page")
        assert result == ""

    def test_wiki_domain_without_path_returns_empty(self):
        """/wiki/ パスが存在しない deadlock.wiki URL は空文字を返す"""
        result = fetch_page_by_url("https://deadlock.wiki/api.php")
        assert result == ""

    @patch("scripts.sources.wiki.requests.get")
    def test_api_error_returns_empty(self, mock_get):
        """API エラー時は空文字を返す"""
        mock_get.side_effect = Exception("timeout")

        result = fetch_page_by_url("https://deadlock.wiki/wiki/McGinnis")

        assert result == ""

    @patch("scripts.sources.wiki.requests.get")
    def test_http_error_returns_empty(self, mock_get):
        """HTTP エラー (4xx/5xx) 時は空文字を返す"""
        import requests as req

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req.HTTPError("500")
        mock_get.return_value = mock_resp

        result = fetch_page_by_url("https://deadlock.wiki/wiki/McGinnis")

        assert result == ""
