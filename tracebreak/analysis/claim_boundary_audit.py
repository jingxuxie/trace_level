from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


BOUNDARY_CHECKS = [
    {
        "boundary": "api_subset_scope",
        "source": "paper/main.tex",
        "require": [
            "24-task API subset using \\texttt{gpt-4.1-mini}",
            "covering two risky/safe pairs per category",
        ],
        "note": "Main-paper API claims are scoped to the cached gpt-4.1-mini subset.",
    },
    {
        "boundary": "api_preliminary_not_leaderboard",
        "source": "paper/main.tex",
        "require": [
            "API results are preliminary evidence, not a model leaderboard",
            "zero observed\nTraceGuard violations cover TraceBreak invariants, not arbitrary enterprise\npolicies",
        ],
        "note": "The limitations distinguish benchmark evidence from a broad model or product claim.",
    },
    {
        "boundary": "synthetic_no_real_services",
        "source": "paper/main.tex",
        "require": [
            "TraceBreak is synthetic",
            "no real email, ticketing, browsing, or\nexternal enterprise systems are used",
        ],
        "note": "The release/safety claim stays tied to synthetic local simulator data.",
    },
    {
        "boundary": "provenance_dependency",
        "source": "paper/main.tex",
        "require": [
            "ordinary monitor still trusts correct \\texttt{source\\_refs}",
            "Production monitors should validate provenance or\ninfer runtime dependencies rather than trust model-authored fields",
        ],
        "note": "The paper preserves the distinction between cooperative refs and trusted runtime inference.",
    },
    {
        "boundary": "live_recovery_future_work",
        "source": "paper/main.tex",
        "require": [
            "A matched-control oracle finds safe continuations for blocked traces,\nbut live recovery remains future work",
        ],
        "note": "The repair-oracle result is not overstated as live model recovery.",
    },
    {
        "boundary": "modern_model_rows_missing",
        "source": "results/tables/research_readiness_report.md",
        "require": [
            "Modern-model evidence remains incomplete until paid API rows exist",
            "gpt-5.4-mini 120-task sweep | yes | blocked_on_paid_api | 0/480",
            "gpt-5.5 48-task sweep | yes | blocked_on_paid_api | 0/192",
        ],
        "note": "The readiness report keeps the minimum-package modern-model gap explicit.",
    },
]


def build_claim_boundary_rows(root: str | Path = ".") -> list[dict[str, Any]]:
    base = Path(root)
    rows: list[dict[str, Any]] = []
    for check in BOUNDARY_CHECKS:
        source_path = base / check["source"]
        text = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        missing = [phrase for phrase in check["require"] if phrase not in text]
        rows.append(
            {
                "boundary": check["boundary"],
                "source": check["source"],
                "required_phrases": len(check["require"]),
                "missing_phrases": len(missing),
                "missing": " || ".join(missing),
                "note": check["note"],
                "pass": not missing,
            }
        )
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
    lines = [
        "# Claim Boundary Audit",
        "",
        "No API calls are used. This audit checks that the manuscript and "
        "readiness report keep the key claim boundaries explicit: cached API "
        "subset scope, preliminary-model scope, synthetic-data scope, provenance "
        "dependency, live-recovery limitation, and missing modern-model rows.",
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "boundary": str(row["boundary"]),
        "source": str(row["source"]),
        "required": str(row["required_phrases"]),
        "missing": str(row["missing_phrases"]),
        "pass": "yes" if row["pass"] else "no",
        "note": str(row["note"]),
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

    rows = build_claim_boundary_rows(args.root)
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
