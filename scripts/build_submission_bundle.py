"""Build the anonymized TraceBreak submission artifact bundle."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dist" / "tracebreak_submission_bundle.zip"

TOP_LEVEL_FILES = [
    "ARTIFACT_MANIFEST.md",
    "README.md",
    "REPRODUCIBILITY.md",
    "SUBMISSION_CHECKLIST.md",
    "pyproject.toml",
    "data/tasks_tracebreak_120.jsonl",
    "results/EXPERIMENT_SUMMARY.md",
    "results/metrics.csv",
    "results/injection_overlay_metrics.csv",
    "results/decoy_stress_metrics.csv",
    "results/api_gpt41mini_24_metrics.csv",
    "results/api_gpt41mini_same_action_replay_metrics.csv",
    "results/api_gpt41mini_visibility_gap_audit.csv",
    "results/api_gpt41mini_critic_baseline_audit.csv",
    "results/api_gpt41mini_source_ref_compliance.csv",
    "results/api_gpt41mini_source_ref_ablation_24_metrics.csv",
    "results/api_gpt41mini_repair_oracle_metrics.csv",
    "results/traceguard_repair_oracle_60_metrics.csv",
    "results/api_gpt41mini_paired_tests.csv",
    "results/api_gpt41mini_policy_prompt_diagnostics.csv",
    "results/traceguard_block_reason_audit.csv",
    "results/benchmark_fact_audit.csv",
    "results/benchmark_coverage_audit.csv",
    "results/bibliography_audit.csv",
    "results/claim_boundary_audit.csv",
    "results/traceguard_inferred_metrics.csv",
    "results/api_prompt_surface_audit.csv",
    "results/api_recovery_prompt_audit.csv",
    "results/api_modern_sweep_cost_estimate.csv",
    "results/api_gpt55_48_cost_estimate.csv",
    "results/api_gpt54mini_120_plus_visible_cost_estimate.csv",
    "results/api_gpt55_48_plus_visible_cost_estimate.csv",
    "results/api_gpt54mini_no_source_ref_instruction_24_cost_estimate.csv",
    "results/api_gpt54mini_120_sweep_status.csv",
    "results/api_gpt55_48_sweep_status.csv",
    "results/api_gpt54mini_120_plus_visible_sweep_status.csv",
    "results/api_gpt55_48_plus_visible_sweep_status.csv",
    "results/api_gpt54mini_multi_topology_24_sweep_status.csv",
    "results/api_gpt54mini_inferred_guard_24_sweep_status.csv",
    "results/api_gpt54mini_no_source_ref_instruction_24_sweep_status.csv",
    "results/api_modern_sweep_launch_audit.csv",
    "results/api_gpt54mini_paid_smoke_preflight.csv",
    "results/api_gpt54mini_paid_smoke_payload.json",
    "results/api_gpt54mini_no_source_ref_instruction_preflight.csv",
    "results/api_gpt54mini_no_source_ref_instruction_payload.json",
    "results/research_readiness_report.csv",
    "results/tables/main_results.md",
    "results/tables/injection_overlay_results.md",
    "results/tables/decoy_stress_results.md",
    "results/tables/api_gpt41mini_24_results.md",
    "results/tables/api_gpt41mini_same_action_replay_results.md",
    "results/tables/api_gpt41mini_visibility_gap_audit.md",
    "results/tables/api_gpt41mini_critic_baseline_audit.md",
    "results/tables/api_gpt41mini_source_ref_compliance.md",
    "results/tables/api_gpt41mini_source_ref_ablation_24_results.md",
    "results/tables/api_gpt41mini_repair_oracle_results.md",
    "results/tables/traceguard_repair_oracle_60_results.md",
    "results/tables/api_gpt41mini_paired_tests.md",
    "results/tables/api_gpt41mini_policy_prompt_diagnostics.md",
    "results/tables/traceguard_block_reason_audit.md",
    "results/tables/benchmark_fact_audit.md",
    "results/tables/benchmark_coverage_audit.md",
    "results/tables/bibliography_audit.md",
    "results/tables/claim_boundary_audit.md",
    "results/tables/traceguard_inferred_results.md",
    "results/tables/api_prompt_surface_audit.md",
    "results/tables/api_recovery_prompt_audit.md",
    "results/tables/api_modern_sweep_cost_estimate.md",
    "results/tables/api_gpt55_48_cost_estimate.md",
    "results/tables/api_gpt54mini_120_plus_visible_cost_estimate.md",
    "results/tables/api_gpt55_48_plus_visible_cost_estimate.md",
    "results/tables/api_gpt54mini_no_source_ref_instruction_24_cost_estimate.md",
    "results/tables/api_gpt54mini_120_sweep_status.md",
    "results/tables/api_gpt55_48_sweep_status.md",
    "results/tables/api_gpt54mini_120_plus_visible_sweep_status.md",
    "results/tables/api_gpt55_48_plus_visible_sweep_status.md",
    "results/tables/api_gpt54mini_multi_topology_24_sweep_status.md",
    "results/tables/api_gpt54mini_inferred_guard_24_sweep_status.md",
    "results/tables/api_gpt54mini_no_source_ref_instruction_24_sweep_status.md",
    "results/tables/api_modern_sweep_launch_audit.md",
    "results/tables/api_gpt54mini_paid_smoke_preflight.md",
    "results/tables/api_gpt54mini_no_source_ref_instruction_preflight.md",
    "results/tables/api_paid_smoke_next_step.md",
    "results/tables/research_readiness_report.md",
    "paper/README.md",
    "paper/main.pdf",
    "paper/main.tex",
    "paper/supplement.pdf",
    "paper/supplement.tex",
    "paper/references.bib",
    "paper/related_work_notes.md",
    "paper/colm2026_conference.bst",
    "paper/colm2026_conference.sty",
    "paper/fancyhdr.sty",
    "paper/math_commands.tex",
    "paper/natbib.sty",
]

REPORTED_RAW_TRACES = [
    "single_local",
    "multi_local",
    "dlp",
    "visible_policy",
    "traceguard",
    "traceguard_inferred",
    "multi_local_injection_overlay",
    "dlp_injection_overlay",
    "visible_policy_injection_overlay",
    "traceguard_injection_overlay",
    "traceguard_inferred_injection_overlay",
    "multi_local_decoy_stress",
    "dlp_decoy_stress",
    "visible_policy_decoy_stress",
    "traceguard_decoy_stress",
    "traceguard_inferred_decoy_stress",
    "api_local_gpt41mini_12",
    "api_local_gpt41mini_seed1_12",
    "api_dlp_gpt41mini_12",
    "api_dlp_gpt41mini_seed1_12",
    "api_policy_prompt_gpt41mini_12",
    "api_policy_prompt_gpt41mini_seed1_12",
    "api_traceguard_gpt41mini_12",
    "api_traceguard_gpt41mini_seed1_12",
    "api_local_replay_dlp_gpt41mini_24",
    "api_local_replay_visible_policy_gpt41mini_24",
    "api_local_replay_metadata_critic_gpt41mini_24",
    "api_local_replay_traceguard_gpt41mini_24",
    "api_traceguard_drop_at_sink_replay_gpt41mini_24",
    "api_traceguard_inferred_drop_at_sink_replay_gpt41mini_24",
    "api_traceguard_strict_drop_at_sink_replay_gpt41mini_24",
    "api_traceguard_corrupt_at_sink_replay_gpt41mini_24",
    "api_traceguard_inferred_corrupt_at_sink_replay_gpt41mini_24",
    "api_traceguard_strict_corrupt_at_sink_replay_gpt41mini_24",
    "api_traceguard_drop_intermediate_replay_gpt41mini_24",
    "api_traceguard_inferred_drop_intermediate_replay_gpt41mini_24",
    "api_traceguard_strict_drop_intermediate_replay_gpt41mini_24",
    "api_traceguard_repair_oracle_gpt41mini_12",
    "traceguard_repair_oracle_60",
]

INCLUDE_DIRS = {
    "tracebreak": {".py"},
    "tests": {".py"},
    "paper/tables": {".md", ".tex"},
    "paper/figures": {".svg", ".tex"},
    "scripts": {".py"},
}

TEXT_SUFFIXES = {
    ".bib",
    ".bst",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sty",
    ".svg",
    ".tex",
    ".toml",
    ".txt",
}

SECRET_KEY_RE = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")


def add_reported_traces(files: list[Path]) -> None:
    for stem in REPORTED_RAW_TRACES:
        files.append(ROOT / "results" / "raw_traces" / f"{stem}.jsonl")


def add_directory_files(files: list[Path]) -> None:
    for directory, suffixes in INCLUDE_DIRS.items():
        base = ROOT / directory
        if not base.exists():
            raise FileNotFoundError(f"missing directory: {directory}")
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in suffixes:
                files.append(path)


def collect_files() -> list[Path]:
    files = [ROOT / rel for rel in TOP_LEVEL_FILES]
    add_reported_traces(files)
    add_directory_files(files)

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def archive_name(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def scan_text_file(path: Path) -> None:
    if path.suffix not in TEXT_SUFFIXES:
        return
    text = path.read_text(encoding="utf-8")
    rel = archive_name(path)
    local_home = str(Path.home())
    if local_home and local_home in text:
        raise ValueError(f"local home path found in included file: {rel}")
    if SECRET_KEY_RE.search(text):
        raise ValueError(f"apparent API key found in included file: {rel}")


def build_bundle(out_path: Path, dry_run: bool = False) -> list[str]:
    files = collect_files()
    missing = [archive_name(path) for path in files if not path.exists()]
    if missing:
        raise FileNotFoundError("missing required files:\n" + "\n".join(missing))

    for path in files:
        scan_text_file(path)

    names = sorted(archive_name(path) for path in files)
    if dry_run:
        return names

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(files, key=archive_name):
            zf.write(path, archive_name(path))
    return names


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    try:
        names = build_bundle(out_path=out_path, dry_run=args.dry_run)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("\n".join(names))
    else:
        rel_out = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
        print(f"wrote {rel_out} with {len(names)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
