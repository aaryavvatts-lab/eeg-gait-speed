"""Turn the write-up into a printable PDF.

The Markdown file stays the single source, so the PDF cannot drift away from
the web page. Figures are embedded so the PDF stands alone once it leaves this
folder.
"""
from __future__ import annotations

import base64
import re
import shutil
import subprocess
import sys

import markdown

from gaitbci import config as cfg

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PRINT_HTML = cfg.REPORT / "paper_print.html"
PDF = cfg.REPORT / "walking-speed-from-eeg.pdf"

PRINT_CSS = """
@page { size: A4; margin: 20mm 18mm 18mm; }
body { font-family: "Source Serif 4", Georgia, "Times New Roman", serif;
  font-size: 10.5pt; line-height: 1.5; color: #14121a; margin: 0; }
h1 { font-size: 20pt; line-height: 1.15; margin: 0 0 6pt; font-weight: 700;
  letter-spacing: -.01em; }
h2 { font-size: 13pt; margin: 20pt 0 5pt; font-weight: 700;
  page-break-after: avoid; border-bottom: 1px solid #d8d5e0; padding-bottom: 3pt; }
h3 { font-size: 11pt; margin: 14pt 0 3pt; font-weight: 600;
  page-break-after: avoid; }
p { margin: 0 0 7pt; }
a { color: #155288; text-decoration: none; word-break: break-word; }
strong { font-weight: 600; }
code { font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 9pt; background: #f2f1f7; padding: 1px 3px; border-radius: 2px; }
pre { background: #f6f5fa; border: 1px solid #e2e0ea; border-radius: 4px;
  padding: 8pt 10pt; font-size: 8.5pt; overflow-x: auto;
  page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.5pt; }
table { border-collapse: collapse; width: 100%; font-size: 9pt;
  margin: 8pt 0 12pt; page-break-inside: avoid; }
th, td { border-bottom: 1px solid #ddd9e6; padding: 4pt 6pt; text-align: left;
  vertical-align: top; }
th { background: #f2f1f7; font-weight: 600; font-size: 8pt;
  text-transform: uppercase; letter-spacing: .05em; color: #55506b; }
img { max-width: 100%; height: auto; display: block; margin: 6pt auto; }
p:has(img) { page-break-inside: avoid; text-align: center; }
ol, ul { margin: 0 0 8pt; padding-left: 16pt; }
li { margin-bottom: 3pt; }
ol li { padding-left: 2pt; }
.title-block { border-bottom: 2px solid #14121a; padding-bottom: 10pt;
  margin-bottom: 14pt; }
.sub { color: #55506b; font-size: 9.5pt; margin: 4pt 0 0; }
h2#references + ol { font-size: 9pt; }
"""


def embed_images(html: str) -> str:
    """Swap figure paths for inline data so the PDF carries its own pictures."""
    def repl(m):
        rel = m.group(1)
        name = rel.split("/")[-1]
        path = cfg.FIGURES / name
        if not path.exists():
            return m.group(0)
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f'src="data:image/png;base64,{b64}"'
    return re.sub(r'src="([^"]+\.png)"', repl, html)


def main() -> int:
    if not shutil.which(CHROME) and not cfg.ROOT.joinpath(CHROME).exists():
        import os
        if not os.path.exists(CHROME):
            print(f"Chrome not found at {CHROME}; cannot render the PDF")
            return 1

    md_text = (cfg.REPORT / "report.md").read_text()
    body = markdown.markdown(
        md_text, extensions=["tables", "fenced_code", "attr_list"])

    # The first heading becomes a title block rather than a run-of-page heading.
    body = body.replace(
        "<h1>Guessing walking speed from brain and muscle signals</h1>",
        '<div class="title-block">'
        "<h1>Guessing walking speed from brain and muscle signals</h1>"
        '<p class="sub">A re-analysis of a public gait dataset, and what happens '
        "to the result when the test setup is fixed.</p></div>",
        1,
    )
    body = embed_images(body)

    html = (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>Guessing walking speed from brain and muscle signals</title>"
            f"<style>{PRINT_CSS}</style></head><body>{body}</body></html>")
    PRINT_HTML.write_text(html)

    cmd = [
        CHROME, "--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF}",
        PRINT_HTML.as_uri(),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not PDF.exists():
        print("chrome stderr:", res.stderr[-800:])
        return 1
    print(f"pdf -> {PDF.relative_to(cfg.ROOT)} "
          f"({PDF.stat().st_size / 1024:.0f} KB)")
    PRINT_HTML.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
