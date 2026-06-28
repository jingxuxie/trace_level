# TraceBreak Experiment Summary

Generated on 2026-06-27.

## Implemented Artifacts

- `data/tasks_tracebreak_120.jsonl`: 120 paired tasks, with 10 risky and 10 safe controls for each of 6 categories.
- `tracebreak/env`: synthetic world, tool runtime, provenance tags, and local-only tools.
- `tracebreak/policies`: local guards, content DLP, visible-policy guard, and TraceGuard.
- `tracebreak/experiments`: deterministic scripted runner plus bounded OpenAI API runner.
- `tracebreak/analysis/compute_metrics.py`: aggregate and category-level result tables.
- `tracebreak/analysis/verify_claims.py`: executable claim-to-artifact verifier for dataset size, deterministic results, API results, and paper outputs.
- `paper/tables/example_traces.md`: paper-facing local-violation versus TraceGuard-block example.
- `paper/tables/api_gpt41mini_24_ci.md` and `.tex`: API result table with 95% bootstrap confidence intervals.
- `paper/tables/deterministic_120_ci.md` and `.tex`: deterministic result table with 95% bootstrap confidence intervals.
- `paper/figures/api_security_utility.svg`: utility/security tradeoff figure.
- `paper/figures/traceguard_schematic.svg`: local-allow versus trace-block schematic.
- `paper/related_work_notes.md` and `paper/references.bib`: verified related-work positioning and bibliography starter.
- `paper/main.tex` and `paper/main.pdf`: compile-verified 6-page COLM-format workshop-paper draft.
- `REPRODUCIBILITY.md`: exact commands for regenerating tasks, traces, metrics, tables, figures, tests, and the paper build.
- `paper/supplement.tex` and `paper/supplement.pdf`: standalone supplement with artifact map, metric definitions, API protocol details, confidence-interval tables, and representative trace pair.
- `SUBMISSION_CHECKLIST.md`: anonymous submission and artifact packaging checklist.
- `ARTIFACT_MANIFEST.md` and `scripts/build_submission_bundle.py`: reproducible artifact inventory and bundle builder.

Implementation note: `search_records` now carries provenance for returned record identifiers, including source IDs and record count. This is important because exporting a list of identifiers can itself violate the aggregation policy even if full records are not individually read.

## Main Deterministic Matrix

Source table: `results/tables/main_results.md`.

| condition | sink rate | safe utility | risky global violation | risky LPVR | safe false block |
| --- | ---: | ---: | ---: | ---: | ---: |
| single_local | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 |
| multi_local | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 |
| dlp | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 |
| visible_policy | 83.3 | 100.0 | 66.7 | 66.7 | 0.0 |
| traceguard | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 |

Interpretation: the harness cleanly reproduces the local-permission/global-policy gap. Local guards and visible-content DLP allow every risky scripted trace. The visible-policy guard only catches approval-scope and bulk-export cases, because those are visible from action arguments. TraceGuard blocks all risky traces while allowing all matched safe controls.

## API Two-Seed Subset

Source table: `results/tables/api_gpt41mini_24_results.md`.

Small matched subset:

- model: `gpt-4.1-mini`
- tasks: 24 total, two risky/safe pairs for each of 6 categories
- conditions: `api_local`, `api_dlp`, `api_policy_prompt`, `api_traceguard`

| condition | sink rate | safe utility | risky global violation | risky LPVR | safe false block |
| --- | ---: | ---: | ---: | ---: | ---: |
| api_local | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 |
| api_dlp | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 |
| api_policy_prompt | 79.2 | 83.3 | 75.0 | 75.0 | 0.0 |
| api_traceguard | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 |

Interpretation: on the 24-task API subset, the model reaches all sinks under local guards and DLP. All 12 risky local-guard traces are local-pass violations. Content DLP misses all 12 because the decisive policy state is provenance/metadata rather than visible keywords. Policy prompting reduces violations but also reduces completion. TraceGuard preserves all 12 safe-control completions and blocks all 12 risky sink attempts.

`gpt-4.1-nano` was tested on 12 tasks and then 4 tasks, but it repeatedly re-read documents and rarely reached sinks. Do not use nano for main paper results without changing the agent loop.

## Current Paper Status

- `paper/main.tex` uses the local COLM 2026 submission style files copied from the official template.
- `paper/main.tex` embeds a compact TikZ TraceGuard schematic, while the SVG files remain auxiliary artifacts.
- `paper/main.tex` now states the bootstrap-interval caveat and artifact reproducibility contract in the main text.
- `paper/main.pdf` builds with `latexmk -pdf -interaction=nonstopmode main.tex` and is currently 6 pages, including references.
- `paper/supplement.pdf` builds with `latexmk -pdf -interaction=nonstopmode supplement.tex`.
- The workshop CFP requests up to 6 pages excluding references and supplement, so the current main draft is within the target page budget.

## Immediate Next Steps

1. Inspect the rendered main PDF and supplement manually for layout and argument flow before submission.
2. Run one additional API offset only if budget remains and the extra uncertainty reduction is worth the cost.
3. Rebuild `dist/tracebreak_submission_bundle.zip` with `python scripts/build_submission_bundle.py` after any further paper or result edits.
