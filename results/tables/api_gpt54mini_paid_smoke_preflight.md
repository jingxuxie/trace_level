# Paid API Smoke Preflight

No API calls are made by this audit. It validates the first planned Responses API request payload and budget guard before the paid modern-model smoke is approved.

| Model | Condition | Task | API | Format | Strict | Refs required | Refs nullable array | No extra props | Source-ref prompt | Policy prompt | Auth header | Budget | Pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-5.4-mini | api_local | sensitive_external_000_risky | responses | json_schema:tracebreak_action | yes | yes | yes | yes | yes | no | no | $0.0130 <= $0.0200 | yes |
