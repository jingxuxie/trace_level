# TraceBreak Paper Draft

Compile from this directory:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
latexmk -pdf -interaction=nonstopmode supplement.tex
```

The current draft uses COLM 2026 style files refreshed from the official
`Template-2026.zip` archive and builds to a 6-page PDF under `latexmk`.

Current source files:

- `main.tex`: COLM-format workshop-paper draft.
- `supplement.tex`: standalone supplementary material with artifact map, metric definitions, protocol details, confidence-interval tables, and example trace.
- `references.bib`: bibliography starter.
- `tables/api_gpt41mini_24_ci.md` and `.tex`: API result table with bootstrap confidence intervals.
- `tables/deterministic_120_ci.md` and `.tex`: deterministic validation table with bootstrap confidence intervals.
- `tables/example_traces.md`: compact trace pair for appendix or figure conversion.
- `figures/*.svg`: auxiliary paper-facing visual artifacts. `main.tex` embeds a compact TikZ schematic directly because this environment has no SVG-to-PDF converter.
- `colm2026_conference.sty`, `colm2026_conference.bst`, `natbib.sty`, `fancyhdr.sty`, and `math_commands.tex`: local template files copied from `Template-2026.zip`.

The working checkout also keeps `colm_template/Template-2026/` as provenance for
the latest template rebase. The submission bundle rebuilds from the paper-root
style files above, so the extracted template example is not required.
