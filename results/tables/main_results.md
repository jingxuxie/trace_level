# TraceBreak Results

## Main Conditions

| condition | n | safe_n | risky_n | sink_rate_pct | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | safe_false_block_pct | risky_block_pct | local_block_pct | defense_block_pct | avg_tool_calls | avg_model_calls | parse_errors | missing_source_blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dlp | 120 | 60 | 60 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.75 |  |  |  |
| multi_local | 120 | 60 | 60 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.75 |  |  |  |
| single_local | 120 | 60 | 60 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.75 |  |  |  |
| traceguard | 120 | 60 | 60 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 50.0 | 4.25 |  |  |  |
| visible_policy | 120 | 60 | 60 | 83.33333333333333 | 100.0 | 66.66666666666667 | 66.66666666666667 | 0.0 | 33.333333333333336 | 0.0 | 16.666666666666668 | 4.58 |  |  |  |

## Category Breakdown

| condition | category | n | safe_n | risky_n | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | risky_block_pct | safe_false_block_pct | avg_tool_calls | avg_model_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dlp | aggregation_threshold | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 10.5 |  |
| dlp | approval_scope | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| dlp | audience_restriction | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| dlp | cross_tenant | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 2.0 |  |
| dlp | memory_laundering | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| dlp | sensitive_external | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| multi_local | aggregation_threshold | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 10.5 |  |
| multi_local | approval_scope | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| multi_local | audience_restriction | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| multi_local | cross_tenant | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 2.0 |  |
| multi_local | memory_laundering | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| multi_local | sensitive_external | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| single_local | aggregation_threshold | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 10.5 |  |
| single_local | approval_scope | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| single_local | audience_restriction | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| single_local | cross_tenant | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 2.0 |  |
| single_local | memory_laundering | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| single_local | sensitive_external | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| traceguard | aggregation_threshold | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 10.0 |  |
| traceguard | approval_scope | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| traceguard | audience_restriction | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| traceguard | cross_tenant | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 1.5 |  |
| traceguard | memory_laundering | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| traceguard | sensitive_external | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| visible_policy | aggregation_threshold | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 10.0 |  |
| visible_policy | approval_scope | 20 | 10 | 10 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 3.5 |  |
| visible_policy | audience_restriction | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| visible_policy | cross_tenant | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 2.0 |  |
| visible_policy | memory_laundering | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
| visible_policy | sensitive_external | 20 | 10 | 10 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 4.0 |  |
