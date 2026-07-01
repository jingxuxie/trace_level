# Repair-Oracle Upper Bound

This table replays the 12 risky `gpt-4.1-mini` API TraceGuard traces whose
unsafe sink was blocked. A deterministic repair oracle then appends one
policy-compliant alternative sink based on the matched safe-control task. This
is not model behavior; it is an upper-bound analysis showing whether the blocked
trace contains enough state for a compliant continuation.

| Condition | Repair candidates | Repair success | Repair blocked | Risky violation after repair | Categories covered |
| --- | ---: | ---: | ---: | ---: | ---: |
| API TraceGuard repair oracle | 12 | 100 | 0 | 0 | 6 |

Interpretation: every blocked risky API TraceGuard trace has a one-step
policy-compliant continuation under the matched-control oracle. This suggests
that TraceGuard blocks need not destroy utility, but it does not show that the
language-model agent will discover the repair without a live recovery run.
