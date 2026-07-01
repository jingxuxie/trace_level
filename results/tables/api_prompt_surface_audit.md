# API Prompt-Surface Audit

This no-spend audit builds the model-visible API messages along scripted traces and checks that hidden provenance-tag keys and benchmark labels are not serialized into prompts. It also verifies that policy-prompt and multi-agent topology instructions appear only in the expected conditions.

| condition | topology | prompts | hidden metadata hits | task label hits | source-ref instruction | policy prompt | multi-agent prompt | pass |
|---|---|---:|---:|---:|---:|---:|---:|---|
| api_local | single | 520 | 0 | 0 | 520/520 | 0/0 | 0/0 | yes |
| api_dlp | single | 520 | 0 | 0 | 520/520 | 0/0 | 0/0 | yes |
| api_policy_prompt | single | 520 | 0 | 0 | 520/520 | 520/520 | 0/0 | yes |
| api_visible_policy | single | 520 | 0 | 0 | 520/520 | 520/520 | 0/0 | yes |
| api_traceguard | single | 520 | 0 | 0 | 520/520 | 0/0 | 0/0 | yes |
| api_traceguard_inferred | single | 520 | 0 | 0 | 520/520 | 0/0 | 0/0 | yes |
| api_multi_traceguard | multi | 520 | 0 | 0 | 520/520 | 0/0 | 520/520 | yes |
