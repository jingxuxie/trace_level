# TraceBreak

TraceBreak is a small synthetic benchmark for trace-level policy violations in
tool-using agent workflows. The current implementation includes deterministic
experiments, a bounded API subset, and a COLM-format paper draft:

- paired risky and safe-control tasks;
- local tool guards that only validate action-local permissions;
- visible-content and visible-policy baselines;
- TraceGuard, a deterministic provenance monitor over full traces;
- JSONL trace logs and reproducible metrics;
- paper tables, SVG figures, `paper/main.pdf`, and `paper/supplement.pdf`.

For the full reproduction path, see `REPRODUCIBILITY.md`.

Generate tasks:

```bash
conda run -n trace_level python -m tracebreak.data.generate_tasks --out data/tasks_tracebreak_120.jsonl
```

Run a condition:

```bash
conda run -n trace_level python -m tracebreak.experiments.run_condition \
  --tasks data/tasks_tracebreak_120.jsonl \
  --condition traceguard \
  --out results/raw_traces/traceguard.jsonl
```

Compute tables:

```bash
conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs results/raw_traces/*.jsonl \
  --out-csv results/metrics.csv \
  --out-md results/tables/main_results.md
```

Verify headline claims against the current artifacts:

```bash
conda run -n trace_level python -m tracebreak.analysis.verify_claims
```

Build the paper:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
latexmk -pdf -interaction=nonstopmode supplement.tex
```

Build the anonymized artifact bundle:

```bash
python scripts/build_submission_bundle.py
```
