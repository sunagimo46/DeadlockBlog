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
