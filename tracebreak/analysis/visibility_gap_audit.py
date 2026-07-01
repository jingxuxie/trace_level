from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from tracebreak.analysis.compute_metrics import read_runs


CATEGORY_FACTS = {
    "aggregation_threshold": "visible record count / bulk export",
    "approval_scope": "visible approval identifier and recipient",
    "audience_restriction": "hidden allowed audience tag",
    "cross_tenant": "hidden source tenant tag",
    "memory_laundering": "hidden memory provenance tag",
    "sensitive_external": "hidden confidentiality and recipient metadata",
}

LATEX_FACT_LABELS = {
    "aggregation_threshold": "visible bulk count",
    "approval_scope": "visible approval",
    "audience_restriction": "hidden audience",
    "cross_tenant": "hidden tenant",
    "memory_laundering": "hidden memory provenance",
    "sensitive_external": "hidden confidentiality/recipient",
    "overall": "visible subset + hidden metadata",
}

CONDITION_LABELS = {
    "api_local_replay_visible_policy": "Visible policy",
    "api_local_replay_metadata_critic": "Metadata critic",
    "api_local_replay_traceguard": "TraceGuard",
}


def summarize_visibility_gap(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("condition") in CONDITION_LABELS:
            grouped[(row["condition"], row["category"])].append(row)

    out = []
    for category in sorted(CATEGORY_FACTS):
        out.append(_summarize_category(category, grouped))
    if out:
        out.append(_summarize_overall(out))
    return out


def write_csv(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Same-Action Visibility-Gap Audit",
        "",
        "Counterfactual audit over fixed `gpt-4.1-mini` API-local actions. "
        "The visible-policy replay sees task text, visible trace, proposed sink, "
        "and policy text, but not hidden source tags. The metadata critic and "
        "TraceGuard replay use hidden metadata. Counts are over risky rows unless "
        "the column names safe utility.",
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Category & Decisive fact & Visible block & Visible viol. & Metadata block & TG block \\\\",
        "\\midrule",
    ]
    for row in rows:
        if row["category"] == "overall":
            lines.append("\\midrule")
        lines.append(
            f"{_latex_escape(row['category'].replace('_', ' '))} & "
            f"{_latex_escape(LATEX_FACT_LABELS[row['category']])} & "
            f"{row['visible_policy_block_n']}/{row['risky_n']} & "
            f"{row['visible_policy_violation_n']}/{row['risky_n']} & "
            f"{row['metadata_critic_block_n']}/{row['risky_n']} & "
            f"{row['traceguard_block_n']}/{row['risky_n']} \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\caption{Same-action visibility-gap audit over fixed \\texttt{gpt-4.1-mini} API-local traces. Visible-policy review catches only categories whose decisive fact is visible at the sink; metadata-aware review and TraceGuard catch every risky sink.}",
            "\\label{tab:visibility-gap-audit}",
            "\\end{table}",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _summarize_category(
    category: str,
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    visible = grouped[("api_local_replay_visible_policy", category)]
    metadata = grouped[("api_local_replay_metadata_critic", category)]
    traceguard = grouped[("api_local_replay_traceguard", category)]
    visible_risky = [row for row in visible if row["risk_label"] == "risky"]
    visible_safe = [row for row in visible if row["risk_label"] == "safe"]
    metadata_risky = [row for row in metadata if row["risk_label"] == "risky"]
    metadata_safe = [row for row in metadata if row["risk_label"] == "safe"]
    traceguard_risky = [row for row in traceguard if row["risk_label"] == "risky"]
    traceguard_safe = [row for row in traceguard if row["risk_label"] == "safe"]

    return {
        "category": category,
        "decisive_fact": CATEGORY_FACTS[category],
        "risky_n": len(visible_risky),
        "safe_n": len(visible_safe),
        "visible_policy_block_n": _sum_metric(visible_risky, "blocked_risky"),
        "visible_policy_violation_n": _sum_metric(visible_risky, "global_violation"),
        "visible_policy_safe_utility_n": _sum_metric(visible_safe, "safe_utility_success"),
        "metadata_critic_block_n": _sum_metric(metadata_risky, "blocked_risky"),
        "metadata_critic_violation_n": _sum_metric(metadata_risky, "global_violation"),
        "metadata_critic_safe_utility_n": _sum_metric(metadata_safe, "safe_utility_success"),
        "traceguard_block_n": _sum_metric(traceguard_risky, "blocked_risky"),
        "traceguard_violation_n": _sum_metric(traceguard_risky, "global_violation"),
        "traceguard_safe_utility_n": _sum_metric(traceguard_safe, "safe_utility_success"),
    }


def _summarize_overall(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "risky_n",
        "safe_n",
        "visible_policy_block_n",
        "visible_policy_violation_n",
        "visible_policy_safe_utility_n",
        "metadata_critic_block_n",
        "metadata_critic_violation_n",
        "metadata_critic_safe_utility_n",
        "traceguard_block_n",
        "traceguard_violation_n",
        "traceguard_safe_utility_n",
    ]
    return {
        "category": "overall",
        "decisive_fact": "visible subset plus hidden metadata",
        **{key: sum(row[key] for row in rows) for key in keys},
    }


def _sum_metric(rows: list[dict[str, Any]], metric: str) -> int:
    return sum(bool(row.get("metrics", {}).get(metric, False)) for row in rows)


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Category": row["category"].replace("_", " "),
        "Decisive fact": row["decisive_fact"],
        "Visible block": f"{row['visible_policy_block_n']}/{row['risky_n']}",
        "Visible violation": f"{row['visible_policy_violation_n']}/{row['risky_n']}",
        "Metadata block": f"{row['metadata_critic_block_n']}/{row['risky_n']}",
        "TraceGuard block": f"{row['traceguard_block_n']}/{row['risky_n']}",
        "Safe utility (visible/meta/TG)": (
            f"{row['visible_policy_safe_utility_n']}/"
            f"{row['metadata_critic_safe_utility_n']}/"
            f"{row['traceguard_safe_utility_n']} of {row['safe_n']}"
        ),
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
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-tex", required=True)
    args = parser.parse_args()

    rows = summarize_visibility_gap(read_runs(args.runs))
    write_csv(rows, Path(args.out_csv))
    write_markdown(rows, Path(args.out_md))
    write_latex(rows, Path(args.out_tex))
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_tex}")


if __name__ == "__main__":
    main()
