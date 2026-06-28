# TraceBreak Results

## Main Conditions

| condition | n | safe_n | risky_n | sink_rate_pct | safe_utility_pct | risky_global_violation_pct | risky_lpvr_pct | safe_false_block_pct | risky_block_pct | local_block_pct | defense_block_pct | avg_tool_calls | avg_model_calls | parse_errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| api_dlp | 24 | 12 | 12 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5.12 | 5.12 | 0 |
| api_local | 24 | 12 | 12 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5.12 | 5.12 | 0 |
| api_policy_prompt | 24 | 12 | 12 | 79.16666666666667 | 83.33333333333333 | 75.0 | 75.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.58 | 4.58 | 0 |
| api_traceguard | 24 | 12 | 12 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 50.0 | 4.62 | 5.12 | 0 |

## Risky Category Breakdown

| condition | category | risky_n | global_violation_pct | block_pct |
| --- | --- | --- | --- | --- |
| api_dlp | aggregation_threshold | 2 | 100.0 | 0.0 |
| api_dlp | approval_scope | 2 | 100.0 | 0.0 |
| api_dlp | audience_restriction | 2 | 100.0 | 0.0 |
| api_dlp | cross_tenant | 2 | 100.0 | 0.0 |
| api_dlp | memory_laundering | 2 | 100.0 | 0.0 |
| api_dlp | sensitive_external | 2 | 100.0 | 0.0 |
| api_local | aggregation_threshold | 2 | 100.0 | 0.0 |
| api_local | approval_scope | 2 | 100.0 | 0.0 |
| api_local | audience_restriction | 2 | 100.0 | 0.0 |
| api_local | cross_tenant | 2 | 100.0 | 0.0 |
| api_local | memory_laundering | 2 | 100.0 | 0.0 |
| api_local | sensitive_external | 2 | 100.0 | 0.0 |
| api_policy_prompt | aggregation_threshold | 2 | 100.0 | 0.0 |
| api_policy_prompt | approval_scope | 2 | 0.0 | 0.0 |
| api_policy_prompt | audience_restriction | 2 | 100.0 | 0.0 |
| api_policy_prompt | cross_tenant | 2 | 50.0 | 0.0 |
| api_policy_prompt | memory_laundering | 2 | 100.0 | 0.0 |
| api_policy_prompt | sensitive_external | 2 | 100.0 | 0.0 |
| api_traceguard | aggregation_threshold | 2 | 0.0 | 100.0 |
| api_traceguard | approval_scope | 2 | 0.0 | 100.0 |
| api_traceguard | audience_restriction | 2 | 0.0 | 100.0 |
| api_traceguard | cross_tenant | 2 | 0.0 | 100.0 |
| api_traceguard | memory_laundering | 2 | 0.0 | 100.0 |
| api_traceguard | sensitive_external | 2 | 0.0 | 100.0 |
