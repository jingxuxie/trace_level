from __future__ import annotations

import argparse
import json
import random
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


def bootstrap_ci(
    values: list[bool],
    *,
    samples: int = 5000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    estimates = []
    for _ in range(samples):
        draw = [values[rng.randrange(n)] for _ in range(n)]
        estimates.append(pct(draw))
    estimates.sort()
    lo_index = int((alpha / 2.0) * (samples - 1))
    hi_index = int((1.0 - alpha / 2.0) * (samples - 1))
    return estimates[lo_index], estimates[hi_index]


def summarize_with_ci(rows: list[dict[str, Any]], samples: int, seed: int) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["condition"]].append(row)

    out = []
    for condition, condition_rows in sorted(grouped.items()):
        formatted: dict[str, str] = {
            "condition": condition,
            "n": str(len(condition_rows)),
        }
        for idx, (label, split, fn) in enumerate(METRICS):
            selected = select_rows(condition_rows, split)
            values = [bool(fn(row)) for row in selected]
            estimate = pct(values)
            lo, hi = bootstrap_ci(values, samples=samples, seed=seed + idx)
            formatted[label] = f"{estimate:.1f} [{lo:.1f}, {hi:.1f}]"
        model_calls = [
            row["metrics"].get("model_calls")
            for row in condition_rows
            if "model_calls" in row["metrics"]
        ]
        formatted["model calls"] = (
            f"{mean(model_calls):.2f}" if model_calls else "-"
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
    note = (
        "Rates are percentages with 95% nonparametric bootstrap confidence intervals.\n\n"
    )
    out_md.write_text(note + markdown_table(rows), encoding="utf-8")
    out_tex.write_text(
        latex_table(
            rows,
            "TraceBreak results with 95% bootstrap confidence intervals.",
            "tab:tracebreak-results",
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-tex", required=True)
    parser.add_argument("--samples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    rows = read_runs(args.runs)
    summary = summarize_with_ci(rows, samples=args.samples, seed=args.seed)
    write_outputs(summary, Path(args.out_md), Path(args.out_tex))
    print(f"read {len(rows)} runs")
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_tex}")


if __name__ == "__main__":
    main()
