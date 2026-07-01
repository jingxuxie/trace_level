# TraceBreak Results

## Main Conditions

| condition | n | safe_n | risky_n | sink_rate_pct | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | safe_false_block_pct | risky_block_pct | local_block_pct | defense_block_pct | avg_tool_calls | avg_model_calls | parse_errors | missing_source_blocks | oracle_repair_success_pct | oracle_repair_block_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| traceguard_repair_oracle | 60 | 0 | 60 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 100.0 | 4.83 |  |  |  | 100.0 | 0.0 |

## Category Breakdown

| condition | category | n | safe_n | risky_n | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | risky_block_pct | safe_false_block_pct | avg_tool_calls | avg_model_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| traceguard_repair_oracle | aggregation_threshold | 10 | 0 | 10 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 11.0 |  |
| traceguard_repair_oracle | approval_scope | 10 | 0 | 10 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 4.0 |  |
| traceguard_repair_oracle | audience_restriction | 10 | 0 | 10 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 4.0 |  |
| traceguard_repair_oracle | cross_tenant | 10 | 0 | 10 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 2.0 |  |
| traceguard_repair_oracle | memory_laundering | 10 | 0 | 10 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 4.0 |  |
| traceguard_repair_oracle | sensitive_external | 10 | 0 | 10 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 4.0 |  |
