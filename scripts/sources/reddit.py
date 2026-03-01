"""Reddit JSON API からDeadlock関連の投稿を取得するモジュール"""

import requests

SUBREDDIT_URL = "https://www.reddit.com/r/DeadlockTheGame/hot.json"
HEADERS = {"User-Agent": "DeadlockBlogCollector/1.0"}


def fetch_hot_posts(limit: int = 15) -> list[dict]:
    """r/DeadlockTheGame のホット投稿を取得する"""
    posts = []

    try:
        resp = requests.get(
            SUBREDDIT_URL,
            headers=HEADERS,
            params={"limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            if post.get("stickied"):
                continue
            posts.append({
                "source": "Reddit",
                "title": post.get("title", ""),
                "url": f"https://www.reddit.com{post.get('permalink', '')}",
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
            })
    except Exception as e:
        print(f"[Reddit] 取得に失敗: {e}")

    return posts


def search_posts(
    query: str,
    sort: str = "relevance",
    time_filter: str = "year",
    limit: int = 10,
) -> list[dict]:
    """r/DeadlockTheGame でキーワード検索を行う"""
    posts = []

    try:
        resp = requests.get(
            "https://www.reddit.com/r/DeadlockTheGame/search.json",
            headers=HEADERS,
            params={
                "q": query,
                "restrict_sr": "on",
                "sort": sort,
                "t": time_filter,
                "limit": limit,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            selftext = post.get("selftext", "")
            posts.append({
                "source": "Reddit",
                "title": post.get("title", ""),
                "url": f"https://www.reddit.com{post.get('permalink', '')}",
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
                "selftext": selftext[:200] if selftext else "",
            })
    except Exception as e:
        print(f"[Reddit] 検索に失敗: {e}")

    return posts


def fetch_post_by_url(url: str) -> str:
    """Reddit 投稿 URL から本文を取得する（最大 1000 文字）"""
    if "reddit.com/r/" not in url or "/comments/" not in url:
        return ""
    try:
        json_url = url.rstrip("/") + ".json"
        resp = requests.get(json_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        post = data[0]["data"]["children"][0]["data"]
        title = post.get("title", "")
        selftext = post.get("selftext", "")
        content = f"{title}\n\n{selftext}".strip()
        if len(content) > 1000:
            content = content[:1000] + "…（以下省略）"
        return content
    except Exception as e:
        print(f"[Reddit] 投稿取得エラー ({url}): {e}")
        return ""
