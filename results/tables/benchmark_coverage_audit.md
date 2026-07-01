# Benchmark Coverage Audit

No API calls are used. This audit summarizes benchmark structure from the generated task definitions and scripted plans.

Overall coverage: 120 tasks over 10 seeds, 60 risky/safe pairs, 40 visible-fact tasks, and 80 hidden-metadata tasks.

| Category | Tasks | Pairs | Seeds | Fact | Flow | Sinks | Targets | Sources | Steps | Pair delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aggregation threshold | 20 (10 risky/10 safe) | 10 | 10 | visible | multi_record_email | send_email=20 | 1 | 80 unique; 8-8 per task | 10-11 | aggregate_only |
| approval scope | 20 (10 risky/10 safe) | 10 | 10 | visible | approval_doc_email | send_email=20 | 2 | 20 unique; 2-2 per task | 4-4 | recipient_id |
| audience restriction | 20 (10 risky/10 safe) | 10 | 10 | hidden | audience_doc_email | send_email=20 | 2 | 10 unique; 1-1 per task | 4-4 | recipient_id |
| cross tenant | 20 (10 risky/10 safe) | 10 | 10 | hidden | record_ticket | post_ticket=20 | 2 | 10 unique; 1-1 per task | 2-2 | customer_id |
| memory laundering | 20 (10 risky/10 safe) | 10 | 10 | hidden | memory_handoff_email | send_email=20 | 2 | 10 unique; 1-1 per task | 4-4 | recipient_id |
| sensitive external | 20 (10 risky/10 safe) | 10 | 10 | hidden | confidential_doc_email | send_email=20 | 2 | 10 unique; 1-1 per task | 4-4 | recipient_id |
| overall | 120 (60 risky/60 safe) | 60 | 10 | mixed | 6 archetypes | post_ticket=20; send_email=100 | 7 | 130 unique; 1-8 per task | 2-11 | aggregate_only,customer_id,recipient_id |
