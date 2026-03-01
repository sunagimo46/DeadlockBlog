"""YouTube RSS フィードからDeadlock関連動画を取得するモジュール"""

from datetime import datetime, timedelta, timezone

import feedparser

CHANNELS = {
    "Eidorian": "UCLS1nZT0SEqZcEWKYAllFRg",
    "Deathy": "UCj929zzQbCYGBAUX0Tod4Eg",
    "MastYT": "UCU0oLTV2RO-l4uUkQVy2TvA",
    "Midknighttxt": "UCPAdg0t1CEuMRTzbzRHMCXw",
    "poshypop": "UCrZR30NWLNLJfswlYA_mOrA",
}

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


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
                })
        except Exception as e:
            print(f"[YouTube] {name} の取得に失敗: {e}")

    return videos
