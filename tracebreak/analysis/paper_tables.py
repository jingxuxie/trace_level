from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from tracebreak.analysis.compute_metrics import read_runs


Metric = tuple[str, str, Callable[[dict[str, Any]], bool]]


METRICS: list[Metric] = [
    ("Sink", "all", lambda row: row["metrics"]["sink_executed"]),
    ("Safe utility", "safe", lambda row: row["metrics"]["safe_utility_success"]),
    ("Risky violation", "risky", lambda row: row["metrics"]["global_violation"]),
    ("LPVR", "risky", lambda row: row["metrics"]["local_pass_violation"]),
    ("Safe false block", "safe", lambda row: row["metrics"]["blocked_safe_control"]),
    ("Risky block", "risky", lambda row: row["metrics"]["blocked_risky"]),
]


def select_rows(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    if split == "all":
        return rows
    return [row for row in rows if row["risk_label"] == split]


def pct(values: list[bool]) -> float:
    if not values:
        return 0.0
    return 100.0 * sum(bool(value) for value in values) / len(values)


def format_percent(value: float) -> str:
    if value in {0.0, 100.0}:
        return str(int(value))
    if abs(value - round(value)) < 0.05 or value >= 10.0:
        return str(int(round(value)))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def format_calls(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def summarize_point_estimates(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["condition"]].append(row)

    out = []
    for condition, condition_rows in sorted(grouped.items()):
        formatted: dict[str, str] = {
            "condition": condition,
            "n": str(len(condition_rows)),
        }
        for label, split, fn in METRICS:
            selected = select_rows(condition_rows, split)
            values = [bool(fn(row)) for row in selected]
            formatted[label] = format_percent(pct(values))
        model_calls = [
            row["metrics"].get("model_calls")
            for row in condition_rows
            if "model_calls" in row["metrics"]
        ]
        formatted["model calls"] = (
            format_calls(mean(model_calls)) if model_calls else "-"
        )
        out.append(formatted)
    return out


def markdown_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No rows.\n"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[header] for header in headers) + " |")
    return "\n".join(lines) + "\n"


def latex_table(rows: list[dict[str, str]], caption: str, label: str) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    colspec = "l" + "r" * (len(headers) - 1)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        f"\\begin{{tabular}}{{{colspec}}}",
        "\\toprule",
        " & ".join(_latex_escape(header) for header in headers) + " \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(_latex_escape(row[header]) for header in headers) + " \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            f"\\caption{{{_latex_escape(caption)}}}",
            f"\\label{{{_latex_escape(label)}}}",
            "\\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


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


def write_outputs(rows: list[dict[str, str]], out_md: Path, out_tex: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_tex.parent.mkdir(parents=True, exist_ok=True)
    note = "Rates are percentages; model calls are means per task.\n\n"
    out_md.write_text(note + markdown_table(rows), encoding="utf-8")
    out_tex.write_text(
        latex_table(
            rows,
            "TraceBreak point-estimate results.",
            "tab:tracebreak-results",
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-tex", required=True)
    args = parser.parse_args()

    rows = read_runs(args.runs)
    summary = summarize_point_estimates(rows)
    write_outputs(summary, Path(args.out_md), Path(args.out_tex))
    print(f"read {len(rows)} runs")
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_tex}")


if __name__ == "__main__":
    main()
