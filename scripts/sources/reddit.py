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
