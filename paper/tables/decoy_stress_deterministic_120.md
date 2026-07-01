# Decoy-Ambiguity Stress Results

Deterministic 120-task stress test after adding plausible decoy documents, recipients, approvals, and records to each synthetic world. Search preambles expose the decoys, but scripted plans still choose the ground-truth target IDs; this is a structural clutter check, not a live model-selection benchmark.

| Condition | n | Decoy hits | Safe util. | Risky viol. | LPVR | Risky block | Safe FP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Multi local | 120 | 260 | 100 | 100 | 100 | 0 | 0 |
| DLP | 120 | 260 | 100 | 100 | 100 | 0 | 0 |
| Visible policy | 120 | 260 | 100 | 67 | 67 | 33 | 0 |
| TraceGuard | 120 | 260 | 100 | 0 | 0 | 100 | 0 |
| Inferred TraceGuard | 120 | 260 | 100 | 0 | 0 | 100 | 0 |
