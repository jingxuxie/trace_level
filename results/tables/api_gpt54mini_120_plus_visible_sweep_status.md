# API Sweep Status

| expected | completed | missing | actual cost | remaining nominal | remaining budget |
|---:|---:|---:|---:|---:|---:|
| 600 | 0 | 600 | $0.0000 | $3.9969 | $7.9225 |

| model | condition | API | expected | completed | missing | parse errors | actual cost | remaining nominal | remaining budget | out path |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.4-mini | api_local | responses | 120 | 0 | 120 | 0 | $0.0000 | $0.7815 | $1.5519 | `results/raw_traces/api_local_gpt54mini_120.jsonl` |
| gpt-5.4-mini | api_dlp | responses | 120 | 0 | 120 | 0 | $0.0000 | $0.7815 | $1.5519 | `results/raw_traces/api_dlp_gpt54mini_120.jsonl` |
| gpt-5.4-mini | api_policy_prompt | responses | 120 | 0 | 120 | 0 | $0.0000 | $0.8261 | $1.6342 | `results/raw_traces/api_policy_prompt_gpt54mini_120.jsonl` |
| gpt-5.4-mini | api_traceguard | responses | 120 | 0 | 120 | 0 | $0.0000 | $0.7815 | $1.5506 | `results/raw_traces/api_traceguard_gpt54mini_120.jsonl` |
| gpt-5.4-mini | api_visible_policy | responses | 120 | 0 | 120 | 0 | $0.0000 | $0.8261 | $1.6338 | `results/raw_traces/api_visible_policy_gpt54mini_120.jsonl` |

## Resume Commands

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_local --model gpt-5.4-mini --api-mode responses --offset 0 --limit 120 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_local_gpt54mini_120.jsonl --max-estimated-cost-usd 1.551938
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_dlp --model gpt-5.4-mini --api-mode responses --offset 0 --limit 120 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_dlp_gpt54mini_120.jsonl --max-estimated-cost-usd 1.551938
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_policy_prompt --model gpt-5.4-mini --api-mode responses --offset 0 --limit 120 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_policy_prompt_gpt54mini_120.jsonl --max-estimated-cost-usd 1.634251
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_traceguard --model gpt-5.4-mini --api-mode responses --offset 0 --limit 120 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_traceguard_gpt54mini_120.jsonl --max-estimated-cost-usd 1.550551
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_visible_policy --model gpt-5.4-mini --api-mode responses --offset 0 --limit 120 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_visible_policy_gpt54mini_120.jsonl --max-estimated-cost-usd 1.633846
```
