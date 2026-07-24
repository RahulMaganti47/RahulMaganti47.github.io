# Personal site build.
#
# Pages that contain math are authored in content/ with LaTeX kept as
# $...$ / $$...$$, then rendered to static SVGs and written to their served
# location. Everything else in the repo is plain static HTML, edited in place.
#
# Requires TeX Live / MacTeX (latex, dvisvgm) on PATH for the math targets.

# One entry per math page: "served.html:source.html". Render always runs
# (it's cheap and deterministic), which keeps `make clean-math && make math`
# from silently skipping regeneration.
MATH_PAGES = writing/synthesis-constrained-diffusion.html:content/writing/synthesis-constrained-diffusion.html

.PHONY: math serve clean-math

# Render math for all math pages.
math:
	@for pair in $(MATH_PAGES); do \
	  out=$${pair%%:*}; src=$${pair##*:}; \
	  python3 build/render_math.py $$src $$out; \
	done

# Serve the site locally for preview.
serve:
	python3 -m http.server 8080 --bind 127.0.0.1

# Remove all generated equation SVGs (regenerate with `make math`).
clean-math:
	rm -f assets/math/*.svg
