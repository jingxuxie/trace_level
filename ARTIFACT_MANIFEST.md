# TraceBreak Artifact Manifest

This manifest describes the anonymized artifact package for the TraceBreak
paper draft. Build it with:

```bash
python scripts/build_submission_bundle.py
```

The default output is `dist/tracebreak_submission_bundle.zip`.

## Included Materials

- `paper/main.pdf` and `paper/supplement.pdf`: compiled anonymous paper and
  supplement.
- `paper/main.tex`, `paper/supplement.tex`, `paper/references.bib`, local COLM
  style files refreshed from `Template-2026.zip`, `paper/tables/`, and
  `paper/figures/`: source needed to inspect and rebuild the paper artifacts.
- `tracebreak/`, `tests/`, and `pyproject.toml`: benchmark, policy monitors,
  experiment runners, analysis code, and unit tests.
- `data/tasks_tracebreak_120.jsonl`: 120 paired risky/safe-control benchmark
  tasks.
- Reported deterministic traces:
  `single_local`, `multi_local`, `dlp`, `visible_policy`, and `traceguard`.
- Reported API traces for `gpt-4.1-mini`: two 12-task offsets for
  `api_local`, `api_dlp`, `api_policy_prompt`, and `api_traceguard`.
- `results/metrics.csv`, `results/api_gpt41mini_24_metrics.csv`,
  `results/tables/main_results.md`, `results/tables/api_gpt41mini_24_results.md`,
  and `results/EXPERIMENT_SUMMARY.md`.
- `README.md`, `REPRODUCIBILITY.md`, `SUBMISSION_CHECKLIST.md`, and this
  manifest.

## Excluded Materials

- API keys and local secret files.
- `results/api_cache/`, because the reported JSONL traces are sufficient for
  metrics and the cache may contain provider metadata.
- TeX auxiliary logs and machine-specific build files, including `.aux`,
  `.log`, `.fls`, `.fdb_latexmk`, `.out`, `.blg`, and generated `.bbl` files.
- Local control directories such as `.git`, `.agents`, `.codex`, and `dist/`.
- Exploratory or obsolete smoke/nano API runs that are not reported in the
  paper.
- `trace_level_policy_workshop_plan.md`, which is an internal planning note, not
  a review artifact.

## Verification

Before submission, run:

```bash
conda run -n trace_level python -m unittest tests/test_policies.py tests/test_api_normalization.py
conda run -n trace_level python -m compileall -q tracebreak tests
conda run -n trace_level python -m tracebreak.analysis.verify_claims
python scripts/build_submission_bundle.py
```

The bundle builder checks that included text files do not contain the local home
path or an apparent OpenAI API key.
