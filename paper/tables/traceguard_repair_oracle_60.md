# Deterministic Repair-Oracle Upper Bound

This table replays the 60 risky scripted TraceGuard traces whose unsafe sink was
blocked. A deterministic repair oracle then appends the matched safe-control
continuation. This is not model behavior; it is an upper-bound analysis showing
whether the blocked trace contains enough state for a compliant continuation.

| Condition | Repair candidates | Repair success | Repair blocked | Risky violation after repair | Categories covered | Max repair steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted TraceGuard repair oracle | 60 | 100 | 0 | 0 | 6 | 2 |

Interpretation: every blocked risky scripted TraceGuard trace has a
policy-compliant continuation under the matched-control oracle. Five categories
repair in one step by changing the sink target or approval fields; aggregation
repairs require one additional aggregate operation before emailing the aggregate
summary. This strengthens the utility story while preserving the limitation
that live model recovery remains unmeasured.
