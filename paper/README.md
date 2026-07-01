# TraceBreak Paper Draft

Compile from this directory:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
latexmk -pdf -interaction=nonstopmode supplement.tex
```

The current draft uses COLM 2026 style files refreshed from the official
`Template-2026.zip` archive and builds under `latexmk` to a 7-page main PDF
including references plus a 5-page standalone supplement. The non-reference
body ends on page 6.

Current source files:

- `main.tex`: COLM-format workshop-paper draft.
- `supplement.tex`: standalone supplementary material with artifact map, metric definitions, protocol details, rounded point-estimate tables, and example trace.
- `references.bib`: bibliography starter.
- `tables/api_gpt41mini_24_results.md` and `.tex`: API point-estimate table.
- `tables/deterministic_120_results.md` and `.tex`: deterministic validation
  point-estimate table.
- `tables/api_gpt41mini_visibility_gap_audit.tex`: compact table localizing
  visible-policy replay failures to hidden metadata categories.
- `tables/api_gpt41mini_source_ref_compliance.tex`: compact audit table showing
  cached cooperative API sinks carry valid nonempty source references before the
  robustness stress tests.
- `tables/source_ref_ablation_gpt41mini_24.md`: paper-facing source-reference
  robustness ablation table, including missing, corrupted, and intermediate
  provenance-erasure replays.
- `tables/api_gpt41mini_policy_prompt_diagnostics.tex`: compact diagnostic
  table for policy-prompt non-enforcement failure modes.
- `tables/traceguard_block_reason_audit.tex`: compact audit table for
  TraceGuard reason-code/category alignment.
- `tables/example_traces.md`: compact trace pair for appendix or figure conversion.
- `tables/api_gpt41mini_category_examples.md`: one risky API-local example per
  policy category, aligned with the matching TraceGuard block.
- `figures/api_security_utility.tex`: generated TikZ security-utility frontier included in the supplement.
- `figures/*.svg`: auxiliary paper-facing visual artifacts. `main.tex` embeds a compact TikZ schematic directly because this environment has no SVG-to-PDF converter.
- `colm2026_conference.sty`, `colm2026_conference.bst`, `natbib.sty`, `fancyhdr.sty`, and `math_commands.tex`: local template files copied from `Template-2026.zip`.

The working checkout also keeps `colm_template/Template-2026/` as provenance for
the latest template rebase. The submission bundle rebuilds from the paper-root
style files above, so the extracted template example is not required.
