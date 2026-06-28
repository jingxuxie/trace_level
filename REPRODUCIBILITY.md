# TraceBreak Reproducibility

This checklist reproduces the current TraceBreak artifacts from the repository
root. It assumes the conda environment is named `trace_level`.

## Environment

```bash
conda run -n trace_level python --version
conda run -n trace_level python -m compileall -q tracebreak tests
conda run -n trace_level python -m unittest tests/test_policies.py tests/test_api_normalization.py
conda run -n trace_level python -m tracebreak.analysis.verify_claims
```

The OpenAI API runner reads the key from `../apikey.txt` by default when run
from the repository root; override this with `--api-key-path` if needed. It
caches responses in `results/api_cache`. Re-running the exact commands below
should reuse cached responses where available.

## Generate Tasks

```bash
conda run -n trace_level python -m tracebreak.data.generate_tasks \
  --out data/tasks_tracebreak_120.jsonl
```

Expected dataset: 120 tasks, with 10 risky and 10 safe-control tasks for each
of 6 categories.

## Deterministic Matrix

```bash
for condition in single_local multi_local dlp visible_policy traceguard; do
  conda run -n trace_level python -m tracebreak.experiments.run_condition \
    --tasks data/tasks_tracebreak_120.jsonl \
    --condition "$condition" \
    --out "results/raw_traces/${condition}.jsonl"
done

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs \
    results/raw_traces/single_local.jsonl \
    results/raw_traces/multi_local.jsonl \
    results/raw_traces/dlp.jsonl \
    results/raw_traces/visible_policy.jsonl \
    results/raw_traces/traceguard.jsonl \
  --out-csv results/metrics.csv \
  --out-md results/tables/main_results.md
```

Expected headline: local guards and DLP allow all risky scripted traces, while
TraceGuard blocks all risky traces and allows all safe controls.

## API Subset

The reported API subset uses `gpt-4.1-mini`, two 12-task offsets, and four
conditions. These commands may make live API calls if the cache is missing.

```bash
for condition in api_local api_dlp api_policy_prompt api_traceguard; do
  conda run -n trace_level python -m tracebreak.experiments.run_api_condition \
    --tasks data/tasks_tracebreak_120.jsonl \
    --condition "$condition" \
    --model gpt-4.1-mini \
    --limit 12 \
    --out "results/raw_traces/${condition}_gpt41mini_12.jsonl"

  conda run -n trace_level python -m tracebreak.experiments.run_api_condition \
    --tasks data/tasks_tracebreak_120.jsonl \
    --condition "$condition" \
    --model gpt-4.1-mini \
    --offset 12 \
    --limit 12 \
    --out "results/raw_traces/${condition}_gpt41mini_seed1_12.jsonl"
done

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs results/raw_traces/api_*gpt41mini*_12.jsonl \
  --out-csv results/api_gpt41mini_24_metrics.csv \
  --out-md results/tables/api_gpt41mini_24_results.md
```

Expected headline: `api_local` and `api_dlp` produce local-pass violations on
all risky tasks; `api_policy_prompt` reduces but does not eliminate violations;
`api_traceguard` blocks all risky sink attempts and preserves safe-control
utility.

## Paper Tables And Figures

```bash
conda run -n trace_level python -m tracebreak.analysis.paper_tables \
  --runs results/raw_traces/api_*gpt41mini*_12.jsonl \
  --out-md paper/tables/api_gpt41mini_24_ci.md \
  --out-tex paper/tables/api_gpt41mini_24_ci.tex

conda run -n trace_level python -m tracebreak.analysis.paper_tables \
  --runs \
    results/raw_traces/single_local.jsonl \
    results/raw_traces/multi_local.jsonl \
    results/raw_traces/dlp.jsonl \
    results/raw_traces/visible_policy.jsonl \
    results/raw_traces/traceguard.jsonl \
  --out-md paper/tables/deterministic_120_ci.md \
  --out-tex paper/tables/deterministic_120_ci.tex

conda run -n trace_level python -m tracebreak.analysis.export_examples \
  --local-run results/raw_traces/api_local_gpt41mini_12.jsonl \
  --traceguard-run results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
  --out paper/tables/example_traces.md

conda run -n trace_level python -m tracebreak.analysis.make_figures \
  --runs results/raw_traces/api_*gpt41mini*_12.jsonl \
  --out-dir paper/figures
```

## Paper Build

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
latexmk -pdf -interaction=nonstopmode supplement.tex
pdfinfo main.pdf
pdfinfo supplement.pdf
```

Expected current build: `paper/main.pdf`, 6 pages, using the local COLM 2026
style files. The supplement builds as `paper/supplement.pdf`.
