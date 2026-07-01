# Indirect-Injection Overlay Results

Deterministic 120-task stress test after appending synthetic instruction-like text to every document and record body. This is a structural overlay, not a live prompt-injection benchmark.

| Condition | n | Safe util. | Risky viol. | LPVR | Risky block | Safe FP |
| --- | --- | --- | --- | --- | --- | --- |
| Multi local | 120 | 100 | 100 | 100 | 0 | 0 |
| DLP | 120 | 100 | 100 | 100 | 0 | 0 |
| Visible policy | 120 | 100 | 67 | 67 | 33 | 0 |
| TraceGuard | 120 | 100 | 0 | 0 | 100 | 0 |
| Inferred TraceGuard | 120 | 100 | 0 | 0 | 100 | 0 |
