"""generate_article.py の URL 抽出・コンテンツ取得・プロンプト統合テスト"""

from unittest.mock import patch

import pytest

from scripts.generate_article import (
    build_prompt,
    extract_reference_urls,
    fetch_reference_contents,
)


# ---------------------------------------------------------------------------
# extract_reference_urls
# ---------------------------------------------------------------------------


class TestExtractReferenceUrls:
    """extract_reference_urls: Issue 本文から URL を抽出して分類する"""

    def test_no_reference_section_returns_empty_lists(self):
        """「### 参考情報」セクションがない場合は全キーが空リスト"""
        body = "### 概要\n記事の概要です。\n### 詳細\n詳細です。"
        result = extract_reference_urls(body)
        assert result == {"youtube": [], "reddit": [], "wiki": [], "other": []}

    def test_youtube_watch_url_classified(self):
        """youtube.com/watch URL が youtube カテゴリに分類される"""
        body = "### 参考情報\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = extract_reference_urls(body)
        assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in result["youtube"]
        assert result["reddit"] == []

    def test_youtu_be_url_classified(self):
        """youtu.be 短縮 URL が youtube カテゴリに分類される"""
        body = "### 参考情報\nhttps://youtu.be/dQw4w9WgXcQ"
        result = extract_reference_urls(body)
        assert "https://youtu.be/dQw4w9WgXcQ" in result["youtube"]

    def test_reddit_comments_url_classified(self):
        """reddit.com/r/.../comments/ URL が reddit カテゴリに分類される"""
        body = "### 参考情報\nhttps://www.reddit.com/r/DeadlockTheGame/comments/abc123/test/"
        result = extract_reference_urls(body)
        assert len(result["reddit"]) == 1
        assert result["youtube"] == []

    def test_wiki_url_classified(self):
        """deadlock.wiki/wiki/ URL が wiki カテゴリに分類される"""
        body = "### 参考情報\nhttps://deadlock.wiki/wiki/McGinnis"
        result = extract_reference_urls(body)
        assert "https://deadlock.wiki/wiki/McGinnis" in result["wiki"]

    def test_other_url_classified(self):
        """上記いずれにも該当しない URL が other カテゴリに分類される"""
        body = "### 参考情報\nhttps://example.com/some-page"
        result = extract_reference_urls(body)
        assert "https://example.com/some-page" in result["other"]

    def test_multiple_urls_mixed_categories(self):
        """複数の URL が正しくカテゴリ分けされる"""
        body = (
            "### 参考情報\n"
            "https://www.youtube.com/watch?v=abc\n"
            "https://www.reddit.com/r/DeadlockTheGame/comments/xyz/post/\n"
            "https://deadlock.wiki/wiki/Hero\n"
        )
        result = extract_reference_urls(body)
        assert len(result["youtube"]) == 1
        assert len(result["reddit"]) == 1
        assert len(result["wiki"]) == 1

    def test_section_boundary_stops_at_next_header(self):
        """「### 参考情報」の次の「### 」で URL 抽出が止まる"""
        body = (
            "### 参考情報\n"
            "https://www.youtube.com/watch?v=abc\n"
            "### 別セクション\n"
            "https://www.youtube.com/watch?v=xyz\n"
        )
        result = extract_reference_urls(body)
        # 最初のセクションの URL のみ抽出される
        assert len(result["youtube"]) == 1
        assert "https://www.youtube.com/watch?v=abc" in result["youtube"]


# ---------------------------------------------------------------------------
# fetch_reference_contents
# ---------------------------------------------------------------------------


class TestFetchReferenceContents:
    """fetch_reference_contents: 各 URL のコンテンツを取得して結合する"""

    def test_all_empty_returns_empty_string(self):
        """全 URL でコンテンツ取得が空の場合は空文字を返す"""
        urls = {"youtube": [], "reddit": [], "wiki": [], "other": []}
        result = fetch_reference_contents(urls)
        assert result == ""

    @patch("scripts.generate_article.fetch_transcript", return_value="字幕テスト")
    def test_youtube_content_included(self, mock_transcript):
        """YouTube URL のコンテンツが結果に含まれる"""
        urls = {
            "youtube": ["https://www.youtube.com/watch?v=abc"],
            "reddit": [],
            "wiki": [],
            "other": [],
        }
        result = fetch_reference_contents(urls)
        assert "字幕テスト" in result
        assert "YouTube 動画の字幕" in result

    @patch("scripts.generate_article.fetch_post_by_url", return_value="Reddit 投稿本文")
    def test_reddit_content_included(self, mock_post):
        """Reddit URL のコンテンツが結果に含まれる"""
        urls = {
            "youtube": [],
            "reddit": ["https://www.reddit.com/r/DeadlockTheGame/comments/abc/post/"],
            "wiki": [],
            "other": [],
        }
        result = fetch_reference_contents(urls)
        assert "Reddit 投稿本文" in result
        assert "Reddit 投稿" in result

    @patch("scripts.generate_article.fetch_page_by_url", return_value="Wikiテキスト")
    def test_wiki_content_included(self, mock_page):
        """Wiki URL のコンテンツが結果に含まれる"""
        urls = {
            "youtube": [],
            "reddit": [],
            "wiki": ["https://deadlock.wiki/wiki/McGinnis"],
            "other": [],
        }
        result = fetch_reference_contents(urls)
        assert "Wikiテキスト" in result
        assert "Deadlock Wiki ページ" in result

    def test_other_urls_listed_without_content(self):
        """other URL はコンテンツ取得せず URL のみ列挙される"""
        urls = {
            "youtube": [],
            "reddit": [],
            "wiki": [],
            "other": ["https://example.com/page"],
        }
        result = fetch_reference_contents(urls)
        assert "https://example.com/page" in result
        assert "その他の参考 URL" in result

    @patch("scripts.generate_article.fetch_transcript", return_value="")
    def test_empty_content_entries_skipped(self, mock_transcript):
        """コンテンツが空文字のエントリはスキップされる"""
        urls = {
            "youtube": ["https://www.youtube.com/watch?v=abc"],
            "reddit": [],
            "wiki": [],
            "other": [],
        }
        result = fetch_reference_contents(urls)
        assert result == ""

    @patch("scripts.generate_article.fetch_transcript", return_value="字幕A")
    @patch("scripts.generate_article.fetch_post_by_url", return_value="投稿B")
    def test_multiple_contents_joined_with_separator(self, mock_post, mock_transcript):
        """複数のコンテンツが区切り文字で結合される"""
        urls = {
            "youtube": ["https://www.youtube.com/watch?v=abc"],
            "reddit": ["https://www.reddit.com/r/DeadlockTheGame/comments/xyz/post/"],
            "wiki": [],
            "other": [],
        }
        result = fetch_reference_contents(urls)
        assert "---" in result
        assert "字幕A" in result
        assert "投稿B" in result


# ---------------------------------------------------------------------------
# build_prompt (参照コンテンツ統合テスト)
# ---------------------------------------------------------------------------


class TestBuildPromptWithReferenceContent:
    """build_prompt: 参照コンテンツがプロンプトに正しく統合される"""

    def _make_issue(self, body: str = "") -> dict:
        return {
            "title": "テスト記事",
            "body": body,
            "labels": [],
        }

    @patch("scripts.generate_article.fetch_transcript", return_value="動画の字幕内容")
    def test_reference_content_section_included(self, mock_transcript):
        """参照コンテンツがある場合、「## 参照コンテンツ」セクションがプロンプトに含まれる"""
        body = "### 参考情報\nhttps://www.youtube.com/watch?v=abc"
        issue = self._make_issue(body)
        prompt = build_prompt(issue, [], "")
        assert "## 参照コンテンツ" in prompt
        assert "動画の字幕内容" in prompt

    @patch("scripts.generate_article.fetch_transcript", return_value="")
    def test_no_reference_content_shows_default_message(self, mock_transcript):
        """参照コンテンツもリサーチ結果もない場合、デフォルトメッセージが含まれる"""
        body = "### 参考情報\nhttps://www.youtube.com/watch?v=abc"
        issue = self._make_issue(body)
        prompt = build_prompt(issue, [], "")
        assert "リサーチ結果はありません" in prompt

    def test_no_reference_section_shows_default_message(self):
        """「### 参考情報」セクションがなく、リサーチ結果もない場合、デフォルトメッセージ"""
        issue = self._make_issue("記事の概要です。")
        prompt = build_prompt(issue, [], "")
        assert "リサーチ結果はありません" in prompt

    @patch("scripts.generate_article.fetch_transcript", return_value="字幕テスト")
    def test_reference_content_and_research_both_included(self, mock_transcript):
        """参照コンテンツとリサーチ結果が両方ある場合、両方プロンプトに含まれる"""
        body = "### 参考情報\nhttps://www.youtube.com/watch?v=abc"
        issue = self._make_issue(body)
        research_comment = {"body": "## リサーチ結果: テスト\nリサーチ内容"}
        prompt = build_prompt(issue, [research_comment], "")
        assert "## 参照コンテンツ" in prompt
        assert "## リサーチ結果（参考情報）" in prompt
        assert "リサーチ結果はありません" not in prompt
