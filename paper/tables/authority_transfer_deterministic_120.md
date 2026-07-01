# Multi-Agent Authority-Transfer Results

A transfer sink is an expected write sink whose referenced output was produced by another actor, or by a memory handoff. Rates are computed from deterministic 120-task traces.

| Condition | Risky transfer | Viol. after transfer | Block after transfer | Safe util. after transfer |
| --- | --- | --- | --- | --- |
| Single local | 17 | 100 | 0 | 100 |
| Multi local | 100 | 100 | 0 | 100 |
| DLP | 100 | 100 | 0 | 100 |
| Visible policy | 100 | 67 | 33 | 100 |
| TraceGuard | 100 | 0 | 100 | 100 |
