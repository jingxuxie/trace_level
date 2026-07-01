from __future__ import annotations

import argparse
import csv
import shlex
from pathlib import Path
from typing import Any


REQUIRED_PREFIX = [
    "conda",
    "run",
    "-n",
    "trace_level",
    "python",
    "-m",
    "tracebreak.experiments.run_api_condition",
]


def read_status_rows(paths: list[str | Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path_like in paths:
        path = Path(path_like)
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                rows.append({"sweep_file": path.name, **row})
    return rows


def audit_launch_rows(status_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_audit_row(row) for row in status_rows]


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
    pass_count = sum(row["launch_ready"] == "yes" for row in rows)
    lines = [
        "# Modern Sweep Launch Audit",
        "",
        "No API calls are used. This audit validates the generated paid-run "
        "resume commands before launch: Responses API mode, expected model and "
        "condition, resumable output path, cache path, API-key path, source-ref "
        "and recovery modes, and per-command budget cap.",
        "",
        f"Launch-ready commands: {pass_count}/{len(rows)}.",
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _audit_row(row: dict[str, Any]) -> dict[str, Any]:
    command = row.get("run_command", "")
    try:
        parts = shlex.split(command)
        parse_ok = True
    except ValueError:
        parts = []
        parse_ok = False

    expected = int(row.get("expected") or 0)
    completed = int(row.get("completed") or 0)
    missing = int(row.get("missing") or 0)
    remaining_budget = float(row.get("remaining_budget_cost_usd") or 0.0)
    cap = _float_option(parts, "--max-estimated-cost-usd")
    cap_ok = cap is not None and cap + 1e-9 >= remaining_budget
    prefix_ok = parts[: len(REQUIRED_PREFIX)] == REQUIRED_PREFIX
    output_ok = _option(parts, "--out") == row.get("out_path")
    checks = {
        "parse_ok": parse_ok,
        "prefix_ok": prefix_ok,
        "api_mode_ok": _option(parts, "--api-mode") == "responses",
        "model_ok": _option(parts, "--model") == row.get("model"),
        "condition_ok": _option(parts, "--condition") == row.get("condition"),
        "limit_ok": _option(parts, "--limit") == str(expected),
        "offset_ok": _option(parts, "--offset") == "0",
        "max_steps_ok": _option(parts, "--max-steps") == "8",
        "source_ref_mode_ok": _option(parts, "--source-ref-mode") == "cooperative",
        "recovery_mode_ok": _option(parts, "--recovery-mode") == "stop",
        "recovery_steps_ok": _option(parts, "--recovery-steps") == "3",
        "api_key_path_ok": _option(parts, "--api-key-path") == "../apikey.txt",
        "cache_dir_ok": _option(parts, "--cache-dir") == "results/api_cache",
        "resume_ok": "--resume" in parts,
        "output_path_ok": output_ok,
        "budget_cap_ok": cap_ok,
        "counts_ok": completed + missing == expected,
    }
    launch_ready = all(checks.values())
    return {
        "sweep_file": row.get("sweep_file", ""),
        "model": row.get("model", ""),
        "condition": row.get("condition", ""),
        "expected": expected,
        "completed": completed,
        "missing": missing,
        "out_path": row.get("out_path", ""),
        "remaining_budget_cost_usd": f"{remaining_budget:.6f}",
        "command_budget_cap_usd": "" if cap is None else f"{cap:.6f}",
        **{key: _yes(value) for key, value in checks.items()},
        "launch_ready": _yes(launch_ready),
    }


def _option(parts: list[str], name: str) -> str | None:
    try:
        index = parts.index(name)
    except ValueError:
        return None
    if index + 1 >= len(parts):
        return None
    return parts[index + 1]


def _float_option(parts: list[str], name: str) -> float | None:
    value = _option(parts, name)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _yes(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Sweep": row["sweep_file"],
        "Model": row["model"],
        "Condition": row["condition"],
        "Missing": str(row["missing"]),
        "Budget": f"${float(row['remaining_budget_cost_usd']):.4f}",
        "Cap": f"${float(row['command_budget_cap_usd']):.4f}",
        "Mode": row["api_mode_ok"],
        "Resume": row["resume_ok"],
        "Out": row["output_path_ok"],
        "Cap ok": row["budget_cap_ok"],
        "Ready": row["launch_ready"],
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
    parser.add_argument("--status-csv", nargs="+", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = audit_launch_rows(read_status_rows(args.status_csv))
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
