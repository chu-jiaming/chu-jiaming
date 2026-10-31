"""Make a dark-mode copy of the GitAnimals farm SVG.

The farm draws its text as black paths on a white card, so swap the card colours
and recolour only the name / level / contribution glyphs (pets keep their colours).

Usage: python3 scripts/farm_dark.py <user> <out_file>
"""

import sys
import urllib.request

BG = '<rect x="0.5" y="0.5" width="599" height="299" rx="4.5" fill="white"/>'
BORDER = 'stroke="#D9D9D9"'
CSS = '<style>[id^="name"] path,[id^="level"] path,[id^="commit"] path{fill:#e6edf3}</style>'


def main():
    user, out = sys.argv[1], sys.argv[2]
    req = urllib.request.Request(f"https://render.gitanimals.org/farms/{user}", headers={"User-Agent": "chu-jiaming-profile"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        svg = resp.read().decode("utf-8")
    if BG not in svg or BORDER not in svg:
        raise SystemExit("farm SVG layout changed; not publishing a broken dark copy")
    svg = svg.replace(BG, BG.replace('fill="white"', 'fill="#0d1117"'), 1).replace(BORDER, 'stroke="#3d444d"', 1)
    head = svg.index(">") + 1
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg[:head] + CSS + svg[head:])


if __name__ == "__main__":
    main()
