from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


MINIMUM_ITEMS = [
    "gpt-5.4-mini 120-task sweep",
    "gpt-5.5 48-task sweep",
    "source-reference robustness",
    "category-level reporting",
    "paper and bundle validation",
]


def build_readiness_rows(root: Path) -> list[dict[str, Any]]:
    results = root / "results"
    paper = root / "paper"
    dist = root / "dist"
    rows = [
        _sweep_row(
            results,
            item="gpt-5.4-mini 120-task sweep",
            status_file="api_gpt54mini_120_sweep_status.csv",
            expected_total=480,
            next_action=(
                "Run the approved one-task gpt-5.4-mini smoke, then resume the "
                "four-condition 120-task sweep."
            ),
        ),
        _sweep_row(
            results,
            item="gpt-5.5 48-task sweep",
            status_file="api_gpt55_48_sweep_status.csv",
            expected_total=192,
            next_action=(
                "Run after the low-cost modern smoke/sweep path is validated; "
                "keep the generated budget caps."
            ),
        ),
        _artifact_row(
            item="source-reference robustness",
            required=[
                root / "results/api_gpt41mini_source_ref_ablation_24_metrics.csv",
                root / "results/api_gpt41mini_source_ref_compliance.csv",
                root / "paper/tables/source_ref_ablation_gpt41mini_24.md",
                root / "paper/tables/api_gpt41mini_source_ref_compliance.tex",
            ],
            evidence=(
                "cooperative compliance audit plus deleted/corrupted provenance "
                "replays with inferred-source recovery"
            ),
            next_action="Optional live no-instruction API ablation after budget approval.",
        ),
        _artifact_row(
            item="category-level reporting",
            required=[
                root / "results/tables/api_gpt41mini_24_results.md",
                root / "paper/tables/api_gpt41mini_24_by_category.tex",
                root / "paper/tables/api_gpt41mini_category_examples.md",
            ],
            evidence="API by-category table and six-category example gallery",
            next_action="Regenerate analogous tables after modern-model sweeps complete.",
        ),
        _paper_bundle_row(paper=paper, dist=dist),
        _sweep_row(
            results,
            item="multi-agent topology 24-task status",
            status_file="api_gpt54mini_multi_topology_24_sweep_status.csv",
            expected_total=96,
            next_action=(
                "Run after the one-task modern smoke succeeds; keep the "
                "generated resume commands and budget caps."
            ),
            minimum_package=False,
        ),
        _artifact_row(
            item="prompt-surface and recovery audits",
            required=[
                results / "api_prompt_surface_audit.csv",
                results / "api_recovery_prompt_audit.csv",
                results / "tables/api_prompt_surface_audit.md",
                results / "tables/api_recovery_prompt_audit.md",
            ],
            evidence=(
                "model-visible hidden-metadata audit plus recovery-prompt "
                "placement audit"
            ),
            next_action="Repeat after adding any new API prompt condition.",
            minimum_package=False,
        ),
        _artifact_row(
            item="critic and replay baselines",
            required=[
                results / "api_gpt41mini_critic_baseline_audit.csv",
                results / "api_gpt41mini_same_action_replay_metrics.csv",
                results / "tables/api_gpt41mini_critic_baseline_audit.md",
                results / "tables/api_gpt41mini_same_action_replay_results.md",
            ],
            evidence=(
                "same-action replay plus visible-critic and metadata-critic "
                "information-boundary accounting"
            ),
            next_action="Optional live critic baseline only if API budget remains after modern sweeps.",
            minimum_package=False,
        ),
        _artifact_row(
            item="deterministic stress tests",
            required=[
                results / "injection_overlay_metrics.csv",
                results / "decoy_stress_metrics.csv",
                paper / "tables/injection_overlay_deterministic_120.tex",
                paper / "tables/decoy_stress_deterministic_120.tex",
            ],
            evidence=(
                "scripted indirect-injection overlay and decoy-clutter checks "
                "with paper-facing tables for ordinary and runtime-inferred TraceGuard"
            ),
            next_action="Treat as structural stress evidence, not a live model-selection benchmark.",
            minimum_package=False,
        ),
        _artifact_row(
            item="bibliography integrity audit",
            required=[
                results / "bibliography_audit.csv",
                results / "tables/bibliography_audit.md",
            ],
            evidence=(
                "TeX, BibTeX, generated bibliography, and LaTeX/BibTeX logs "
                "agree with no stale or malformed citation keys"
            ),
            next_action="Rerun after changing related work or bibliography metadata.",
            minimum_package=False,
        ),
        _artifact_row(
            item="claim-boundary audit",
            required=[
                results / "claim_boundary_audit.csv",
                results / "tables/claim_boundary_audit.md",
            ],
            evidence=(
                "main manuscript and readiness report keep API scope, synthetic "
                "scope, provenance caveat, live-recovery limitation, and paid "
                "modern-model blocker explicit"
            ),
            next_action="Rerun after changing main-paper claims, limitations, or readiness status.",
            minimum_package=False,
        ),
        _artifact_row(
            item="paid smoke preflight",
            required=[
                results / "api_gpt54mini_paid_smoke_preflight.csv",
                results / "api_gpt54mini_paid_smoke_payload.json",
                results / "tables/api_gpt54mini_paid_smoke_preflight.md",
                results / "tables/api_paid_smoke_next_step.md",
            ],
            evidence="strict Responses payload contract and $0.02 budget guard",
            next_action="Requires explicit approval before reading API key or making network call.",
            minimum_package=False,
        ),
    ]
    return rows


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    minimum = [row for row in rows if row["minimum_package"]]
    complete = sum(row["status"] == "complete" for row in minimum)
    lines = [
        "# Research Readiness Report",
        "",
        (
            f"Minimum package status: {complete}/{len(minimum)} items complete. "
            "Modern-model evidence remains incomplete until paid API rows exist."
        ),
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sweep_row(
    results_dir: Path,
    *,
    item: str,
    status_file: str,
    expected_total: int,
    next_action: str,
    minimum_package: bool = True,
) -> dict[str, Any]:
    path = results_dir / status_file
    rows = _read_csv(path) if path.exists() else []
    completed = sum(int(row.get("completed") or 0) for row in rows)
    missing = sum(int(row.get("missing") or 0) for row in rows)
    expected = sum(int(row.get("expected") or 0) for row in rows)
    if not rows:
        status = "missing"
        evidence = f"missing {path}"
    elif expected != expected_total:
        status = "incomplete"
        evidence = f"{path}: expected {expected}, wanted {expected_total}"
    elif completed == expected_total and missing == 0:
        status = "complete"
        evidence = f"{path}: {completed}/{expected_total} rows complete"
    else:
        status = "blocked_on_paid_api"
        evidence = f"{path}: {completed}/{expected_total} rows complete, {missing} missing"
    return {
        "item": item,
        "minimum_package": minimum_package,
        "status": status,
        "completed": completed,
        "expected": expected_total,
        "evidence": evidence,
        "next_action": next_action,
    }


def _artifact_row(
    *,
    item: str,
    required: list[Path],
    evidence: str,
    next_action: str,
    minimum_package: bool = True,
) -> dict[str, Any]:
    missing = [str(path) for path in required if not path.exists()]
    status = "complete" if not missing else "missing"
    return {
        "item": item,
        "minimum_package": minimum_package,
        "status": status,
        "completed": 0 if missing else len(required),
        "expected": len(required),
        "evidence": evidence if not missing else "missing: " + "; ".join(missing),
        "next_action": next_action,
    }


def _paper_bundle_row(*, paper: Path, dist: Path) -> dict[str, Any]:
    return _artifact_row(
        item="paper and bundle validation",
        required=[
            paper / "main.pdf",
            paper / "supplement.pdf",
            dist / "tracebreak_submission_bundle.zip",
        ],
        evidence="compiled PDFs, release gate, and anonymized submission bundle",
        next_action=(
            "Rerun scripts/run_release_checks.py after any paper or result-table change."
        ),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Item": row["item"],
        "Minimum": "yes" if row["minimum_package"] else "no",
        "Status": row["status"],
        "Progress": f"{row['completed']}/{row['expected']}",
        "Evidence": row["evidence"],
        "Next action": row["next_action"],
    }


def _md_table(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["No rows."]
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(header, "") for header in headers) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    root = Path(args.root)
    rows = build_readiness_rows(root)
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
