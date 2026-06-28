# TraceBreak Results

## Main Conditions

| condition | n | safe_n | risky_n | sink_rate_pct | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | safe_false_block_pct | risky_block_pct | local_block_pct | defense_block_pct | avg_tool_calls | avg_model_calls | parse_errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dlp | 120 | 60 | 60 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.75 |  |  |
| multi_local | 120 | 60 | 60 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.75 |  |  |
| single_local | 120 | 60 | 60 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.75 |  |  |
| traceguard | 120 | 60 | 60 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 50.0 | 4.25 |  |  |
| visible_policy | 120 | 60 | 60 | 83.33333333333333 | 100.0 | 66.66666666666667 | 66.66666666666667 | 0.0 | 33.333333333333336 | 0.0 | 16.666666666666668 | 4.58 |  |  |

## Risky Category Breakdown

| condition | category | risky_n | global_violation_pct | block_pct |
| --- | --- | --- | --- | --- |
| dlp | aggregation_threshold | 10 | 100.0 | 0.0 |
| dlp | approval_scope | 10 | 100.0 | 0.0 |
| dlp | audience_restriction | 10 | 100.0 | 0.0 |
| dlp | cross_tenant | 10 | 100.0 | 0.0 |
| dlp | memory_laundering | 10 | 100.0 | 0.0 |
| dlp | sensitive_external | 10 | 100.0 | 0.0 |
| multi_local | aggregation_threshold | 10 | 100.0 | 0.0 |
| multi_local | approval_scope | 10 | 100.0 | 0.0 |
| multi_local | audience_restriction | 10 | 100.0 | 0.0 |
| multi_local | cross_tenant | 10 | 100.0 | 0.0 |
| multi_local | memory_laundering | 10 | 100.0 | 0.0 |
| multi_local | sensitive_external | 10 | 100.0 | 0.0 |
| single_local | aggregation_threshold | 10 | 100.0 | 0.0 |
| single_local | approval_scope | 10 | 100.0 | 0.0 |
| single_local | audience_restriction | 10 | 100.0 | 0.0 |
| single_local | cross_tenant | 10 | 100.0 | 0.0 |
| single_local | memory_laundering | 10 | 100.0 | 0.0 |
| single_local | sensitive_external | 10 | 100.0 | 0.0 |
| traceguard | aggregation_threshold | 10 | 0.0 | 100.0 |
| traceguard | approval_scope | 10 | 0.0 | 100.0 |
| traceguard | audience_restriction | 10 | 0.0 | 100.0 |
| traceguard | cross_tenant | 10 | 0.0 | 100.0 |
| traceguard | memory_laundering | 10 | 0.0 | 100.0 |
| traceguard | sensitive_external | 10 | 0.0 | 100.0 |
| visible_policy | aggregation_threshold | 10 | 0.0 | 100.0 |
| visible_policy | approval_scope | 10 | 0.0 | 100.0 |
| visible_policy | audience_restriction | 10 | 100.0 | 0.0 |
| visible_policy | cross_tenant | 10 | 100.0 | 0.0 |
| visible_policy | memory_laundering | 10 | 100.0 | 0.0 |
| visible_policy | sensitive_external | 10 | 100.0 | 0.0 |
