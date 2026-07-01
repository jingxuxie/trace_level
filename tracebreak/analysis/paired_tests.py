from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from math import comb
from pathlib import Path
from typing import Any

from tracebreak.analysis.compute_metrics import read_runs


@dataclass(frozen=True)
class Comparison:
    baseline: str
    comparator: str
    label: str


@dataclass(frozen=True)
class MetricSpec:
    label: str
    key: str
    split: str
    higher_is_better: bool


DEFAULT_COMPARISONS = (
    Comparison("api_local", "api_traceguard", "API local vs TraceGuard"),
    Comparison("api_dlp", "api_traceguard", "API DLP vs TraceGuard"),
    Comparison("api_policy_prompt", "api_traceguard", "API prompt vs TraceGuard"),
    Comparison(
        "api_local_replay_dlp",
        "api_local_replay_traceguard",
        "same-action DLP vs TraceGuard",
    ),
    Comparison(
        "api_local_replay_visible_policy",
        "api_local_replay_traceguard",
        "same-action visible policy vs TraceGuard",
    ),
    Comparison(
        "api_local_replay_visible_policy",
        "api_local_replay_metadata_critic",
        "same-action visible policy vs metadata critic",
    ),
    Comparison(
        "api_local_replay_metadata_critic",
        "api_local_replay_traceguard",
        "same-action metadata critic vs TraceGuard",
    ),
    Comparison(
        "api_traceguard_drop_at_sink_replay",
        "api_traceguard_inferred_drop_at_sink_replay",
        "deleted refs vs inferred TraceGuard",
    ),
    Comparison(
        "api_traceguard_corrupt_at_sink_replay",
        "api_traceguard_inferred_corrupt_at_sink_replay",
        "corrupt refs vs inferred TraceGuard",
    ),
)


METRICS = (
    MetricSpec("Risky violation", "global_violation", "risky", False),
    MetricSpec("LPVR", "local_pass_violation", "risky", False),
    MetricSpec("Risky block", "blocked_risky", "risky", True),
    MetricSpec("Safe utility", "safe_utility_success", "safe", True),
    MetricSpec("Safe false block", "blocked_safe_control", "safe", False),
)


def exact_binomial_two_sided(successes: int, failures: int) -> float:
    trials = successes + failures
    if trials == 0:
        return 1.0
    tail = min(successes, failures)
    probability = 2.0 * sum(comb(trials, k) for k in range(tail + 1)) / (2**trials)
    return min(1.0, probability)


def exact_binomial_improvement_p(improvements: int, regressions: int) -> float:
    trials = improvements + regressions
    if trials == 0 or improvements <= regressions:
        return 1.0
    return sum(comb(trials, k) for k in range(improvements, trials + 1)) / (2**trials)


def summarize_pairs(
    rows: list[dict[str, Any]],
    comparisons: list[Comparison] | tuple[Comparison, ...] = DEFAULT_COMPARISONS,
) -> list[dict[str, Any]]:
    by_condition = _index_by_condition_and_task(rows)
    out: list[dict[str, Any]] = []
    for comparison in comparisons:
        if comparison.baseline not in by_condition or comparison.comparator not in by_condition:
            continue
        baseline_rows = by_condition[comparison.baseline]
        comparator_rows = by_condition[comparison.comparator]
        for metric in METRICS:
            task_ids = [
                task_id
                for task_id in sorted(set(baseline_rows) & set(comparator_rows))
                if baseline_rows[task_id]["risk_label"] == metric.split
                and comparator_rows[task_id]["risk_label"] == metric.split
            ]
            if not task_ids:
                continue
            baseline_positive = 0
            comparator_positive = 0
            improvements = 0
            regressions = 0
            for task_id in task_ids:
                baseline_value = bool(
                    baseline_rows[task_id]["metrics"].get(metric.key, False)
                )
                comparator_value = bool(
                    comparator_rows[task_id]["metrics"].get(metric.key, False)
                )
                baseline_positive += int(baseline_value)
                comparator_positive += int(comparator_value)
                if metric.higher_is_better:
                    improvements += int(comparator_value and not baseline_value)
                    regressions += int(baseline_value and not comparator_value)
                else:
                    improvements += int(baseline_value and not comparator_value)
                    regressions += int(comparator_value and not baseline_value)
            n = len(task_ids)
            ties = n - improvements - regressions
            baseline_rate = 100.0 * baseline_positive / n
            comparator_rate = 100.0 * comparator_positive / n
            better_delta = (
                comparator_rate - baseline_rate
                if metric.higher_is_better
                else baseline_rate - comparator_rate
            )
            out.append(
                {
                    "comparison": comparison.label,
                    "baseline": comparison.baseline,
                    "comparator": comparison.comparator,
                    "split": metric.split,
                    "metric": metric.label,
                    "n_matched": n,
                    "baseline_rate_pct": round(baseline_rate, 3),
                    "comparator_rate_pct": round(comparator_rate, 3),
                    "better_delta_pp": round(better_delta, 3),
                    "improvements": improvements,
                    "regressions": regressions,
                    "ties": ties,
                    "exact_p_two_sided": _format_p(
                        exact_binomial_two_sided(improvements, regressions)
                    ),
                    "exact_p_improvement": _format_p(
                        exact_binomial_improvement_p(improvements, regressions)
                    ),
                }
            )
    return out


def _index_by_condition_and_task(
    rows: list[dict[str, Any]]
) -> dict[str, dict[str, dict[str, Any]]]:
    indexed: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        condition = row["condition"]
        task_id = row["task_id"]
        condition_rows = indexed.setdefault(condition, {})
        if task_id in condition_rows:
            raise ValueError(f"duplicate run for {condition}/{task_id}")
        condition_rows[task_id] = row
    return indexed


def _format_p(value: float) -> str:
    if value < 0.001:
        return f"{value:.3g}"
    return f"{value:.4f}".rstrip("0").rstrip(".")


def parse_comparison(text: str) -> Comparison:
    parts = text.split(":")
    if len(parts) == 2:
        baseline, comparator = parts
        label = f"{baseline} vs {comparator}"
    elif len(parts) == 3:
        baseline, comparator, label = parts
    else:
        raise argparse.ArgumentTypeError(
            "comparison must be baseline:comparator[:label]"
        )
    if not baseline or not comparator:
        raise argparse.ArgumentTypeError("baseline and comparator are required")
    return Comparison(baseline, comparator, label)


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    note = (
        "Exact paired binomial sign tests over matched task IDs. "
        "Positive delta means the comparator is better under the metric polarity.\n\n"
    )
    path.write_text(note + markdown_table(rows), encoding="utf-8")


def markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No paired comparisons available.\n"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[header]) for header in headers) + " |")
    return "\n".join(lines) + "\n"


def write_latex(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = [
        {
            "Comparison": _short_comparison(row["comparison"]),
            "Metric": row["metric"],
            "n": row["n_matched"],
            "Base": _format_percent(row["baseline_rate_pct"]),
            "Comp.": _format_percent(row["comparator_rate_pct"]),
            "+Delta": _format_percent(row["better_delta_pp"]),
            "Imp./reg.": f"{row['improvements']}/{row['regressions']}",
        }
        for row in rows
        if row["metric"] in {"Risky violation", "Safe utility"}
    ]
    path.write_text(latex_table(selected), encoding="utf-8")


def _format_percent(value: float) -> str:
    if value in {0.0, 100.0}:
        return str(int(value))
    if abs(value - round(value)) < 0.05 or value >= 10.0:
        return str(int(round(value)))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _short_comparison(label: str) -> str:
    replacements = {
        "API local vs TraceGuard": "API local",
        "API DLP vs TraceGuard": "API DLP",
        "API prompt vs TraceGuard": "API prompt",
        "same-action DLP vs TraceGuard": "Replay DLP",
        "same-action visible policy vs TraceGuard": "Replay visible policy",
        "same-action visible policy vs metadata critic": "Replay metadata critic",
        "same-action metadata critic vs TraceGuard": "Metadata vs TraceGuard",
        "deleted refs vs inferred TraceGuard": "Deleted refs",
        "corrupt refs vs inferred TraceGuard": "Corrupt refs",
    }
    return replacements.get(label, label)


def latex_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    lines = [
        "\\begin{table}[h]",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{2.5pt}",
        "\\begin{tabular}{llrrrrr}",
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
            "\\caption{Matched-pair counts over API task IDs. Base and Comp. are "
            "rates in percent; +Delta is positive when the comparator improves "
            "the metric under its safety or utility polarity.}",
            "\\label{tab:paired-tests}",
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
    return "".join(replacements.get(char, char) for char in text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--comparison", action="append", type=parse_comparison)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-tex")
    args = parser.parse_args()

    rows = read_runs(args.runs)
    comparisons = args.comparison if args.comparison else DEFAULT_COMPARISONS
    summary = summarize_pairs(rows, comparisons)
    write_csv(summary, Path(args.out_csv))
    write_markdown(summary, Path(args.out_md))
    if args.out_tex:
        write_latex(summary, Path(args.out_tex))
    print(f"read {len(rows)} runs")
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")
    if args.out_tex:
        print(f"wrote {args.out_tex}")


if __name__ == "__main__":
    main()
