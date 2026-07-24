# Build

Most of this site is plain static HTML, edited in place and served directly by
GitHub Pages. Pages that contain **math** are the exception: the math is
pre-rendered to static SVG at build time so it renders with no client-side
library (no MathJax/KaTeX), which means it can't be broken by a blocked CDN,
disabled JavaScript, or a stale cache.

## How math pages work

A math page has two files:

| File | Role |
| --- | --- |
| `content/writing/<name>.html` | **Source of truth.** Author here; keep equations as `$...$` (inline) and `$$...$$` (display). |
| `writing/<name>.html` | **Generated + served.** Produced by the build; do not hand-edit. |

`build/render_math.py` reads the source, renders each unique equation to
`assets/math/<name>-{d,m}<n>.svg` via `latex` + `dvisvgm`, and writes the served
page with `<img class="matheq">` tags. Inline equations get a per-equation
`vertical-align` computed from the glyph bounding box so they sit on the text
baseline. SVG filenames are namespaced by page, so multiple pages never collide.

## Editing an equation

1. Edit the LaTeX in `content/writing/<name>.html`.
2. Run `make math` (rebuilds only pages whose source changed).
3. Commit the source, the regenerated `writing/<name>.html`, and any changed
   `assets/math/*.svg`.

## Adding a new math page

1. Create `content/writing/<name>.html` with `$...$` / `$$...$$`.
2. Add `writing/<name>.html` to `MATH_PAGES` in the `Makefile`.
3. `make math`.

Equation styling (`.matheq`, `.matheq--display`) lives in `style.css`.

## Requirements

`latex` and `dvisvgm` on `PATH` — install TeX Live (Linux) or MacTeX (macOS).

```
make math        # render math for all math pages
make serve       # preview at http://127.0.0.1:8080
make clean-math  # delete all generated equation SVGs (regenerate with `make math`)
```
