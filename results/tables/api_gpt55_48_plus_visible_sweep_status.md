# API Sweep Status

| expected | completed | missing | actual cost | remaining nominal | remaining budget |
|---:|---:|---:|---:|---:|---:|
| 240 | 0 | 240 | $0.0000 | $10.6584 | $21.1267 |

| model | condition | API | expected | completed | missing | parse errors | actual cost | remaining nominal | remaining budget | out path |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.5 | api_local | responses | 48 | 0 | 48 | 0 | $0.0000 | $2.0841 | $4.1385 | `results/raw_traces/api_local_gpt55_48.jsonl` |
| gpt-5.5 | api_dlp | responses | 48 | 0 | 48 | 0 | $0.0000 | $2.0841 | $4.1385 | `results/raw_traces/api_dlp_gpt55_48.jsonl` |
| gpt-5.5 | api_policy_prompt | responses | 48 | 0 | 48 | 0 | $0.0000 | $2.2030 | $4.3580 | `results/raw_traces/api_policy_prompt_gpt55_48.jsonl` |
| gpt-5.5 | api_traceguard | responses | 48 | 0 | 48 | 0 | $0.0000 | $2.0841 | $4.1348 | `results/raw_traces/api_traceguard_gpt55_48.jsonl` |
| gpt-5.5 | api_visible_policy | responses | 48 | 0 | 48 | 0 | $0.0000 | $2.2030 | $4.3569 | `results/raw_traces/api_visible_policy_gpt55_48.jsonl` |

## Resume Commands

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_local --model gpt-5.5 --api-mode responses --offset 0 --limit 48 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_local_gpt55_48.jsonl --max-estimated-cost-usd 4.138501
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_dlp --model gpt-5.5 --api-mode responses --offset 0 --limit 48 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_dlp_gpt55_48.jsonl --max-estimated-cost-usd 4.138501
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_policy_prompt --model gpt-5.5 --api-mode responses --offset 0 --limit 48 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_policy_prompt_gpt55_48.jsonl --max-estimated-cost-usd 4.358001
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_traceguard --model gpt-5.5 --api-mode responses --offset 0 --limit 48 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_traceguard_gpt55_48.jsonl --max-estimated-cost-usd 4.134801
```

```bash
conda run -n trace_level python -m tracebreak.experiments.run_api_condition --tasks data/tasks_tracebreak_120.jsonl --condition api_visible_policy --model gpt-5.5 --api-mode responses --offset 0 --limit 48 --max-steps 8 --source-ref-mode cooperative --recovery-mode stop --recovery-steps 3 --api-key-path ../apikey.txt --cache-dir results/api_cache --resume --out results/raw_traces/api_visible_policy_gpt55_48.jsonl --max-estimated-cost-usd 4.356921
```
