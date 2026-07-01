from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tracebreak.analysis.compute_metrics import read_runs, summarize


ROW_ORDER = [
    ("api_local", "Local guard"),
    ("api_local_replay_dlp", "DLP replay"),
    ("api_local_replay_visible_policy", "Visible-policy replay"),
    ("api_local_replay_metadata_critic", "Metadata-critic replay"),
    ("api_local_replay_traceguard", "TraceGuard replay"),
]


def build_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = {row["condition"]: row for row in summarize(runs)}
    rows = []
    for condition, label in ROW_ORDER:
        if condition not in summary:
            continue
        row = summary[condition]
        rows.append(
            {
                "Defense": label,
                "n": row["n"],
                "Safe util.": _fmt(row["safe_utility_pct"]),
                "Risky viol.": _fmt(row["risky_global_violation_pct"]),
                "LPVR": _fmt(row["risky_lpvr_pct"]),
                "Risky block": _fmt(row["risky_block_pct"]),
                "Safe FP": _fmt(row["safe_false_block_pct"]),
            }
        )
    return rows


def write_markdown(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Same-Action API-Local Defense Replay",
        "",
        "Counterfactual replay over the same 24 `gpt-4.1-mini` API-local action "
        "traces. The proposed model actions are fixed; only the runtime defense "
        "changes.",
        "",
    ]
    lines.extend(_md_table(rows))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    headers = list(rows[0].keys())
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{4pt}",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        " & ".join(_latex_escape(header) for header in headers) + " \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(_latex_escape(str(row[header])) for header in headers) + " \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\caption{Same-action counterfactual replay over the 24 \\texttt{gpt-4.1-mini} API-local traces. The language-model actions are fixed; only the runtime defense changes.}",
            "\\label{tab:same-action-replay}",
            "\\end{table}",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _fmt(value: Any) -> str:
    return f"{float(value):.1f}"


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

    rows = build_rows(read_runs(args.runs))
    write_markdown(rows, Path(args.out_md))
    write_latex(rows, Path(args.out_tex))
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_tex}")


if __name__ == "__main__":
    main()
