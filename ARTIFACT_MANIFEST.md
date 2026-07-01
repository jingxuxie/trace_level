# TraceBreak Artifact Manifest

This manifest describes the anonymized artifact package for the TraceBreak
paper draft. Build it with:

```bash
python scripts/build_submission_bundle.py
```

The default output is `dist/tracebreak_submission_bundle.zip`.
Before sharing the bundle, run the complete local gate:

```bash
conda run -n trace_level python scripts/run_release_checks.py
```

## Included Materials

- `paper/main.pdf` and `paper/supplement.pdf`: compiled anonymous paper and
  supplement.
- `paper/main.tex`, `paper/supplement.tex`, `paper/references.bib`, local COLM
  style files refreshed from `Template-2026.zip`, `paper/tables/`, and
  `paper/figures/`: source needed to inspect and rebuild the paper artifacts.
- `paper/related_work_notes.md`: conservative positioning notes for adjacent
  prompt-injection, runtime-enforcement, hidden-policy, and multi-agent-security
  work.
- `paper/tables/api_gpt41mini_24_by_category.md` and `.tex`: compact
  category-level API table for the supplement.
- `paper/tables/api_gpt41mini_category_examples.md`: one concrete risky
  API-local example per policy category, aligned with the matching TraceGuard
  block.
- `paper/figures/api_security_utility.tex` and `.svg`: generated
  security-utility frontier for the reported API subset.
- `paper/tables/authority_transfer_deterministic_120.md` and `.tex`:
  deterministic multi-agent authority-transfer table.
- `paper/tables/injection_overlay_deterministic_120.md` and `.tex`:
  deterministic indirect-injection overlay stress table.
- `paper/tables/decoy_stress_deterministic_120.md` and `.tex`:
  deterministic decoy-ambiguity clutter stress table.
- `paper/tables/same_action_replay_gpt41mini_24.md` and `.tex`:
  counterfactual replay table applying alternate defenses to fixed API-local
  action traces.
- `paper/tables/api_gpt41mini_visibility_gap_audit.tex`: compact supplement
  table showing which policy categories visible review can and cannot catch on
  fixed API-local actions.
- `paper/tables/api_gpt41mini_source_ref_compliance.tex`: compact supplement
  table checking that cached cooperative API write sinks carry valid nonempty
  source references before the source-reference stress tests.
- `paper/tables/source_ref_ablation_gpt41mini_24.md`: paper-facing
  source-reference robustness table covering missing, corrupted, and
  intermediate-erased provenance replays.
- `paper/tables/api_gpt41mini_policy_prompt_diagnostics.tex`: compact
  supplement table attributing policy-prompt avoided violations to abstention
  or changed sink targets rather than runtime enforcement.
- `paper/tables/traceguard_block_reason_audit.tex`: compact supplement table
  checking that TraceGuard risky blocks use the expected category-aligned reason
  codes in deterministic and API traces.
- `paper/tables/traceguard_repair_oracle_60.md`: full scripted repair-oracle
  upper-bound table over all 60 blocked risky TraceGuard traces.
- `tracebreak/`, `tests/`, and `pyproject.toml`: benchmark, policy monitors,
  experiment runners, block-and-recover runner support, analysis code, and unit
  tests. The API runner supports both Chat Completions mode for reproducing the
  cached `gpt-4.1-mini` subset and Responses mode for planned GPT-5 sweeps. It
  records provider-reported token usage when available, the metric script
  aggregates token totals for budgeted model sweeps, and
  `tracebreak.analysis.estimate_api_cost` provides a no-API-call cost preflight
  for modern-model sweeps, and `tracebreak.analysis.api_sweep_status` reports
  resumable sweep completion plus remaining budget with budget-capped resume
  commands, including a 24-task role-routed `api_multi_*` topology preflight
  and a 24-task no-source-ref-instruction prompt/schema ablation preflight.
  `tracebreak.analysis.api_paid_smoke_preflight` validates the first
  planned paid `gpt-5.4-mini` Responses smoke payload and budget guard, and
  writes a redacted payload snapshot, without reading the API key or making a
  network call.
  `tracebreak.analysis.research_readiness` records which minimum-package items
  are complete, which optional no-spend hardening artifacts are present, and
  which modern-model/topology evidence remains blocked on paid API rows.
- `data/tasks_tracebreak_120.jsonl`: 120 paired risky/safe-control benchmark
  tasks.
- `results/benchmark_fact_audit.csv` and
  `results/tables/benchmark_fact_audit.md`: no-spend audit localizing the
  decisive hidden or visible policy fact for each benchmark category.
- `results/benchmark_coverage_audit.csv` and
  `results/tables/benchmark_coverage_audit.md`: no-spend audit reporting task
  counts, complete pairs, world seeds, sink tools, flow archetypes,
  visible/hidden facts, and scripted trace lengths.
- `results/bibliography_audit.csv` and
  `results/tables/bibliography_audit.md`: no-spend audit checking TeX citation
  keys, BibTeX entries, generated bibliography entries, arXiv identifier shape,
  removed unsupported keys, and LaTeX/BibTeX undefined-citation warnings.
- `results/claim_boundary_audit.csv` and
  `results/tables/claim_boundary_audit.md`: no-spend audit checking that the
  paper and readiness report keep API-subset, preliminary-model,
  synthetic-data, provenance, live-recovery, and modern-model-evidence limits
  explicit.
- `results/api_prompt_surface_audit.csv` and
  `results/tables/api_prompt_surface_audit.md`: no-spend audit confirming that
  model-visible API prompts omit hidden provenance-tag fields and benchmark
  labels, while source-reference, policy-prompt, and multi-agent instructions
  appear only in the intended conditions.
- `results/api_recovery_prompt_audit.csv` and
  `results/tables/api_recovery_prompt_audit.md`: no-spend audit confirming
  recovery guidance is serialized only in post-block prompts after
  defense-blocked write sinks, not before blocks or on safe controls.
- `results/api_gpt41mini_critic_baseline_audit.csv` and
  `results/tables/api_gpt41mini_critic_baseline_audit.md`: no-spend audit
  reporting visible-critic versus metadata-critic information boundaries and
  lower-bound sink-review call overhead on fixed API-local actions.
- Reported deterministic traces:
  `single_local`, `multi_local`, `dlp`, `visible_policy`, and `traceguard`.
- Reported hardened deterministic trace:
  `traceguard_inferred`, a first-class runtime-inferred provenance monitor
  that matches TraceGuard on the clean 120-task scripted benchmark.
- Reported deterministic indirect-injection overlay traces:
  `multi_local_injection_overlay`, `dlp_injection_overlay`,
  `visible_policy_injection_overlay`, `traceguard_injection_overlay`, and
  `traceguard_inferred_injection_overlay`.
- Reported deterministic decoy-ambiguity stress traces:
  `multi_local_decoy_stress`, `dlp_decoy_stress`,
  `visible_policy_decoy_stress`, `traceguard_decoy_stress`, and
  `traceguard_inferred_decoy_stress`.
- Reported API traces for `gpt-4.1-mini`: two 12-task offsets for
  `api_local`, `api_dlp`, `api_policy_prompt`, and `api_traceguard`.
- Reported same-action replay traces for `gpt-4.1-mini`: DLP, visible-policy,
  metadata-critic, and TraceGuard applied offline to the two `api_local`
  offsets.
- Reported source-reference robustness replay traces for `gpt-4.1-mini`:
  `api_traceguard_drop_at_sink_replay` and
  `api_traceguard_inferred_drop_at_sink_replay`, plus
  `api_traceguard_strict_drop_at_sink_replay`. The artifact also includes the
  corrupted-reference variants:
  `api_traceguard_corrupt_at_sink_replay`,
  `api_traceguard_inferred_corrupt_at_sink_replay`, and
  `api_traceguard_strict_corrupt_at_sink_replay`, plus intermediate-transform
  erasure variants:
  `api_traceguard_drop_intermediate_replay`,
  `api_traceguard_inferred_drop_intermediate_replay`, and
  `api_traceguard_strict_drop_intermediate_replay`.
- Reported repair-oracle replay traces:
  `api_traceguard_repair_oracle` for the `gpt-4.1-mini` API subset and
  `traceguard_repair_oracle_60` for all 60 risky scripted TraceGuard blocks.
- `results/metrics.csv`, `results/api_gpt41mini_24_metrics.csv`,
  `results/injection_overlay_metrics.csv`,
  `results/decoy_stress_metrics.csv`,
  `results/api_gpt41mini_same_action_replay_metrics.csv`,
  `results/api_gpt41mini_visibility_gap_audit.csv`,
  `results/api_gpt41mini_critic_baseline_audit.csv`,
  `results/api_gpt41mini_source_ref_compliance.csv`,
  `results/api_gpt41mini_source_ref_ablation_24_metrics.csv`,
  `results/api_gpt41mini_repair_oracle_metrics.csv`,
  `results/traceguard_repair_oracle_60_metrics.csv`,
  `results/api_gpt41mini_paired_tests.csv`,
  `results/api_gpt41mini_policy_prompt_diagnostics.csv`,
  `results/traceguard_block_reason_audit.csv`,
  `results/benchmark_fact_audit.csv`,
  `results/benchmark_coverage_audit.csv`,
  `results/bibliography_audit.csv`,
  `results/claim_boundary_audit.csv`,
  `results/traceguard_inferred_metrics.csv`,
  `results/api_prompt_surface_audit.csv`,
  `results/api_recovery_prompt_audit.csv`,
  `results/api_modern_sweep_cost_estimate.csv`,
  `results/api_gpt55_48_cost_estimate.csv`,
  `results/api_gpt54mini_120_plus_visible_cost_estimate.csv`,
  `results/api_gpt55_48_plus_visible_cost_estimate.csv`,
  `results/api_gpt54mini_no_source_ref_instruction_24_cost_estimate.csv`,
  `results/api_gpt54mini_120_sweep_status.csv`,
  `results/api_gpt55_48_sweep_status.csv`,
  `results/api_gpt54mini_120_plus_visible_sweep_status.csv`,
  `results/api_gpt55_48_plus_visible_sweep_status.csv`,
  `results/api_gpt54mini_multi_topology_24_sweep_status.csv`,
  `results/api_gpt54mini_inferred_guard_24_sweep_status.csv`,
  `results/api_gpt54mini_no_source_ref_instruction_24_sweep_status.csv`,
  `results/api_modern_sweep_launch_audit.csv`,
  `results/api_gpt54mini_paid_smoke_preflight.csv`,
  `results/api_gpt54mini_paid_smoke_payload.json`,
  `results/api_gpt54mini_no_source_ref_instruction_preflight.csv`,
  `results/api_gpt54mini_no_source_ref_instruction_payload.json`,
  `results/research_readiness_report.csv`,
  `results/tables/main_results.md`, `results/tables/injection_overlay_results.md`,
  `results/tables/decoy_stress_results.md`,
  `results/tables/api_gpt41mini_24_results.md`,
  `results/tables/api_gpt41mini_same_action_replay_results.md`,
  `results/tables/api_gpt41mini_visibility_gap_audit.md`,
  `results/tables/api_gpt41mini_critic_baseline_audit.md`,
  `results/tables/api_gpt41mini_source_ref_compliance.md`,
  `results/tables/api_gpt41mini_source_ref_ablation_24_results.md`,
  `results/tables/api_gpt41mini_repair_oracle_results.md`,
  `results/tables/traceguard_repair_oracle_60_results.md`,
  `results/tables/api_gpt41mini_paired_tests.md`,
  `results/tables/api_gpt41mini_policy_prompt_diagnostics.md`,
  `results/tables/traceguard_block_reason_audit.md`,
  `results/tables/benchmark_fact_audit.md`,
  `results/tables/benchmark_coverage_audit.md`,
  `results/tables/bibliography_audit.md`,
  `results/tables/claim_boundary_audit.md`,
  `results/tables/traceguard_inferred_results.md`,
  `results/tables/api_prompt_surface_audit.md`,
  `results/tables/api_recovery_prompt_audit.md`,
  `results/tables/api_modern_sweep_cost_estimate.md`,
  `results/tables/api_gpt55_48_cost_estimate.md`,
  `results/tables/api_gpt54mini_120_plus_visible_cost_estimate.md`,
  `results/tables/api_gpt55_48_plus_visible_cost_estimate.md`,
  `results/tables/api_gpt54mini_no_source_ref_instruction_24_cost_estimate.md`,
  `results/tables/api_gpt54mini_120_sweep_status.md`,
  `results/tables/api_gpt55_48_sweep_status.md`,
  `results/tables/api_gpt54mini_120_plus_visible_sweep_status.md`,
  `results/tables/api_gpt55_48_plus_visible_sweep_status.md`,
  `results/tables/api_gpt54mini_multi_topology_24_sweep_status.md`,
  `results/tables/api_gpt54mini_inferred_guard_24_sweep_status.md`,
  `results/tables/api_gpt54mini_no_source_ref_instruction_24_sweep_status.md`,
  `results/tables/api_modern_sweep_launch_audit.md`,
  `results/tables/api_gpt54mini_paid_smoke_preflight.md`,
  `results/tables/api_gpt54mini_no_source_ref_instruction_preflight.md`,
  `results/tables/api_paid_smoke_next_step.md`,
  `results/tables/research_readiness_report.md`, and
  `results/EXPERIMENT_SUMMARY.md`.
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
- `additional_experiments_plan.md`, which is a follow-up planning note, not a
  review artifact.

## Verification

Before submission, run:

```bash
conda run -n trace_level python -m unittest tests/test_policies.py tests/test_api_normalization.py
conda run -n trace_level python -m unittest tests/test_openai_client.py
conda run -n trace_level python -m unittest tests/test_cost_estimator.py
conda run -n trace_level python -m unittest tests/test_api_sweep_status.py
conda run -n trace_level python -m unittest tests/test_api_paid_smoke_preflight.py
conda run -n trace_level python -m unittest tests/test_research_readiness.py
conda run -n trace_level python -m unittest tests/test_bibliography_audit.py
conda run -n trace_level python -m unittest tests/test_claim_boundary_audit.py
conda run -n trace_level python -m unittest tests/test_benchmark_fact_audit.py
conda run -n trace_level python -m unittest tests/test_benchmark_coverage_audit.py
conda run -n trace_level python -m unittest tests/test_prompt_surface_audit.py
conda run -n trace_level python -m unittest tests/test_recovery_prompt_audit.py
conda run -n trace_level python -m unittest tests/test_decoy_stress.py
conda run -n trace_level python -m unittest tests/test_source_ref_compliance.py
conda run -n trace_level python -m unittest tests/test_source_ref_ablation.py
conda run -n trace_level python -m unittest tests/test_paired_tests.py
conda run -n trace_level python -m unittest tests/test_category_examples.py
conda run -n trace_level python -m unittest tests/test_critic_baseline_audit.py
conda run -n trace_level python -m compileall -q tracebreak tests
conda run -n trace_level python -m tracebreak.analysis.verify_claims
python scripts/build_submission_bundle.py
```

The bundle builder checks that included text files do not contain the local home
path or an apparent OpenAI API key.
The claim verifier also checks the paper page split, bundle exclusions, included
text files, and rendered PDFs for local-path or key leaks.
The release gate additionally runs unit tests, bytecode compilation, LaTeX
rebuilds, LaTeX log scan, expected PDF page-count checks, claim verification,
bundle rebuild, and bundle spot-checks in one command.
