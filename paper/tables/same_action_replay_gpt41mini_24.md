# Same-Action API-Local Defense Replay

Counterfactual replay over the same 24 `gpt-4.1-mini` API-local action traces. The proposed model actions are fixed; only the runtime defense changes.

| Defense | n | Safe util. | Risky viol. | LPVR | Risky block | Safe FP |
| --- | --- | --- | --- | --- | --- | --- |
| Local guard | 24 | 100 | 100 | 100 | 0 | 0 |
| DLP replay | 24 | 100 | 100 | 100 | 0 | 0 |
| Visible-policy replay | 24 | 100 | 67 | 67 | 33 | 0 |
| Metadata-critic replay | 24 | 100 | 0 | 0 | 100 | 0 |
| TraceGuard replay | 24 | 100 | 0 | 0 | 100 | 0 |
