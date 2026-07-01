# TraceBreak Results

## Main Conditions

| condition | n | safe_n | risky_n | sink_rate_pct | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | safe_false_block_pct | risky_block_pct | local_block_pct | defense_block_pct | avg_tool_calls | avg_model_calls | parse_errors | missing_source_blocks | oracle_repair_success_pct | oracle_repair_block_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| api_traceguard | 24 | 12 | 12 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 50.0 | 4.62 | 5.12 | 0 |  |  |  |
| api_traceguard_repair_oracle | 12 | 0 | 12 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 100.0 | 5.5 | 5.5 | 0 |  | 100.0 | 0.0 |

## Category Breakdown

| condition | category | n | safe_n | risky_n | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | risky_block_pct | safe_false_block_pct | avg_tool_calls | avg_model_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| api_traceguard | aggregation_threshold | 4 | 2 | 2 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 5.0 | 5.5 |
| api_traceguard | approval_scope | 4 | 2 | 2 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 5.0 | 5.5 |
| api_traceguard | audience_restriction | 4 | 2 | 2 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 4.5 | 5.0 |
| api_traceguard | cross_tenant | 4 | 2 | 2 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.25 | 3.75 |
| api_traceguard | memory_laundering | 4 | 2 | 2 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 5.5 | 6.0 |
| api_traceguard | sensitive_external | 4 | 2 | 2 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 4.5 | 5.0 |
| api_traceguard_repair_oracle | aggregation_threshold | 2 | 0 | 2 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 7.0 | 7.0 |
| api_traceguard_repair_oracle | approval_scope | 2 | 0 | 2 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 6.0 | 6.0 |
| api_traceguard_repair_oracle | audience_restriction | 2 | 0 | 2 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 5.0 | 5.0 |
| api_traceguard_repair_oracle | cross_tenant | 2 | 0 | 2 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 4.0 | 4.0 |
| api_traceguard_repair_oracle | memory_laundering | 2 | 0 | 2 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 6.0 | 6.0 |
| api_traceguard_repair_oracle | sensitive_external | 2 | 0 | 2 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 5.0 | 5.0 |
