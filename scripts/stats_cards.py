"""Render GitHub stats and top-language cards as SVG from the GraphQL API.

Usage: GITHUB_TOKEN=... python3 scripts/stats_cards.py <user> <display_name> <out_dir>
"""

import json
import os
import sys
import urllib.request
from html import escape

API = "https://api.github.com/graphql"
TOP_LANGS = 6
# Markup and build files from the website / CV repos would otherwise dominate.
HIDDEN_LANGS = {"HTML", "CSS", "TeX", "CMake", "Makefile", "Batchfile"}

STYLE = """
<style>
  .title { font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #2F81F7; }
  .label { font: 400 14px 'Segoe UI', Ubuntu, sans-serif; fill: #57606A; }
  .value { font: 600 14px 'Segoe UI', Ubuntu, sans-serif; fill: #1F2328; }
  .icon  { fill: #2F81F7; }
  @media (prefers-color-scheme: dark) {
    .label { fill: #9198A1; }
    .value { fill: #F0F6FC; }
  }
</style>
"""

# 16x16 Octicons paths
ICONS = {
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354Z",
    "issue": "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
}


def graphql(query, **variables):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch(login):
    user = graphql("""
      query($login: String!) {
        user(login: $login) {
          contributionsCollection { contributionYears }
          pullRequests { totalCount }
          issues { totalCount }
          repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE]) { totalCount }
          repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
            totalCount
            nodes {
              stargazerCount
              languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
                edges { size node { name color } }
              }
            }
          }
        }
      }""", login=login)["user"]

    commits = 0
    for year in user["contributionsCollection"]["contributionYears"]:
        c = graphql("""
          query($login: String!, $from: DateTime!, $to: DateTime!) {
            user(login: $login) {
              contributionsCollection(from: $from, to: $to) {
                totalCommitContributions
                restrictedContributionsCount
              }
            }
          }""", login=login, **{"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"})
        cc = c["user"]["contributionsCollection"]
        commits += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]

    langs = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in HIDDEN_LANGS:
                continue
            size, _ = langs.get(name, (0, None))
            langs[name] = (size + edge["size"], edge["node"]["color"] or "#8B949E")

    return {
        "stars": sum(r["stargazerCount"] for r in user["repositories"]["nodes"]),
        "commits": commits,
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "langs": sorted(langs.items(), key=lambda kv: -kv[1][0])[:TOP_LANGS],
    }


def stats_svg(s, name):
    rows = [
        ("star", "Total stars", s["stars"]),
        ("commit", "Total commits", s["commits"]),
        ("pr", "Pull requests", s["prs"]),
        ("issue", "Issues", s["issues"]),
        ("repo", "Contributed to", s["contributed"]),
    ]
    body = []
    for i, (icon, label, value) in enumerate(rows):
        y = 60 + i * 25
        body.append(
            f'<path class="icon" transform="translate(25,{y - 12})" d="{ICONS[icon]}"/>'
            f'<text class="label" x="50" y="{y}">{label}:</text>'
            f'<text class="value" x="200" y="{y}">{value:,}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="195" viewBox="0 0 300 195">{STYLE}'
        f'<text class="title" x="25" y="32">{escape(name)}\'s GitHub Stats</text>'
        f'{"".join(body)}</svg>'
    )


def langs_svg(langs):
    total = sum(size for _, (size, _) in langs) or 1
    bar, x = [], 25.0
    for name, (size, color) in langs:
        w = 250 * size / total
        bar.append(f'<rect x="{x:.2f}" y="48" width="{w:.2f}" height="8" fill="{color}"/>')
        x += w
    items = []
    for i, (name, (size, color)) in enumerate(langs):
        cx, cy = 25 + (i % 2) * 130, 85 + (i // 2) * 25
        items.append(
            f'<circle cx="{cx + 5}" cy="{cy - 5}" r="5" fill="{color}"/>'
            f'<text class="label" x="{cx + 16}" y="{cy}">{escape(name)} '
            f'<tspan class="value">{100 * size / total:.1f}%</tspan></text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="195" viewBox="0 0 300 195">{STYLE}'
        f'<text class="title" x="25" y="32">Most Used Languages</text>'
        f'<clipPath id="r"><rect x="25" y="48" width="250" height="8" rx="4"/></clipPath>'
        f'<g clip-path="url(#r)">{"".join(bar)}</g>{"".join(items)}</svg>'
    )


def main():
    login, name, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    s = fetch(login)
    with open(os.path.join(out, "stats.svg"), "w", encoding="utf-8") as f:
        f.write(stats_svg(s, name))
    with open(os.path.join(out, "top-langs.svg"), "w", encoding="utf-8") as f:
        f.write(langs_svg(s["langs"]))
    print(json.dumps({k: v for k, v in s.items() if k != "langs"}), [n for n, _ in s["langs"]])


if __name__ == "__main__":
    main()
