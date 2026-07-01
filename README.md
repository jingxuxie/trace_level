# TraceBreak

TraceBreak is a small synthetic benchmark for trace-level policy violations in
tool-using agent workflows. The current implementation includes deterministic
experiments, a bounded API subset, and a COLM-format paper draft:

- paired risky and safe-control tasks;
- local tool guards that only validate action-local permissions;
- visible-content and visible-policy baselines;
- TraceGuard, a deterministic provenance monitor over full traces;
- deterministic multi-agent authority-transfer analysis;
- deterministic indirect-injection overlay stress test, now including
  runtime-inferred TraceGuard;
- deterministic decoy-ambiguity clutter stress test, now including
  runtime-inferred TraceGuard;
- same-action offline defense replays over fixed API-local action traces;
- a cached API source-reference compliance audit showing executed sinks carry
  valid nonempty refs before provenance stress tests;
- a source-reference robustness ablation covering missing/corrupted sink refs
  and erased intermediate refs, with StrictTraceGuard and runtime-inferred
  provenance replays;
- a first-class `traceguard_inferred` monitor that performs runtime-owned sink
  tag inference and matches TraceGuard on clean deterministic traces;
- a policy-prompt failure diagnostic that separates abstention and changed
  sink targets from runtime enforcement;
- a TraceGuard block-reason audit for category-aligned explanations;
- a same-action visibility-gap audit separating visible sink facts from hidden
  metadata requirements;
- a same-action critic-baseline audit that accounts for visible-critic and
  metadata-critic information boundaries plus lower-bound review-call overhead;
- a no-spend benchmark policy-fact audit localizing each category's decisive
  hidden or visible fact across all 120 paired tasks;
- a no-spend benchmark coverage audit covering seeds, pair completeness, sink
  tools, flow archetypes, visible/hidden facts, and scripted trace lengths;
- a no-spend bibliography integrity audit checking TeX citations, BibTeX keys,
  generated bibliography entries, arXiv identifiers, and LaTeX/BibTeX warnings;
- a no-spend claim-boundary audit checking that API-scope, synthetic-data,
  provenance-dependency, recovery, and modern-model-evidence limitations remain
  explicit;
- a no-spend API prompt-surface audit confirming generated prompts omit hidden
  provenance-tag keys and benchmark labels while preserving expected policy and
  multi-agent prompt boundaries;
- a no-spend API recovery-prompt audit confirming recovery guidance appears
  only after defense-blocked write sinks and never before a block or on safe controls;
- matched-pair counts over cached API task IDs for the main comparisons;
- a rendered security-utility frontier figure for the API subset;
- optional provider-reported token accounting for future API sweeps;
- Chat Completions mode for cached `gpt-4.1-mini` traces and Responses mode
  for planned GPT-5 sweeps;
- role-routed `api_multi_*` conditions for future API topology comparisons
  with researcher, planner, and executor actors;
- a no-spend API cost preflight for budget-gated modern-model sweeps;
- resumable API JSONL sweeps with `--resume` to avoid duplicate paid calls;
- no-spend API sweep status reports with remaining-cost and budget-capped resume commands;
- a no-spend 24-task GPT-5.4-mini topology status report for
  `api_single_local`, `api_multi_local`, `api_multi_policy_prompt`, and
  `api_multi_traceguard`;
- a no-spend 24-task GPT-5.4-mini status report for a future
  `api_traceguard_inferred` run;
- a no-spend 24-task GPT-5.4-mini no-source-ref-instruction ablation status
  report and schema-only payload preflight for future prompt/schema validation;
- optional five-condition modern-sweep cost/status reports that include
  `api_visible_policy` and flag when the extra baseline fits the budget;
- a no-spend modern-sweep launch audit that checks generated paid-run commands
  for Responses mode, resume/cache flags, output paths, API-key path, and
  budget caps;
- a no-spend paid-smoke preflight that validates the first GPT-5.4 Responses
  payload, strict schema, source-reference contract, redacted payload snapshot,
  and budget guard before any external call is approved;
- a no-spend research-readiness report tracking minimum paper-package items,
  optional hardening artifacts, and paid-API-blocked modern-model/topology rows;
- JSONL trace logs and reproducible metrics;
- paper tables, per-category example trace exports, SVG figures,
  `paper/main.pdf`, and `paper/supplement.pdf`.

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

Run the full no-spend release gate:

```bash
conda run -n trace_level python scripts/run_release_checks.py
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
