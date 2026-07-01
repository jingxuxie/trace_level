# Modern Sweep Launch Audit

No API calls are used. This audit validates the generated paid-run resume commands before launch: Responses API mode, expected model and condition, resumable output path, cache path, API-key path, source-ref and recovery modes, and per-command budget cap.

Launch-ready commands: 18/18.

| Sweep | Model | Condition | Missing | Budget | Cap | Mode | Resume | Out | Cap ok | Ready |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| api_gpt54mini_120_sweep_status.csv | gpt-5.4-mini | api_local | 120 | $1.5519 | $1.5519 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_sweep_status.csv | gpt-5.4-mini | api_dlp | 120 | $1.5519 | $1.5519 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_sweep_status.csv | gpt-5.4-mini | api_policy_prompt | 120 | $1.6342 | $1.6343 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_sweep_status.csv | gpt-5.4-mini | api_traceguard | 120 | $1.5506 | $1.5506 | yes | yes | yes | yes | yes |
| api_gpt55_48_sweep_status.csv | gpt-5.5 | api_local | 48 | $4.1385 | $4.1385 | yes | yes | yes | yes | yes |
| api_gpt55_48_sweep_status.csv | gpt-5.5 | api_dlp | 48 | $4.1385 | $4.1385 | yes | yes | yes | yes | yes |
| api_gpt55_48_sweep_status.csv | gpt-5.5 | api_policy_prompt | 48 | $4.3580 | $4.3580 | yes | yes | yes | yes | yes |
| api_gpt55_48_sweep_status.csv | gpt-5.5 | api_traceguard | 48 | $4.1348 | $4.1348 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_plus_visible_sweep_status.csv | gpt-5.4-mini | api_local | 120 | $1.5519 | $1.5519 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_plus_visible_sweep_status.csv | gpt-5.4-mini | api_dlp | 120 | $1.5519 | $1.5519 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_plus_visible_sweep_status.csv | gpt-5.4-mini | api_policy_prompt | 120 | $1.6342 | $1.6343 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_plus_visible_sweep_status.csv | gpt-5.4-mini | api_traceguard | 120 | $1.5506 | $1.5506 | yes | yes | yes | yes | yes |
| api_gpt54mini_120_plus_visible_sweep_status.csv | gpt-5.4-mini | api_visible_policy | 120 | $1.6338 | $1.6338 | yes | yes | yes | yes | yes |
| api_gpt55_48_plus_visible_sweep_status.csv | gpt-5.5 | api_local | 48 | $4.1385 | $4.1385 | yes | yes | yes | yes | yes |
| api_gpt55_48_plus_visible_sweep_status.csv | gpt-5.5 | api_dlp | 48 | $4.1385 | $4.1385 | yes | yes | yes | yes | yes |
| api_gpt55_48_plus_visible_sweep_status.csv | gpt-5.5 | api_policy_prompt | 48 | $4.3580 | $4.3580 | yes | yes | yes | yes | yes |
| api_gpt55_48_plus_visible_sweep_status.csv | gpt-5.5 | api_traceguard | 48 | $4.1348 | $4.1348 | yes | yes | yes | yes | yes |
| api_gpt55_48_plus_visible_sweep_status.csv | gpt-5.5 | api_visible_policy | 48 | $4.3569 | $4.3569 | yes | yes | yes | yes | yes |
