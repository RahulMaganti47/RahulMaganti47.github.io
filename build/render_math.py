#!/usr/bin/env python3
"""Render LaTeX math in an HTML page to static, self-contained SVGs.

The site is plain static HTML served by GitHub Pages, so math must not
depend on a client-side library (MathJax/KaTeX) that can be blocked,
cached stale, or disabled. This renders every $...$ (inline) and
$$...$$ (display) equation to an SVG once, at build time, via the local
LaTeX toolchain, and rewrites the page to reference those SVGs with
correct per-equation baseline alignment.

Usage:
    python3 build/render_math.py <source.html> <output.html>

    <source.html>  authored page, LaTeX kept as $...$ / $$...$$  (edit this)
    <output.html>  built page committed and served by Pages       (generated)

SVGs are written to assets/math/<output-slug>-{d,m}<n>.svg, namespaced by
the output filename so different pages never collide.

Requires `latex` and `dvisvgm` on PATH (TeX Live / MacTeX).
Re-run after editing any equation in a source file.
"""
import re, os, sys, html, shutil, tempfile, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATHDIR = os.path.join(REPO, "assets", "math")
INK = "#17171a"          # matches --ink in style.css
BASE_PT = 12.0           # LaTeX document base size; sets the em scale

TEX_TEMPLATE = r"""\documentclass[12pt]{article}
\usepackage{amsmath,amssymb,xcolor}
\usepackage[tightpage,active]{preview}
\setlength\PreviewBorder{0pt}
\pagestyle{empty}
\begin{document}
%s
\end{document}
"""


def unescape_tex(s):
    return s.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: render_math.py <source.html> <output.html>")
    src_path, out_path = sys.argv[1], sys.argv[2]

    for tool in ("latex", "dvisvgm"):
        if not shutil.which(tool):
            sys.exit(f"error: '{tool}' not on PATH — install TeX Live / MacTeX")

    src = open(src_path).read()
    # Defensive: strip any leftover MathJax wiring so it can't shadow the SVGs.
    src = re.sub(r"\n?\s*<!-- Math -->", "", src)
    src = re.sub(r"<script>\s*window\.MathJax[\s\S]*?</script>\s*", "", src)
    src = re.sub(r'<script src="https://cdn\.jsdelivr\.net/npm/mathjax[^"]*"[^>]*></script>\s*', "", src)

    slug = os.path.splitext(os.path.basename(out_path))[0]
    os.makedirs(MATHDIR, exist_ok=True)
    relpath = os.path.relpath(MATHDIR, os.path.dirname(os.path.abspath(out_path)))

    display = list(dict.fromkeys(m.group(1).strip()
                   for m in re.finditer(r"\$\$(.+?)\$\$", src, re.S)))
    no_disp = re.sub(r"\$\$.+?\$\$", "\x00", src, flags=re.S)
    inline = list(dict.fromkeys(m.group(1).strip()
                  for m in re.finditer(r"\$(.+?)\$", no_disp, re.S)))

    if not display and not inline:
        open(out_path, "w").write(src)
        print(f"{slug}: no math; copied to {out_path}")
        return

    items = ([(k, "display", f"{slug}-d{i}.svg") for i, k in enumerate(display)] +
             [(k, "inline",  f"{slug}-m{i}.svg") for i, k in enumerate(inline)])

    pages = []
    for k, mode, _ in items:
        tex = unescape_tex(k)
        wrap = r"\[ %s \]" % tex if mode == "display" else r"$%s$" % tex
        pages.append(r"\begin{preview}%s\end{preview}" % wrap)
    doc = TEX_TEMPLATE % ("\n\\newpage\n".join(pages))

    work = tempfile.mkdtemp(prefix="rendermath-")
    try:
        open(os.path.join(work, "m.tex"), "w").write(doc)
        r = subprocess.run(["latex", "-interaction=nonstopmode", "-halt-on-error", "m.tex"],
                           cwd=work, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-3000:])
            sys.exit(f"{slug}: latex failed")

        vbre = re.compile(r"viewBox='([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)'")
        meta = {}
        for page, (k, mode, fn) in enumerate(items, start=1):
            out_svg = os.path.join(MATHDIR, fn)
            subprocess.run(["dvisvgm", f"--page={page}", "--no-fonts", "--exact-bbox",
                            "--bbox=preview", "-o", out_svg, "m.dvi"],
                           cwd=work, capture_output=True, text=True)
            if not os.path.exists(out_svg):
                sys.exit(f"{slug}: dvisvgm failed on page {page}: {k[:60]}")
            svg = open(out_svg).read()
            svg = re.sub(r"(<svg version='1\.1'[^>]*?)>", r"\1 fill='%s'>" % INK, svg, count=1)
            open(out_svg, "w").write(svg)
            _, min_y, _, h = map(float, vbre.search(svg).groups())
            meta[k] = dict(fn=fn,
                           h=h / BASE_PT,                 # height in em of body text
                           valign=-(min_y + h) / BASE_PT) # baseline offset (depth below baseline)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    def tag(k, display):
        m = meta[k]
        alt = html.escape(unescape_tex(k), quote=True)
        cls = "matheq matheq--display" if display else "matheq"
        style = f'height:{m["h"]:.3f}em'
        if not display:
            style += f';vertical-align:{m["valign"]:.3f}em'
        return f'<img class="{cls}" src="{relpath}/{m["fn"]}" alt="{alt}" style="{style}">'

    out = re.sub(r"\$\$(.+?)\$\$", lambda mm: tag(mm.group(1).strip(), True), src, flags=re.S)
    out = re.sub(r"\$(.+?)\$", lambda mm: tag(mm.group(1).strip(), False), out, flags=re.S)
    open(out_path, "w").write(out)
    print(f"{slug}: {len(display)} display + {len(inline)} inline equations -> {out_path}")


if __name__ == "__main__":
    main()
