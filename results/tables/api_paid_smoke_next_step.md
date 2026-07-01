# Paid API Smoke Next Step

No API calls are required to read or regenerate this note. The next paid action
should be a one-task `gpt-5.4-mini` smoke using the Responses API mode, written
into the planned full-sweep output path so it becomes resumable work rather
than a throwaway run.
The Responses client requests strict structured JSON schema output with
top-level `action` and `arguments` fields, matching the parser used by the
cached API subset.

No-spend payload preflight:

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition \
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
  --out results/raw_traces/api_local_gpt54mini_120.jsonl \
  --dry-run-first-request
```

Persisted preflight artifacts:
`results/api_gpt54mini_paid_smoke_preflight.csv` and
`results/tables/api_gpt54mini_paid_smoke_preflight.md`, plus the redacted
payload snapshot `results/api_gpt54mini_paid_smoke_payload.json`. They check
that the dry-run payload uses strict `tracebreak_action` JSON schema, requires
`source_refs`, includes the source-reference prompt, contains no Authorization
header, and passes the `$0.02` budget guard.

Estimated cost from `tracebreak.analysis.estimate_api_cost` for
`gpt-5.4-mini`, `api_local`, `limit=1`:

| model | condition | tasks | nominal calls | nominal cost | budget calls | budget cost |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.4-mini | api_local | 1 | 4 | $0.0058 | 8 | $0.0130 |

Run only after fresh explicit approval for this exact `$0.02` OpenAI API smoke,
because the paid command reads `../apikey.txt` and may spend external budget.
The paid command includes a `$0.02` conservative estimate guard, so it fails
before reading the API key if the estimated remaining run would exceed that cap.
It also includes a `$0.02` actual-cost guard, so after each newly generated row
the runner uses provider-reported token usage to stop before launching more
tasks once the cap is reached:

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition \
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
  --api-key-path ../apikey.txt \
  --cache-dir results/api_cache \
  --resume \
  --max-estimated-cost-usd 0.02 \
  --max-actual-cost-usd 0.02 \
  --out results/raw_traces/api_local_gpt54mini_120.jsonl
```

After the smoke succeeds, regenerate the no-spend status report:

```bash
conda run -n trace_level python -m tracebreak.analysis.api_sweep_status \
  --models gpt-5.4-mini \
  --conditions api_local api_dlp api_policy_prompt api_traceguard \
  --limit 120 \
  --api-mode responses \
  --out-csv results/api_gpt54mini_120_sweep_status.csv \
  --out-md results/tables/api_gpt54mini_120_sweep_status.md
```
