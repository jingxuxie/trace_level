# TraceBreak Submission Checklist

Use this checklist before uploading the workshop submission or sharing the
artifact.

## Required Files

- `paper/main.pdf`: anonymous main paper.
- `paper/supplement.pdf`: anonymous supplement.
- `REPRODUCIBILITY.md`: end-to-end reproduction commands.
- `ARTIFACT_MANIFEST.md`: submission-bundle inventory and exclusions.
- `README.md`: short project orientation.
- `tracebreak/`, `tests/`, `data/tasks_tracebreak_120.jsonl`: source, tests, and benchmark tasks.
- `results/raw_traces/`: JSONL traces supporting the reported tables.
- `results/tables/` and `paper/tables/`: metric and paper-facing tables.

## Do Not Include

- API keys or local secret files.
- `results/api_cache/` unless a reviewer explicitly needs cached provider
  responses; the raw trace JSONL files are sufficient for the reported metrics.
- Local TeX logs, auxiliary files, or machine-specific build products except
  the final PDFs.
- Any path containing a username or local home directory.

## Verification Commands

Run from the repository root:

```bash
conda run -n trace_level python -m unittest tests/test_policies.py tests/test_api_normalization.py
conda run -n trace_level python -m compileall -q tracebreak tests
conda run -n trace_level python -m tracebreak.analysis.verify_claims
python scripts/build_submission_bundle.py
```

Run from `paper/`:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
latexmk -pdf -interaction=nonstopmode supplement.tex
```

Optional anonymity scan:

```bash
rg -n "eston|/home|apikey|api key" README.md REPRODUCIBILITY.md SUBMISSION_CHECKLIST.md paper/*.tex tracebreak
pdftotext paper/main.pdf - | rg -n "eston|/home|apikey|api key"
pdftotext paper/supplement.pdf - | rg -n "eston|/home|apikey|api key"
```

The source scan should only show the generic `../apikey.txt` placeholder in API
reproduction instructions, not a real local path or secret.

The bundle command writes `dist/tracebreak_submission_bundle.zip` and excludes
API caches, TeX auxiliary files, local control directories, and internal notes.
