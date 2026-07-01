# TraceBreak Reproducibility

This checklist reproduces the current TraceBreak artifacts from the repository
root. The current follow-up experiments were verified with the conda environment
named `trace_level`.

## Environment

Run the complete no-spend release gate from the repository root:

```bash
conda run -n trace_level python scripts/run_release_checks.py
```

The release gate runs unit tests, bytecode compilation, LaTeX rebuilds, LaTeX
log and page-count checks, claim verification, bundle rebuild, and a spot check
that key release artifacts are present in the bundle. The individual debugging
commands are:

```bash
conda run -n trace_level python --version
conda run -n trace_level python -m compileall -q tracebreak tests
conda run -n trace_level python -m unittest \
  tests/test_policies.py tests/test_api_normalization.py \
  tests/test_cost_estimator.py tests/test_api_paid_smoke_preflight.py \
  tests/test_research_readiness.py \
  tests/test_bibliography_audit.py \
  tests/test_claim_boundary_audit.py \
  tests/test_decoy_stress.py \
  tests/test_source_ref_compliance.py tests/test_source_ref_ablation.py \
  tests/test_paired_tests.py tests/test_prompt_surface_audit.py \
  tests/test_category_examples.py
conda run -n trace_level python -m tracebreak.analysis.verify_claims
```

The OpenAI API runner reads the key from `../apikey.txt` by default when run
from the repository root; override this with `--api-key-path` if needed. It
caches responses in `results/api_cache`. Re-running the exact commands below
should reuse cached responses where available.
Pass `--resume` on budgeted runs to reuse matching rows already present in the
target JSONL and avoid repeating paid calls after an interrupted sweep.
The runner supports `--api-mode chat` for reproducing existing Chat Completions
traces and `--api-mode responses` for modern GPT-5 sweeps. The generated
modern-sweep resume commands use the Responses API mode and include
`--max-estimated-cost-usd` caps derived from each row's remaining conservative
budget estimate.

When the provider response includes `usage`, API task metrics record
`prompt_tokens`, `completion_tokens`, `total_tokens`, cached prompt tokens, and
reasoning tokens. `compute_metrics.py` aggregates these fields by condition, so
future model sweeps can report token totals and estimate dollar cost without
post-hoc log scraping.

## API Cost Preflight

Before starting any live modern-model sweep, estimate cost from the actual
TraceBreak prompts and current model prices. The estimator does not contact the
OpenAI API; it approximates token counts from prompt text, uses the scripted
trace shape to estimate nominal calls, and also reports a conservative
max-step budget.

```bash
conda run -n trace_level python -m tracebreak.analysis.estimate_api_cost \
  --models gpt-5.4-mini gpt-5.5 \
  --conditions api_local api_dlp api_policy_prompt api_traceguard \
  --limit 120 \
  --out-csv results/api_modern_sweep_cost_estimate.csv \
  --out-md results/tables/api_modern_sweep_cost_estimate.md

conda run -n trace_level python -m tracebreak.analysis.estimate_api_cost \
  --models gpt-5.5 \
  --conditions api_local api_dlp api_policy_prompt api_traceguard \
  --limit 48 \
  --out-csv results/api_gpt55_48_cost_estimate.csv \
  --out-md results/tables/api_gpt55_48_cost_estimate.md

conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.4-mini \
  --conditions api_local api_dlp api_policy_prompt api_traceguard \
  --limit 120 \
  --api-mode responses \
  --out-csv results/api_gpt54mini_120_sweep_status.csv \
  --out-md results/tables/api_gpt54mini_120_sweep_status.md

conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.5 \
  --conditions api_local api_dlp api_policy_prompt api_traceguard \
  --limit 48 \
  --api-mode responses \
  --out-csv results/api_gpt55_48_sweep_status.csv \
  --out-md results/tables/api_gpt55_48_sweep_status.md
```

Optional visible-policy modern-sweep planning uses the same no-spend tools but
adds `api_visible_policy` as a fifth condition:

```bash
conda run -n trace_level python -m tracebreak.analysis.estimate_api_cost \
  --models gpt-5.4-mini \
  --conditions api_local api_dlp api_policy_prompt api_traceguard api_visible_policy \
  --limit 120 \
  --out-csv results/api_gpt54mini_120_plus_visible_cost_estimate.csv \
  --out-md results/tables/api_gpt54mini_120_plus_visible_cost_estimate.md

conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.4-mini \
  --conditions api_local api_dlp api_policy_prompt api_traceguard api_visible_policy \
  --limit 120 \
  --api-mode responses \
  --out-csv results/api_gpt54mini_120_plus_visible_sweep_status.csv \
  --out-md results/tables/api_gpt54mini_120_plus_visible_sweep_status.md

conda run -n trace_level python -m tracebreak.analysis.estimate_api_cost \
  --models gpt-5.5 \
  --conditions api_local api_dlp api_policy_prompt api_traceguard api_visible_policy \
  --limit 48 \
  --out-csv results/api_gpt55_48_plus_visible_cost_estimate.csv \
  --out-md results/tables/api_gpt55_48_plus_visible_cost_estimate.md

conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.5 \
  --conditions api_local api_dlp api_policy_prompt api_traceguard api_visible_policy \
  --limit 48 \
  --api-mode responses \
  --out-csv results/api_gpt55_48_plus_visible_sweep_status.csv \
  --out-md results/tables/api_gpt55_48_plus_visible_sweep_status.md
```

No-spend planning for the P1 API topology comparison uses role-routed
`api_multi_*` conditions. In those runs the scaffold assigns search/read
actions to a researcher, summaries/approvals/memory writes/aggregation to a
planner, and sinks/memory reads/final answers to an executor while the model
still emits the same next-action JSON schema:

```bash
conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.4-mini \
  --conditions api_single_local api_multi_local api_multi_policy_prompt api_multi_traceguard \
  --limit 24 \
  --api-mode responses \
  --out-csv results/api_gpt54mini_multi_topology_24_sweep_status.csv \
  --out-md results/tables/api_gpt54mini_multi_topology_24_sweep_status.md
```

Expected headline: the topology comparison has 0/96 rows completed until
approved API spend exists, remains under `$1.30` under the conservative
max-step budget, and emits exact `--resume` commands for each condition.

Before running any paid modern sweep command, validate the generated launch
commands from the status reports:

```bash
conda run -n trace_level python -m tracebreak.analysis.modern_sweep_launch_audit \
  --status-csv \
    results/api_gpt54mini_120_sweep_status.csv \
    results/api_gpt55_48_sweep_status.csv \
    results/api_gpt54mini_120_plus_visible_sweep_status.csv \
    results/api_gpt55_48_plus_visible_sweep_status.csv \
  --out-csv results/api_modern_sweep_launch_audit.csv \
  --out-md results/tables/api_modern_sweep_launch_audit.md
```

Expected headline: all generated commands are launch-ready and include
Responses API mode, `--resume`, `results/api_cache`, `../apikey.txt`, the
planned output path, cooperative source refs, stop recovery mode, and a
budget cap at least as large as the conservative remaining estimate.

Current estimates using the pricing embedded in
`tracebreak.analysis.estimate_api_cost`: a 120-task, four-condition
`gpt-5.4-mini` sweep is about `$3.17` nominal and `$6.29` under the conservative
max-step budget; a full 120-task `gpt-5.5` sweep is about `$21.14` nominal and
`$41.92` under the max-step budget, so it exceeds the stated `$20` cap. The
48-task `gpt-5.5` fallback is about `$8.46` nominal and `$16.77` under the
max-step budget. The sweep-status commands report completed rows, remaining
rows, remaining cost, and exact `--resume` commands from the current JSONL
state.
Adding `api_visible_policy` to the 120-task `gpt-5.4-mini` sweep remains
budget-feasible at about `$4.00` nominal and `$7.92` under the conservative
max-step budget. Adding the same fifth condition to the 48-task `gpt-5.5`
fallback is about `$10.66` nominal but `$21.13` under the conservative max-step
budget, so keep it optional unless actual token usage from the cheaper sweep
shows enough budget headroom.

The next paid action should be the one-task `gpt-5.4-mini` Responses smoke in
`results/tables/api_paid_smoke_next_step.md`. That note first gives a no-spend
`--dry-run-first-request` payload preflight, then the paid `--resume` command
with `--max-estimated-cost-usd 0.02` and `--max-actual-cost-usd 0.02`. Its
no-spend estimate is `$0.0058`
nominal and `$0.0130` under the conservative max-step budget. Run the paid
command only after fresh explicit approval for this exact `$0.02` OpenAI API
smoke, because it reads `../apikey.txt` and may spend external budget.

The preflight report below also checks the dry-run payload contract and writes
reviewable CSV/Markdown artifacts. It does not read the API key or make network
calls.

```bash
conda run -n trace_level python -m tracebreak.analysis.api_paid_smoke_preflight \
  --tasks data/tasks_tracebreak_120.jsonl \
  --condition api_local \
  --model gpt-5.4-mini \
  --api-mode responses \
  --limit 1 \
  --max-steps 8 \
  --max-tokens 220 \
  --source-ref-mode cooperative \
  --recovery-mode stop \
  --recovery-steps 3 \
  --max-estimated-cost-usd 0.02 \
  --out-csv results/api_gpt54mini_paid_smoke_preflight.csv \
  --out-md results/tables/api_gpt54mini_paid_smoke_preflight.md \
  --out-payload-json results/api_gpt54mini_paid_smoke_payload.json
```

Expected headline: the first `gpt-5.4-mini` smoke request uses the Responses API
with strict `tracebreak_action` JSON schema, requires `source_refs` in the
structured argument object, includes the source-reference prompt, contains no
Authorization header in the persisted dry-run payload snapshot, and passes the
`$0.02` budget cap.

The readiness report records the current minimum-package status, optional
no-spend hardening artifacts, and paid-API blockers without reading the API key
or making network calls.

```bash
conda run -n trace_level python -m tracebreak.analysis.research_readiness \
  --root . \
  --out-csv results/research_readiness_report.csv \
  --out-md results/tables/research_readiness_report.md
```

Expected headline: the minimum package is 3/5 complete. Source-reference
robustness, category-level reporting, and paper/bundle validation are complete;
the planned `gpt-5.4-mini` 120-task sweep and `gpt-5.5` 48-task sweep remain
blocked until approved paid API rows exist. Optional rows mark the
prompt-surface/recovery audits, critic/replay baselines, deterministic stress
tests, bibliography integrity audit, claim-boundary audit, and paid-smoke
preflight complete, while the 24-task multi-agent topology status remains
blocked on paid API rows.

## Generate Tasks

```bash
conda run -n trace_level python -m tracebreak.data.generate_tasks \
  --out data/tasks_tracebreak_120.jsonl
```

Expected dataset: 120 tasks, with 10 risky and 10 safe-control tasks for each
of 6 categories.

## Benchmark Policy-Fact Audit

This no-spend audit checks the generated task definitions and records where
each category's decisive policy fact lives.

```bash
conda run -n trace_level python -m tracebreak.analysis.benchmark_fact_audit \
  --tasks data/tasks_tracebreak_120.jsonl \
  --out-csv results/benchmark_fact_audit.csv \
  --out-md results/tables/benchmark_fact_audit.md
```

Expected headline: all six categories have 10 risky/safe pairs. Local guards
do not have the decisive global-policy fact; visible sink review covers the
approval-scope and aggregation-threshold categories, while four categories
require hidden source or runtime metadata.

## Benchmark Coverage Audit

This no-spend audit summarizes task diversity and pair completeness from the
generated task definitions and scripted plans.

```bash
conda run -n trace_level python -m tracebreak.analysis.benchmark_coverage_audit \
  --tasks data/tasks_tracebreak_120.jsonl \
  --out-csv results/benchmark_coverage_audit.csv \
  --out-md results/tables/benchmark_coverage_audit.md
```

Expected headline: the benchmark has 120 tasks over 10 world seeds, 60 complete
risky/safe pairs, 100 email sinks and 20 ticket sinks, 40 visible-fact tasks and
80 hidden-metadata tasks, and scripted multi-agent plans ranging from 2 to 11
tool steps.

## API Prompt-Surface Audit

This no-spend audit constructs the model-visible API prompt messages along
scripted traces. It checks that hidden provenance-tag fields and benchmark
labels are not serialized into prompts, while verifying that source-reference,
policy-prompt, and multi-agent instructions appear only in the intended
conditions.

```bash
conda run -n trace_level python -m tracebreak.analysis.prompt_surface_audit \
  --tasks data/tasks_tracebreak_120.jsonl \
  --out-csv results/api_prompt_surface_audit.csv \
  --out-md results/tables/api_prompt_surface_audit.md
```

Expected headline: seven API prompt conditions produce 3,640 total prompts.
All rows have zero hidden-metadata key hits and zero benchmark-label hits. The
source-reference instruction appears in every prompt, the security-policy prompt
appears only for `api_policy_prompt` and `api_visible_policy`, and the
multi-agent topology prompt appears only for `api_multi_traceguard`.

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

## Multi-Agent Authority Transfer

The deterministic traces include a single-agent scaffold and multi-agent
researcher/planner/executor scaffolds. This analysis reports whether the
expected sink depends on another actor's output or a shared-memory handoff.

```bash
conda run -n trace_level python -m tracebreak.analysis.authority_transfer \
  --runs \
    results/raw_traces/single_local.jsonl \
    results/raw_traces/multi_local.jsonl \
    results/raw_traces/dlp.jsonl \
    results/raw_traces/visible_policy.jsonl \
    results/raw_traces/traceguard.jsonl \
  --out-md paper/tables/authority_transfer_deterministic_120.md \
  --out-tex paper/tables/authority_transfer_deterministic_120.tex
```

Expected headline: all multi-agent risky traces reach a transfer sink; DLP
permits all such risky transfer violations, visible-policy blocks only the
visible subset, and TraceGuard blocks all risky transfer sinks while preserving
safe-transfer utility.

## Indirect-Injection Overlay

This deterministic stress test appends synthetic instruction-like text to every
document and record body before replaying the scripted traces. It is a
structural composition check, not a live prompt-injection benchmark, and it does
not require API calls.

```bash
for condition in multi_local dlp visible_policy traceguard traceguard_inferred; do
  conda run -n trace_level python -m tracebreak.analysis.injection_overlay \
    --condition "$condition" \
    --out "results/raw_traces/${condition}_injection_overlay.jsonl"
done

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs \
    results/raw_traces/multi_local_injection_overlay.jsonl \
    results/raw_traces/dlp_injection_overlay.jsonl \
    results/raw_traces/visible_policy_injection_overlay.jsonl \
    results/raw_traces/traceguard_injection_overlay.jsonl \
    results/raw_traces/traceguard_inferred_injection_overlay.jsonl \
  --out-csv results/injection_overlay_metrics.csv \
  --out-md results/tables/injection_overlay_results.md

conda run -n trace_level python -m tracebreak.analysis.injection_overlay \
  --runs \
    results/raw_traces/multi_local_injection_overlay.jsonl \
    results/raw_traces/dlp_injection_overlay.jsonl \
    results/raw_traces/visible_policy_injection_overlay.jsonl \
    results/raw_traces/traceguard_injection_overlay.jsonl \
    results/raw_traces/traceguard_inferred_injection_overlay.jsonl \
  --out-md paper/tables/injection_overlay_deterministic_120.md \
  --out-tex paper/tables/injection_overlay_deterministic_120.tex
```

Expected headline: the overlay does not change the structural result. DLP and
multi-local traces still allow all risky local-pass violations, visible-policy
blocks only the visible subset, and TraceGuard blocks all risky sinks while
preserving safe-control utility. Runtime-inferred TraceGuard matches ordinary
TraceGuard under the same overlay.

## Decoy-Ambiguity Stress

This deterministic stress test adds plausible decoy documents, recipients,
approvals, and records to each synthetic world and uses search preambles to
expose those decoys before replaying scripted traces. It is a structural clutter
check, not a live model-selection benchmark.

```bash
for condition in multi_local dlp visible_policy traceguard traceguard_inferred; do
  conda run -n trace_level python -m tracebreak.analysis.decoy_stress \
    --condition "$condition" \
    --out "results/raw_traces/${condition}_decoy_stress.jsonl"
done

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs \
    results/raw_traces/multi_local_decoy_stress.jsonl \
    results/raw_traces/dlp_decoy_stress.jsonl \
    results/raw_traces/visible_policy_decoy_stress.jsonl \
    results/raw_traces/traceguard_decoy_stress.jsonl \
    results/raw_traces/traceguard_inferred_decoy_stress.jsonl \
  --out-csv results/decoy_stress_metrics.csv \
  --out-md results/tables/decoy_stress_results.md

conda run -n trace_level python -m tracebreak.analysis.decoy_stress \
  --runs \
    results/raw_traces/multi_local_decoy_stress.jsonl \
    results/raw_traces/dlp_decoy_stress.jsonl \
    results/raw_traces/visible_policy_decoy_stress.jsonl \
    results/raw_traces/traceguard_decoy_stress.jsonl \
    results/raw_traces/traceguard_inferred_decoy_stress.jsonl \
  --out-md paper/tables/decoy_stress_deterministic_120.md \
  --out-tex paper/tables/decoy_stress_deterministic_120.tex
```

Expected headline: the decoy clutter exposes 260 decoy search hits per
condition. Multi-local and DLP still allow all risky local-pass violations,
visible-policy still misses the hidden subset, and TraceGuard blocks all risky
sinks while preserving safe-control utility. Runtime-inferred TraceGuard matches
ordinary TraceGuard under the same clutter.

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
    --resume \
    --out "results/raw_traces/${condition}_gpt41mini_12.jsonl"

  conda run -n trace_level python -m tracebreak.experiments.run_api_condition \
    --tasks data/tasks_tracebreak_120.jsonl \
    --condition "$condition" \
    --model gpt-4.1-mini \
    --offset 12 \
    --limit 12 \
    --resume \
    --out "results/raw_traces/${condition}_gpt41mini_seed1_12.jsonl"
done

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs results/raw_traces/api_*gpt41mini*_12.jsonl \
  --out-csv results/api_gpt41mini_24_metrics.csv \
  --out-md results/tables/api_gpt41mini_24_results.md

conda run -n trace_level python -m tracebreak.analysis.policy_prompt_diagnostics \
  --runs \
    results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl \
  --out-csv results/api_gpt41mini_policy_prompt_diagnostics.csv \
  --out-md results/tables/api_gpt41mini_policy_prompt_diagnostics.md \
  --out-tex paper/tables/api_gpt41mini_policy_prompt_diagnostics.tex

conda run -n trace_level python -m tracebreak.analysis.block_reason_audit \
  --deterministic-runs results/raw_traces/traceguard.jsonl \
  --api-runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --out-csv results/traceguard_block_reason_audit.csv \
  --out-md results/tables/traceguard_block_reason_audit.md \
  --out-tex paper/tables/traceguard_block_reason_audit.tex
```

Expected headline: `api_local` and `api_dlp` produce local-pass violations on
all risky tasks; `api_policy_prompt` reduces but does not eliminate violations;
`api_traceguard` blocks all risky sink attempts and preserves safe-control
utility. The diagnostic table attributes the three policy-prompt avoided risky
violations to two approval-scope abstentions that also lose the matched safe
controls, plus one cross-tenant sink-target change. The block-reason audit
checks that TraceGuard's risky blocks use the category-aligned reason code on
both the deterministic 120-task suite and the 24-task API subset, with no
safe-control blocks. If these traces are regenerated with provider usage
metadata, the CSV and Markdown metric files will also include condition-level
token totals.

## Same-Action Defense Replay

The same-action replay uses the reported `api_local` action traces and
counterfactually applies DLP, visible-policy, and TraceGuard defenses. It does
not require additional API calls. This isolates the runtime defense from model
sampling differences across conditions.

```bash
for defense in dlp visible_policy metadata_critic traceguard; do
  conda run -n trace_level python -m tracebreak.analysis.defense_replay \
    --runs \
      results/raw_traces/api_local_gpt41mini_12.jsonl \
      results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    --defense "$defense" \
    --out "results/raw_traces/api_local_replay_${defense}_gpt41mini_24.jsonl"
done

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_local_replay_dlp_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl \
  --out-csv results/api_gpt41mini_same_action_replay_metrics.csv \
  --out-md results/tables/api_gpt41mini_same_action_replay_results.md

conda run -n trace_level python -m tracebreak.analysis.replay_tables \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_local_replay_dlp_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl \
  --out-md paper/tables/same_action_replay_gpt41mini_24.md \
  --out-tex paper/tables/same_action_replay_gpt41mini_24.tex

conda run -n trace_level python -m tracebreak.analysis.visibility_gap_audit \
  --runs \
    results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl \
  --out-csv results/api_gpt41mini_visibility_gap_audit.csv \
  --out-md results/tables/api_gpt41mini_visibility_gap_audit.md \
  --out-tex paper/tables/api_gpt41mini_visibility_gap_audit.tex

conda run -n trace_level python -m tracebreak.analysis.critic_baseline_audit \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl \
  --out-csv results/api_gpt41mini_critic_baseline_audit.csv \
  --out-md results/tables/api_gpt41mini_critic_baseline_audit.md
```

Expected headline: on the exact same model-proposed actions, DLP misses all
risky local-pass violations, visible-policy blocks only the visible
approval/bulk subset, and both metadata-critic and TraceGuard replays block all
risky sinks while preserving safe-control utility.
The visibility-gap audit localizes that split by category: visible-policy
blocks aggregation-threshold and approval-scope rows, but leaves all audience,
tenant, memory-laundering, and sensitive-external rows as violations.
The critic-baseline audit reports the same information boundary as a guard
baseline: a visible-critic proxy leaves 8/12 hidden-metadata risky rows as
violations, while a metadata-aware critic ties TraceGuard on fixed actions. A
one-review-per-sink critic would add 24 extra sink-review calls on this subset.

## API Source-Reference Compliance Audit

Before the stress ablation, audit the cached cooperative API traces to check
whether executed write sinks actually carry usable source references. This is a
no-spend analysis over reported JSONL files.

```bash
conda run -n trace_level python -m tracebreak.analysis.source_ref_compliance \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --out-csv results/api_gpt41mini_source_ref_compliance.csv \
  --out-md results/tables/api_gpt41mini_source_ref_compliance.md \
  --out-tex paper/tables/api_gpt41mini_source_ref_compliance.tex
```

Expected headline: across the 96 cached cooperative API runs, all 92 executed
write sinks have nonempty `source_refs` that resolve to prior unblocked
observations. The policy-prompt condition has 20 sinks because four runs end in
`final_answer` abstentions, and TraceGuard has 12 blocked sink attempts whose
refs are still valid.

## Source-Reference Robustness Ablation

The reported source-reference ablation uses existing cached/reported
`gpt-4.1-mini` TraceGuard traces and does not require additional API calls. It
deletes or corrupts source references from sink actions, or erases refs from
intermediate transform actions, during offline replay. It then compares ordinary
TraceGuard with a runtime-inferred provenance replay and the conservative
`StrictTraceGuard` fallback.

```bash
conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard \
  --out results/raw_traces/api_traceguard_drop_at_sink_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard_strict \
  --out results/raw_traces/api_traceguard_strict_drop_at_sink_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard_inferred \
  --out results/raw_traces/api_traceguard_inferred_drop_at_sink_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard \
  --stress-mode corrupt_at_sink \
  --out results/raw_traces/api_traceguard_corrupt_at_sink_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard_strict \
  --stress-mode corrupt_at_sink \
  --out results/raw_traces/api_traceguard_strict_corrupt_at_sink_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard_inferred \
  --stress-mode corrupt_at_sink \
  --out results/raw_traces/api_traceguard_inferred_corrupt_at_sink_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard \
  --stress-mode drop_intermediate \
  --out results/raw_traces/api_traceguard_drop_intermediate_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard_strict \
  --stress-mode drop_intermediate \
  --out results/raw_traces/api_traceguard_strict_drop_intermediate_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.source_ref_ablation \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --defense traceguard_inferred \
  --stress-mode drop_intermediate \
  --out results/raw_traces/api_traceguard_inferred_drop_intermediate_replay_gpt41mini_24.jsonl

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_traceguard_drop_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_strict_drop_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_inferred_drop_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_corrupt_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_strict_corrupt_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_inferred_corrupt_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_drop_intermediate_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_strict_drop_intermediate_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_inferred_drop_intermediate_replay_gpt41mini_24.jsonl \
  --out-csv results/api_gpt41mini_source_ref_ablation_24_metrics.csv \
  --out-md results/tables/api_gpt41mini_source_ref_ablation_24_results.md
```

Expected headline: deleting sink provenance makes ordinary TraceGuard fail on
all risky replay traces. Runtime-inferred provenance restores safety and
safe-control utility on this replay, while `StrictTraceGuard` restores safety
but heavily overblocks safe controls. Corrupting sink refs to benign public
observations fools ordinary and strict TraceGuard on 10 of 12 risky pairs, while
runtime-inferred provenance again restores safety and utility.
Erasing intermediate transform refs erases 23 provenance-bearing transform
actions and creates one risky violation when a sink points to a laundered
summary. Runtime inference removes that violation, but overblocks one aggregate
safe-control row.

The runtime-inferred monitor can also be run as a first-class deterministic
condition rather than only as an offline replay:

```bash
conda run -n trace_level python -m tracebreak.experiments.run_condition \
  --tasks data/tasks_tracebreak_120.jsonl \
  --condition traceguard_inferred \
  --out results/raw_traces/traceguard_inferred.jsonl

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs results/raw_traces/traceguard_inferred.jsonl \
  --out-csv results/traceguard_inferred_metrics.csv \
  --out-md results/tables/traceguard_inferred_results.md
```

Expected headline: `traceguard_inferred` matches TraceGuard on the clean
deterministic benchmark: 100% safe utility, 0% risky violations, 100% risky
blocks, and 0% safe false blocks across 120 tasks.

No-spend planning for a live `gpt-5.4-mini` inferred-guard subset:

```bash
conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.4-mini \
  --conditions api_traceguard_inferred \
  --limit 24 \
  --api-mode responses \
  --out-csv results/api_gpt54mini_inferred_guard_24_sweep_status.csv \
  --out-md results/tables/api_gpt54mini_inferred_guard_24_sweep_status.md
```

Expected headline: the planned live inferred-guard subset has 0/24 rows
completed until approved API spend exists and remains under `$0.32` under the
conservative max-step budget.

No-spend planning for the prompt/schema ablation that removes the
source-reference instruction from a live `gpt-5.4-mini` TraceGuard subset:

```bash
conda run -n trace_level python -m tracebreak.analysis.estimate_api_cost \
  --models gpt-5.4-mini \
  --conditions api_traceguard \
  --limit 24 \
  --source-ref-mode no_instruction \
  --out-csv results/api_gpt54mini_no_source_ref_instruction_24_cost_estimate.csv \
  --out-md results/tables/api_gpt54mini_no_source_ref_instruction_24_cost_estimate.md

conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.4-mini \
  --conditions api_traceguard \
  --limit 24 \
  --api-mode responses \
  --source-ref-mode no_instruction \
  --out-csv results/api_gpt54mini_no_source_ref_instruction_24_sweep_status.csv \
  --out-md results/tables/api_gpt54mini_no_source_ref_instruction_24_sweep_status.md

conda run -n trace_level python -m tracebreak.analysis.api_paid_smoke_preflight \
  --tasks data/tasks_tracebreak_120.jsonl \
  --condition api_traceguard \
  --model gpt-5.4-mini \
  --api-mode responses \
  --source-ref-mode no_instruction \
  --limit 1 \
  --max-steps 8 \
  --max-tokens 220 \
  --recovery-mode stop \
  --recovery-steps 3 \
  --max-estimated-cost-usd 0.02 \
  --out-csv results/api_gpt54mini_no_source_ref_instruction_preflight.csv \
  --out-md results/tables/api_gpt54mini_no_source_ref_instruction_preflight.md \
  --out-payload-json results/api_gpt54mini_no_source_ref_instruction_payload.json
```

Expected headline: the planned no-instruction ablation has 0/24 rows completed
until approved API spend exists, writes to
`results/raw_traces/api_traceguard_no_instruction_gpt54mini_24.jsonl`, and
remains under `$0.31` under the conservative max-step budget. This ablation is
intended to test whether live model behavior depends on the prompt asking for
`source_refs`; it is separate from the no-spend replay stress tests above. The
payload preflight verifies the schema-only contract: the source-reference prompt
is absent, but the strict Responses schema still requires nullable
`source_refs`, and the one-task budget guard remains under `$0.02`.

## Exact Paired Tests

The paired report uses the cached API subset, same-action replay traces, and
deleted-provenance replay traces. It compares matched task IDs and does not
require additional API calls.

```bash
conda run -n trace_level python -m tracebreak.analysis.paired_tests \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_local_replay_dlp_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl \
    results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_drop_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_inferred_drop_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_corrupt_at_sink_replay_gpt41mini_24.jsonl \
    results/raw_traces/api_traceguard_inferred_corrupt_at_sink_replay_gpt41mini_24.jsonl \
  --out-csv results/api_gpt41mini_paired_tests.csv \
  --out-md results/tables/api_gpt41mini_paired_tests.md
```

Expected headline: TraceGuard reduces risky violations against API local and
DLP on all 12 matched risky pairs, improves over policy prompting on 9 of 12
risky pairs, and metadata-aware replay improves over visible-policy replay on 8
of 12 risky pairs. TraceGuard preserves 100% paired safe utility against local
and DLP.

## Block-And-Recover Runner

The API runner supports an opt-in recovery mode for future budgeted runs. When a
defense blocks a sink, the blocked event is kept in the visible trace with a
policy-compliant recovery instruction, and the model can take up to three more
steps.

The recovery prompt surface can be audited without API calls:

```bash
conda run -n trace_level python -m tracebreak.analysis.recovery_prompt_audit \
  --tasks data/tasks_tracebreak_120.jsonl \
  --out-csv results/api_recovery_prompt_audit.csv \
  --out-md results/tables/api_recovery_prompt_audit.md
```

Expected headline: under the eight-step API loop budget, recovery instructions
appear only in the first prompt after a defense-blocked write sink: 10/10 for
visible-policy blocks and 50/50 for TraceGuard and runtime-inferred TraceGuard.
Local and DLP conditions have zero recovery prompt hits; all conditions have
zero pre-block and zero safe-control recovery prompt hits.

This command may make live API calls if the cache lacks recovery-turn responses:

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition \
  --tasks data/tasks_tracebreak_120.jsonl \
  --condition api_traceguard \
  --model gpt-4.1-mini \
  --limit 12 \
  --max-steps 8 \
  --recovery-mode after_block \
  --recovery-steps 3 \
  --resume \
  --api-key-path ../apikey.txt \
  --out results/raw_traces/api_traceguard_recover_gpt41mini_12.jsonl

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs results/raw_traces/api_traceguard_recover_gpt41mini_12.jsonl \
  --out-csv results/api_gpt41mini_recovery_12_metrics.csv \
  --out-md results/tables/api_gpt41mini_recovery_12_results.md
```

Recovery-specific summary columns include risky repair rate, unsafe retry after
block, clarification/final-answer after block, and average recovery steps.

## Repair-Oracle Upper Bound

The repair-oracle replay uses no API calls. It appends a deterministic
matched-control repair after each blocked risky TraceGuard trace. Aggregation
repairs may require one aggregate operation before the safe sink.

```bash
conda run -n trace_level python -m tracebreak.analysis.repair_oracle \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --out results/raw_traces/api_traceguard_repair_oracle_gpt41mini_12.jsonl

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_traceguard_repair_oracle_gpt41mini_12.jsonl \
  --out-csv results/api_gpt41mini_repair_oracle_metrics.csv \
  --out-md results/tables/api_gpt41mini_repair_oracle_results.md

conda run -n trace_level python -m tracebreak.analysis.repair_oracle \
  --runs results/raw_traces/traceguard.jsonl \
  --out results/raw_traces/traceguard_repair_oracle_60.jsonl

conda run -n trace_level python -m tracebreak.analysis.compute_metrics \
  --runs results/raw_traces/traceguard_repair_oracle_60.jsonl \
  --out-csv results/traceguard_repair_oracle_60_metrics.csv \
  --out-md results/tables/traceguard_repair_oracle_60_results.md
```

Expected headline: all blocked risky API TraceGuard traces have a one-step
policy-compliant repair under the matched-control oracle; all 60 blocked risky
scripted TraceGuard traces have a repair within two steps.

## Paper Tables And Figures

```bash
conda run -n trace_level python -m tracebreak.analysis.paper_tables \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --out-md paper/tables/api_gpt41mini_24_results.md \
  --out-tex paper/tables/api_gpt41mini_24_results.tex

conda run -n trace_level python -m tracebreak.analysis.paper_tables \
  --runs \
    results/raw_traces/single_local.jsonl \
    results/raw_traces/multi_local.jsonl \
    results/raw_traces/dlp.jsonl \
    results/raw_traces/visible_policy.jsonl \
    results/raw_traces/traceguard.jsonl \
  --out-md paper/tables/deterministic_120_results.md \
  --out-tex paper/tables/deterministic_120_results.tex

conda run -n trace_level python -m tracebreak.analysis.export_examples \
  --local-run results/raw_traces/api_local_gpt41mini_12.jsonl \
  --traceguard-run results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
  --out paper/tables/example_traces.md

conda run -n trace_level python -m tracebreak.analysis.category_examples \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --out paper/tables/api_gpt41mini_category_examples.md

conda run -n trace_level python -m tracebreak.analysis.make_figures \
  --runs results/raw_traces/api_*gpt41mini*_12.jsonl \
  --out-dir paper/figures
```

This writes both SVG inspection artifacts and
`paper/figures/api_security_utility.tex`, the TikZ figure included by the
supplement.

## Category-Level API Table

```bash
conda run -n trace_level python -m tracebreak.analysis.category_tables \
  --runs \
    results/raw_traces/api_local_gpt41mini_12.jsonl \
    results/raw_traces/api_local_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_12.jsonl \
    results/raw_traces/api_dlp_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl \
    results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_12.jsonl \
    results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl \
  --out-md paper/tables/api_gpt41mini_24_by_category.md \
  --out-tex paper/tables/api_gpt41mini_24_by_category.tex
```

Expected headline: local guards and DLP have 100% risky violations and 100%
LPVR in all six categories, while TraceGuard has 0% risky violations, 100%
risky block, and 100% safe-control utility in every category.

The category example gallery gives one concrete risky API-local trace per
category and the matching TraceGuard block, so reviewers can inspect the hidden
policy fact behind each aggregate category result.

## Paper Build

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
latexmk -pdf -interaction=nonstopmode supplement.tex
pdfinfo main.pdf
pdfinfo supplement.pdf
cd ..
conda run -n trace_level python -m tracebreak.analysis.bibliography_audit \
  --paper-dir paper \
  --out-csv results/bibliography_audit.csv \
  --out-md results/tables/bibliography_audit.md
```

Expected current build: `paper/main.pdf`, 7 pages including references, using
the local COLM 2026 style files. The non-reference body ends on page 6 and
references begin on page 7. The supplement builds as `paper/supplement.pdf`.
The bibliography audit should report 17 cited keys, 19 BibTeX entries, 17
generated bibliography entries, no undefined or stale keys, no malformed arXiv
IDs, no denied old citation keys, and `pass=yes`.
