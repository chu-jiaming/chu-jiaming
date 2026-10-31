"""Render the productive-box gist as SVG cards matching the light_github / dark_github stats card.

Usage: python3 scripts/productive_card.py <gist_id> <out_dir>
"""

import json
import os
import re
import sys
import urllib.request
from html import escape

THEMES = {
    "": {"title": "#0969da", "text": "#59636e", "bg": "#ffffff", "border": "#d1d9e0", "track": "#eff2f5"},
    "-dark": {"title": "#4493f8", "text": "#9198a1", "bg": "#0d1117", "border": "#3d444d", "track": "#21262d"},
}
ROW = re.compile(r"^(\S+)\s+(\w+)\s+(\d+)\s+commits\s+\S+\s+([\d.]+)%$")
WIDTH, BAR_X, BAR_W = 467, 205, 175


def fetch(gist_id):
    req = urllib.request.Request(f"https://api.github.com/gists/{gist_id}")
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        title, f = next(iter(json.load(resp)["files"].items()))
    rows = [m.groups() for m in map(ROW.match, f["content"].splitlines()) if m]
    if not rows:
        raise SystemExit("gist content not in productive-box format")
    return title, rows


def render(title, rows, c):
    body = []
    for i, (emoji, label, commits, pct) in enumerate(rows):
        y = 80 + i * 28
        fill = BAR_W * float(pct) / 100
        body.append(
            f'<text x="25" y="{y}" class="label">{escape(emoji)} {escape(label)}</text>'
            f'<text x="190" y="{y}" class="label" text-anchor="end">{commits}</text>'
            f'<rect x="{BAR_X}" y="{y - 9}" width="{BAR_W}" height="8" rx="4" fill="{c["track"]}"/>'
            f'<rect x="{BAR_X}" y="{y - 9}" width="{fill:.1f}" height="8" rx="4" fill="{c["title"]}"/>'
            f'<text x="{WIDTH - 25}" y="{y}" class="value" text-anchor="end">{pct}%</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="195" viewBox="0 0 {WIDTH} 195">'
        f"<style>"
        f".title{{font:600 18px 'Segoe UI',Ubuntu,Sans-Serif;fill:{c['title']}}}"
        f".label{{font:600 14px 'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif;fill:{c['text']}}}"
        f".value{{font:600 14px 'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif;fill:{c['text']}}}"
        f"</style>"
        f'<rect x="0.5" y="0.5" rx="4.5" width="{WIDTH - 1}" height="194" fill="{c["bg"]}" stroke="{c["border"]}"/>'
        f'<text x="25" y="35" class="title">{escape(title)}</text>'
        f'{"".join(body)}</svg>'
    )


def main():
    gist_id, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    title, rows = fetch(gist_id)
    for suffix, colors in THEMES.items():
        with open(os.path.join(out, f"productive{suffix}.svg"), "w", encoding="utf-8") as f:
            f.write(render(title, rows, colors))


if __name__ == "__main__":
    main()
