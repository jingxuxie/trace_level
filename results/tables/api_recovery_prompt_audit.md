# API Recovery Prompt Audit

This no-spend audit simulates scripted traces, builds the model-visible API messages, and verifies that the policy-compliant recovery instruction is serialized only in the first prompt after a defense-blocked write sink.

| condition | max steps | prompts | blocked sinks | recovery prompts | pre-block hits | safe-control hits | pass |
|---|---:|---:|---:|---:|---:|---:|---|
| api_local | 8 | 520 | 0 | 0/0 | 0 | 0 | yes |
| api_dlp | 8 | 520 | 0 | 0/0 | 0 | 0 | yes |
| api_visible_policy | 8 | 530 | 10 | 10/10 | 0 | 0 | yes |
| api_traceguard | 8 | 570 | 50 | 50/50 | 0 | 0 | yes |
| api_traceguard_inferred | 8 | 570 | 50 | 50/50 | 0 | 0 | yes |
