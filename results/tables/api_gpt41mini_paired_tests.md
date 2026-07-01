Exact paired binomial sign tests over matched task IDs. Positive delta means the comparator is better under the metric polarity.

| comparison | baseline | comparator | split | metric | n_matched | baseline_rate_pct | comparator_rate_pct | better_delta_pp | improvements | regressions | ties | exact_p_two_sided | exact_p_improvement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API local vs TraceGuard | api_local | api_traceguard | risky | Risky violation | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| API local vs TraceGuard | api_local | api_traceguard | risky | LPVR | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| API local vs TraceGuard | api_local | api_traceguard | risky | Risky block | 12 | 0.0 | 100.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| API local vs TraceGuard | api_local | api_traceguard | safe | Safe utility | 12 | 100.0 | 100.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| API local vs TraceGuard | api_local | api_traceguard | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| API DLP vs TraceGuard | api_dlp | api_traceguard | risky | Risky violation | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| API DLP vs TraceGuard | api_dlp | api_traceguard | risky | LPVR | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| API DLP vs TraceGuard | api_dlp | api_traceguard | risky | Risky block | 12 | 0.0 | 100.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| API DLP vs TraceGuard | api_dlp | api_traceguard | safe | Safe utility | 12 | 100.0 | 100.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| API DLP vs TraceGuard | api_dlp | api_traceguard | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| API prompt vs TraceGuard | api_policy_prompt | api_traceguard | risky | Risky violation | 12 | 75.0 | 0.0 | 75.0 | 9 | 0 | 3 | 0.0039 | 0.002 |
| API prompt vs TraceGuard | api_policy_prompt | api_traceguard | risky | LPVR | 12 | 75.0 | 0.0 | 75.0 | 9 | 0 | 3 | 0.0039 | 0.002 |
| API prompt vs TraceGuard | api_policy_prompt | api_traceguard | risky | Risky block | 12 | 0.0 | 100.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| API prompt vs TraceGuard | api_policy_prompt | api_traceguard | safe | Safe utility | 12 | 83.333 | 100.0 | 16.667 | 2 | 0 | 10 | 0.5 | 0.25 |
| API prompt vs TraceGuard | api_policy_prompt | api_traceguard | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action DLP vs TraceGuard | api_local_replay_dlp | api_local_replay_traceguard | risky | Risky violation | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| same-action DLP vs TraceGuard | api_local_replay_dlp | api_local_replay_traceguard | risky | LPVR | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| same-action DLP vs TraceGuard | api_local_replay_dlp | api_local_replay_traceguard | risky | Risky block | 12 | 0.0 | 100.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| same-action DLP vs TraceGuard | api_local_replay_dlp | api_local_replay_traceguard | safe | Safe utility | 12 | 100.0 | 100.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action DLP vs TraceGuard | api_local_replay_dlp | api_local_replay_traceguard | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action visible policy vs TraceGuard | api_local_replay_visible_policy | api_local_replay_traceguard | risky | Risky violation | 12 | 66.667 | 0.0 | 66.667 | 8 | 0 | 4 | 0.0078 | 0.0039 |
| same-action visible policy vs TraceGuard | api_local_replay_visible_policy | api_local_replay_traceguard | risky | LPVR | 12 | 66.667 | 0.0 | 66.667 | 8 | 0 | 4 | 0.0078 | 0.0039 |
| same-action visible policy vs TraceGuard | api_local_replay_visible_policy | api_local_replay_traceguard | risky | Risky block | 12 | 33.333 | 100.0 | 66.667 | 8 | 0 | 4 | 0.0078 | 0.0039 |
| same-action visible policy vs TraceGuard | api_local_replay_visible_policy | api_local_replay_traceguard | safe | Safe utility | 12 | 100.0 | 100.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action visible policy vs TraceGuard | api_local_replay_visible_policy | api_local_replay_traceguard | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action visible policy vs metadata critic | api_local_replay_visible_policy | api_local_replay_metadata_critic | risky | Risky violation | 12 | 66.667 | 0.0 | 66.667 | 8 | 0 | 4 | 0.0078 | 0.0039 |
| same-action visible policy vs metadata critic | api_local_replay_visible_policy | api_local_replay_metadata_critic | risky | LPVR | 12 | 66.667 | 0.0 | 66.667 | 8 | 0 | 4 | 0.0078 | 0.0039 |
| same-action visible policy vs metadata critic | api_local_replay_visible_policy | api_local_replay_metadata_critic | risky | Risky block | 12 | 33.333 | 100.0 | 66.667 | 8 | 0 | 4 | 0.0078 | 0.0039 |
| same-action visible policy vs metadata critic | api_local_replay_visible_policy | api_local_replay_metadata_critic | safe | Safe utility | 12 | 100.0 | 100.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action visible policy vs metadata critic | api_local_replay_visible_policy | api_local_replay_metadata_critic | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action metadata critic vs TraceGuard | api_local_replay_metadata_critic | api_local_replay_traceguard | risky | Risky violation | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action metadata critic vs TraceGuard | api_local_replay_metadata_critic | api_local_replay_traceguard | risky | LPVR | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action metadata critic vs TraceGuard | api_local_replay_metadata_critic | api_local_replay_traceguard | risky | Risky block | 12 | 100.0 | 100.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action metadata critic vs TraceGuard | api_local_replay_metadata_critic | api_local_replay_traceguard | safe | Safe utility | 12 | 100.0 | 100.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| same-action metadata critic vs TraceGuard | api_local_replay_metadata_critic | api_local_replay_traceguard | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| deleted refs vs inferred TraceGuard | api_traceguard_drop_at_sink_replay | api_traceguard_inferred_drop_at_sink_replay | risky | Risky violation | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| deleted refs vs inferred TraceGuard | api_traceguard_drop_at_sink_replay | api_traceguard_inferred_drop_at_sink_replay | risky | LPVR | 12 | 100.0 | 0.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| deleted refs vs inferred TraceGuard | api_traceguard_drop_at_sink_replay | api_traceguard_inferred_drop_at_sink_replay | risky | Risky block | 12 | 0.0 | 100.0 | 100.0 | 12 | 0 | 0 | 0.000488 | 0.000244 |
| deleted refs vs inferred TraceGuard | api_traceguard_drop_at_sink_replay | api_traceguard_inferred_drop_at_sink_replay | safe | Safe utility | 12 | 83.333 | 100.0 | 16.667 | 2 | 0 | 10 | 0.5 | 0.25 |
| deleted refs vs inferred TraceGuard | api_traceguard_drop_at_sink_replay | api_traceguard_inferred_drop_at_sink_replay | safe | Safe false block | 12 | 0.0 | 0.0 | 0.0 | 0 | 0 | 12 | 1 | 1 |
| corrupt refs vs inferred TraceGuard | api_traceguard_corrupt_at_sink_replay | api_traceguard_inferred_corrupt_at_sink_replay | risky | Risky violation | 12 | 83.333 | 0.0 | 83.333 | 10 | 0 | 2 | 0.002 | 0.000977 |
| corrupt refs vs inferred TraceGuard | api_traceguard_corrupt_at_sink_replay | api_traceguard_inferred_corrupt_at_sink_replay | risky | LPVR | 12 | 83.333 | 0.0 | 83.333 | 10 | 0 | 2 | 0.002 | 0.000977 |
| corrupt refs vs inferred TraceGuard | api_traceguard_corrupt_at_sink_replay | api_traceguard_inferred_corrupt_at_sink_replay | risky | Risky block | 12 | 16.667 | 100.0 | 83.333 | 10 | 0 | 2 | 0.002 | 0.000977 |
| corrupt refs vs inferred TraceGuard | api_traceguard_corrupt_at_sink_replay | api_traceguard_inferred_corrupt_at_sink_replay | safe | Safe utility | 12 | 83.333 | 100.0 | 16.667 | 2 | 0 | 10 | 0.5 | 0.25 |
| corrupt refs vs inferred TraceGuard | api_traceguard_corrupt_at_sink_replay | api_traceguard_inferred_corrupt_at_sink_replay | safe | Safe false block | 12 | 16.667 | 0.0 | 16.667 | 2 | 0 | 10 | 0.5 | 0.25 |
