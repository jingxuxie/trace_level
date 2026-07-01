# Source-Reference Robustness Ablation

This table replays the same 24 `gpt-4.1-mini` TraceGuard action traces under
missing-, corrupted-, and intermediate-erased provenance stress tests. In the
deleted rows, sink source references are removed before policy checking. In the
corrupted rows, each sink is rewritten to point at a benign prior public
observation. In the intermediate-erased rows, refs are removed from derived
tools such as `summarize`, `write_memory`, and `aggregate_records`, while sink
refs are left intact.

| Source-ref mode | Defense | n | Safe utility | Risky violation | Risky LPVR | Risky block | Missing-source blocks | Erased intermediate refs | Safe false block |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cooperative | TraceGuard | 24 | 100 | 0 | 0 | 100 |  |  | 0 |
| deleted-at-sink replay | TraceGuard | 24 | 83 | 100 | 100 | 0 | 0 |  | 0 |
| deleted-at-sink replay | Runtime-inferred TraceGuard | 24 | 100 | 0 | 0 | 100 | 0 |  | 0 |
| deleted-at-sink replay | StrictTraceGuard | 24 | 8.3 | 0 | 0 | 100 | 23 |  | 92 |
| corrupted-at-sink replay | TraceGuard | 24 | 83 | 83 | 83 | 17 | 0 |  | 17 |
| corrupted-at-sink replay | Runtime-inferred TraceGuard | 24 | 100 | 0 | 0 | 100 | 0 |  | 0 |
| corrupted-at-sink replay | StrictTraceGuard | 24 | 83 | 83 | 83 | 17 | 0 |  | 17 |
| intermediate-erased replay | TraceGuard | 24 | 100 | 8.3 | 8.3 | 92 | 0 | 23 | 0 |
| intermediate-erased replay | Runtime-inferred TraceGuard | 24 | 92 | 0 | 0 | 100 | 0 | 23 | 8.3 |
| intermediate-erased replay | StrictTraceGuard | 24 | 100 | 8.3 | 8.3 | 92 | 0 | 23 | 0 |

Interpretation: cooperative TraceGuard blocks all risky sinks while preserving
safe controls. If sink provenance is deleted, ordinary TraceGuard fails because
the decisive source dependency is no longer available at enforcement time. A
runtime-inferred replay recovers the cooperative safety/utility frontier by
reconstructing the sink tag from prior runtime-owned event tags. StrictTraceGuard
also recovers safety by blocking missing-provenance writes after policy-relevant
observations, but it is intentionally conservative and creates high
safe-control false blocking. If sink references are present but corrupted,
StrictTraceGuard no longer helps: the monitor must validate or infer data
dependencies from trusted runtime state. Erasing provenance only at derived
intermediate tools is narrower in this cached subset because many sinks still
refer directly to original observations, but it creates one sensitive-external
risky violation when the sink points to a laundered summary. Runtime inference
recovers safety there, at the cost of one aggregate safe-control false block.
