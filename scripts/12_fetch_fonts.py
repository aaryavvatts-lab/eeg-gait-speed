"""Download the web fonts once and store them as base64 inside the repo.

The page embeds the fonts rather than linking to Google's servers. Two reasons.
The published page then makes no outside requests at all, which keeps the
privacy notice short and true. And nothing breaks if the font host is blocked
or changes a URL.

All three families are licensed under the SIL Open Font License, which allows
embedding and redistribution.
"""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.request

from gaitbci import config as cfg

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# family -> list of (css family query, css font-family name, weight, style)
WANTED = [
    ("Archivo:wght@600;700", "Archivo", [600, 700], "normal"),
    ("Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400",
     "Source Serif 4", [400, 600], "both"),
    ("IBM+Plex+Mono:wght@400;500", "IBM Plex Mono", [400, 500], "normal"),
]

OUT = cfg.ROOT / "src" / "gaitbci" / "fonts.py"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def latin_blocks(css: str) -> list[dict]:
    """Pull out only the plain latin @font-face blocks.

    The other subsets cover alphabets this page never prints, and each one
    would add weight to the file for nothing.
    """
    blocks = []
    for chunk in css.split("@font-face"):
        if "unicode-range" not in chunk:
            continue
        rng = re.search(r"unicode-range:\s*([^;]+);", chunk).group(1)
        if not rng.strip().startswith("U+0000-00FF"):
            continue
        blocks.append({
            "family": re.search(r"font-family:\s*'([^']+)'", chunk).group(1),
            "style": re.search(r"font-style:\s*(\w+)", chunk).group(1),
            "weight": re.search(r"font-weight:\s*(\d+)", chunk).group(1),
            "url": re.search(r"src:\s*url\(([^)]+)\)", chunk).group(1),
        })
    return blocks


def main() -> int:
    faces = []
    for query, _name, _weights, _style in WANTED:
        css = fetch(f"https://fonts.googleapis.com/css2?family={query}"
                    "&display=swap").decode()
        for b in latin_blocks(css):
            data = fetch(b["url"])
            faces.append({
                "family": b["family"],
                "style": b["style"],
                "weight": int(b["weight"]),
                "b64": base64.b64encode(data).decode(),
                "bytes": len(data),
            })
            print(f"  {b['family']} {b['weight']} {b['style']}: "
                  f"{len(data)/1024:.0f} KB")

    total = sum(f["bytes"] for f in faces)
    print(f"{len(faces)} faces, {total/1024:.0f} KB raw")

    body = [
        '"""Web fonts stored as base64, written by scripts/12_fetch_fonts.py.',
        "",
        "Archivo, Source Serif 4 and IBM Plex Mono are all under the SIL Open",
        "Font License, which permits embedding and redistribution.",
        '"""',
        "",
        "FACES = " + json.dumps(faces, indent=0).replace("\n", "\n"),
        "",
        "",
        "def css() -> str:",
        '    """Return @font-face rules with the font data inlined."""',
        "    out = []",
        "    for f in FACES:",
        "        out.append(",
        '            "@font-face{font-family:\'%s\';font-style:%s;font-weight:%d;"',
        '            "font-display:swap;src:url(data:font/woff2;base64,%s) "',
        '            "format(\'woff2\');}"',
        '            % (f["family"], f["style"], f["weight"], f["b64"])',
        "        )",
        '    return "".join(out)',
        "",
    ]
    OUT.write_text("\n".join(body))
    print(f"wrote {OUT.relative_to(cfg.ROOT)} "
          f"({OUT.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
