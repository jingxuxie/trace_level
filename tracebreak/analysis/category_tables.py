from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from tracebreak.analysis.compute_metrics import pct, read_runs


CONDITION_LABELS = {
    "api_local": "Local",
    "api_dlp": "DLP",
    "api_policy_prompt": "Prompt",
    "api_traceguard": "TraceGuard",
}


def summarize_category_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["category"], row["condition"])].append(row)

    out = []
    for category in sorted({row["category"] for row in rows}):
        category_rows = [row for row in rows if row["category"] == category]
        item: dict[str, Any] = {
            "category": category,
            "safe_n": sum(row["risk_label"] == "safe" for row in category_rows)
            // max(len({row["condition"] for row in category_rows}), 1),
            "risky_n": sum(row["risk_label"] == "risky" for row in category_rows)
            // max(len({row["condition"] for row in category_rows}), 1),
        }
        for condition in ["api_local", "api_dlp", "api_policy_prompt", "api_traceguard"]:
            group = grouped[(category, condition)]
            risky = [row for row in group if row["risk_label"] == "risky"]
            safe = [row for row in group if row["risk_label"] == "safe"]
            label = CONDITION_LABELS[condition]
            item[f"{label} risky viol."] = round(
                pct(sum(row["metrics"]["global_violation"] for row in risky), len(risky)),
                1,
            )
            item[f"{label} LPVR"] = round(
                pct(sum(row["metrics"]["local_pass_violation"] for row in risky), len(risky)),
                1,
            )
            item[f"{label} risky block"] = round(
                pct(sum(row["metrics"]["blocked_risky"] for row in risky), len(risky)),
                1,
            )
            item[f"{label} safe util."] = round(
                pct(sum(row["metrics"]["safe_utility_success"] for row in safe), len(safe)),
                1,
            )
        out.append(item)
    return out


def write_markdown(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# API Category-Level Results",
        "",
        "Rates are percentages over the 24-task `gpt-4.1-mini` API subset: "
        "two risky and two safe-control tasks per category.",
        "",
    ]
    lines.extend(_md_table(rows))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    compact_rows = []
    for row in rows:
        compact_rows.append(
            {
                "Category": row["category"].replace("_", " "),
                "Local viol.": row["Local risky viol."],
                "DLP viol.": row["DLP risky viol."],
                "Prompt viol.": row["Prompt risky viol."],
                "TG viol.": row["TraceGuard risky viol."],
                "TG block": row["TraceGuard risky block"],
                "TG safe util.": row["TraceGuard safe util."],
            }
        )

    headers = list(compact_rows[0].keys())
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        " & ".join(_latex_escape(header) for header in headers) + " \\\\",
        "\\midrule",
    ]
    for row in compact_rows:
        lines.append(
            " & ".join(_latex_escape(str(row[header])) for header in headers) + " \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\caption{Category-level API results on the 24-task \\texttt{gpt-4.1-mini} subset. Each category has two risky and two safe-control tasks.}",
            "\\label{tab:api-category}",
            "\\end{table}",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _md_table(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["No rows."]
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
    }
    return "".join(replacements.get(char, char) for char in str(text))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-tex", required=True)
    args = parser.parse_args()

    rows = read_runs(args.runs)
    summary = summarize_category_rows(rows)
    write_markdown(summary, Path(args.out_md))
    write_latex(summary, Path(args.out_tex))
    print(f"read {len(rows)} runs")
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_tex}")


if __name__ == "__main__":
    main()
