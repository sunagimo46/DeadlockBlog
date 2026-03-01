"""Deadlock Wiki (MediaWiki API) から更新情報を取得するモジュール"""

from datetime import datetime, timedelta, timezone

import requests

API_URL = "https://deadlock.wiki/api.php"


def fetch_recent_changes(days: int = 3, limit: int = 20) -> list[dict]:
    """最近更新されたWikiページを取得する"""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    changes = []

    try:
        resp = requests.get(
            API_URL,
            params={
                "action": "query",
                "list": "recentchanges",
                "rcnamespace": "0",
                "rclimit": limit,
                "rcprop": "title|timestamp|sizes",
                "rctype": "edit|new",
                "rcend": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": "json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        seen_titles: set[str] = set()
        for rc in data.get("query", {}).get("recentchanges", []):
            title = rc.get("title", "")
            if title in seen_titles:
                continue
            seen_titles.add(title)
            changes.append({
                "source": "Wiki",
                "title": title,
                "url": f"https://deadlock.wiki/wiki/{title.replace(' ', '_')}",
                "timestamp": rc.get("timestamp", ""),
            })
    except Exception as e:
        print(f"[Wiki] 取得に失敗: {e}")

    return changes


def search_pages(query: str, limit: int = 10) -> list[dict]:
    """Deadlock Wiki でキーワード検索を行う"""
    results = []

    try:
        resp = requests.get(
            API_URL,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srnamespace": "0",
                "srlimit": limit,
                "format": "json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        import re

        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            snippet = re.sub(r"<[^>]+>", "", snippet)
            results.append({
                "source": "Wiki",
                "title": title,
                "url": f"https://deadlock.wiki/wiki/{title.replace(' ', '_')}",
                "snippet": snippet,
            })
    except Exception as e:
        print(f"[Wiki] 検索に失敗: {e}")

    return results


def fetch_page_by_url(url: str) -> str:
    """Deadlock Wiki ページ URL からページ本文を取得する（最大 2000 文字）"""
    if "deadlock.wiki/wiki/" not in url:
        return ""
    try:
        from urllib.parse import unquote
        page_title = unquote(url.split("/wiki/")[-1])
        resp = requests.get(
            API_URL,
            params={"action": "parse", "page": page_title, "prop": "wikitext", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        if len(wikitext) > 2000:
            wikitext = wikitext[:2000] + "…（以下省略）"
        return wikitext
    except Exception as e:
        print(f"[Wiki] ページ取得エラー ({url}): {e}")
        return ""
