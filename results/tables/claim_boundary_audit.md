# Claim Boundary Audit

No API calls are used. This audit checks that the manuscript and readiness report keep the key claim boundaries explicit: cached API subset scope, preliminary-model scope, synthetic-data scope, provenance dependency, live-recovery limitation, and missing modern-model rows.

| boundary | source | required | missing | pass | note |
| --- | --- | --- | --- | --- | --- |
| api_subset_scope | paper/main.tex | 2 | 0 | yes | Main-paper API claims are scoped to the cached gpt-4.1-mini subset. |
| api_preliminary_not_leaderboard | paper/main.tex | 2 | 0 | yes | The limitations distinguish benchmark evidence from a broad model or product claim. |
| synthetic_no_real_services | paper/main.tex | 2 | 0 | yes | The release/safety claim stays tied to synthetic local simulator data. |
| provenance_dependency | paper/main.tex | 2 | 0 | yes | The paper preserves the distinction between cooperative refs and trusted runtime inference. |
| live_recovery_future_work | paper/main.tex | 1 | 0 | yes | The repair-oracle result is not overstated as live model recovery. |
| modern_model_rows_missing | results/tables/research_readiness_report.md | 3 | 0 | yes | The readiness report keeps the minimum-package modern-model gap explicit. |
