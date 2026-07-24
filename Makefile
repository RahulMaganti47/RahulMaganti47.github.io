# Personal site build.
#
# Pages that contain math are authored in content/ with LaTeX kept as
# $...$ / $$...$$, then rendered to static SVGs and written to their served
# location. Everything else in the repo is plain static HTML, edited in place.
#
# Requires TeX Live / MacTeX (latex, dvisvgm) on PATH for the math targets.

# Add a line here for each page that uses math.
MATH_PAGES = writing/synthesis-constrained-diffusion.html

.PHONY: math serve clean-math

# Render math for all math pages (only rebuilds pages whose source changed).
math: $(MATH_PAGES)

# Pattern rule: writing/foo.html is built from content/writing/foo.html.
writing/%.html: content/writing/%.html build/render_math.py
	python3 build/render_math.py $< $@

# Serve the site locally for preview.
serve:
	python3 -m http.server 8080 --bind 127.0.0.1

# Remove all generated equation SVGs (regenerate with `make math`).
clean-math:
	rm -f assets/math/*.svg
