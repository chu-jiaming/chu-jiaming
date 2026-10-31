"""Write the latest Last.fm tracks into README.md between the music markers."""

import json
import os
import re
import urllib.parse
import urllib.request

README = "README.md"
START, END = "<!--START_SECTION:music-->", "<!--END_SECTION:music-->"
LIMIT = 5


def fetch_tracks():
    query = urllib.parse.urlencode({
        "method": "user.getrecenttracks",
        "user": os.environ["LASTFM_USER"],
        "api_key": os.environ["LASTFM_API_KEY"],
        "format": "json",
        "limit": LIMIT,
    })
    with urllib.request.urlopen(f"https://ws.audioscrobbler.com/2.0/?{query}", timeout=20) as resp:
        tracks = json.load(resp)["recenttracks"]["track"]
    # When something is playing, Last.fm returns it in addition to `limit` tracks.
    return tracks[:LIMIT]


def render(tracks):
    if not tracks:
        return "_Nothing scrobbled yet._"
    lines = []
    for t in tracks:
        name = t["name"].replace("|", "\\|")
        artist = t["artist"]["#text"].replace("|", "\\|")
        now = t.get("@attr", {}).get("nowplaying") == "true"
        prefix = "▶️ **Now playing:**" if now else "🎵"
        lines.append(f"- {prefix} [{name}]({t['url']}) — {artist}")
    return "\n".join(lines)


def main():
    with open(README, encoding="utf-8") as f:
        text = f.read()
    block = f"{START}\n{render(fetch_tracks())}\n{END}"
    text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    with open(README, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
