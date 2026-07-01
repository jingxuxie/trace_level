# API Sweep Status

| expected | completed | missing | actual cost | remaining nominal | remaining budget |
|---:|---:|---:|---:|---:|---:|
| 24 | 0 | 24 | $0.0000 | $0.1563 | $0.3101 |

| model | condition | API | expected | completed | missing | parse errors | actual cost | remaining nominal | remaining budget | out path |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.4-mini | api_traceguard_inferred | responses | 24 | 0 | 24 | 0 | $0.0000 | $0.1563 | $0.3101 | `results/raw_traces/api_traceguard_inferred_gpt54mini_24.jsonl` |

## Resume Commands

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_traceguard_inferred --model gpt-5.4-mini --api-mode responses --offset 0 --limit 24 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_traceguard_inferred_gpt54mini_24.jsonl --max-estimated-cost-usd 0.310111
```
