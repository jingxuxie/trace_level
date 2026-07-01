# TraceBreak Results

## Main Conditions

| condition | n | safe_n | risky_n | sink_rate_pct | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | safe_false_block_pct | risky_block_pct | local_block_pct | defense_block_pct | avg_tool_calls | avg_model_calls | parse_errors | missing_source_blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| traceguard_inferred | 120 | 60 | 60 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 50.0 | 4.25 |  |  |  |

## Category Breakdown

| condition | category | n | safe_n | risky_n | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | risky_block_pct | safe_false_block_pct | avg_tool_calls | avg_model_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| traceguard_inferred | aggregation_threshold | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 10.0 |  |
| traceguard_inferred | approval_scope | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| traceguard_inferred | audience_restriction | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| traceguard_inferred | cross_tenant | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 1.5 |  |
| traceguard_inferred | memory_laundering | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| traceguard_inferred | sensitive_external | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
