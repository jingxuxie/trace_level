# API Sweep Status

| expected | completed | missing | actual cost | remaining nominal | remaining budget |
|---:|---:|---:|---:|---:|---:|
| 96 | 0 | 96 | $0.0000 | $0.6557 | $1.2975 |

| model | condition | API | expected | completed | missing | parse errors | actual cost | remaining nominal | remaining budget | out path |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.4-mini | api_single_local | responses | 24 | 0 | 24 | 0 | $0.0000 | $0.1563 | $0.3104 | `results/raw_traces/api_single_local_gpt54mini_24.jsonl` |
| gpt-5.4-mini | api_multi_local | responses | 24 | 0 | 24 | 0 | $0.0000 | $0.1635 | $0.3236 | `results/raw_traces/api_multi_local_gpt54mini_24.jsonl` |
| gpt-5.4-mini | api_multi_policy_prompt | responses | 24 | 0 | 24 | 0 | $0.0000 | $0.1724 | $0.3401 | `results/raw_traces/api_multi_policy_prompt_gpt54mini_24.jsonl` |
| gpt-5.4-mini | api_multi_traceguard | responses | 24 | 0 | 24 | 0 | $0.0000 | $0.1635 | $0.3234 | `results/raw_traces/api_multi_traceguard_gpt54mini_24.jsonl` |

## Resume Commands

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_single_local --model gpt-5.4-mini --api-mode responses --offset 0 --limit 24 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_single_local_gpt54mini_24.jsonl --max-estimated-cost-usd 0.310388
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_multi_local --model gpt-5.4-mini --api-mode responses --offset 0 --limit 24 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_multi_local_gpt54mini_24.jsonl --max-estimated-cost-usd 0.323636
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_multi_policy_prompt --model gpt-5.4-mini --api-mode responses --offset 0 --limit 24 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_multi_policy_prompt_gpt54mini_24.jsonl --max-estimated-cost-usd 0.340099
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_multi_traceguard --model gpt-5.4-mini --api-mode responses --offset 0 --limit 24 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_multi_traceguard_gpt54mini_24.jsonl --max-estimated-cost-usd 0.323359
```
