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
    "results/api_gpt41mini_24_metrics.csv",
    "results/tables/main_results.md",
    "results/tables/api_gpt41mini_24_results.md",
    "paper/README.md",
    "paper/main.pdf",
    "paper/main.tex",
    "paper/supplement.pdf",
    "paper/supplement.tex",
    "paper/references.bib",
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
    "api_local_gpt41mini_12",
    "api_local_gpt41mini_seed1_12",
    "api_dlp_gpt41mini_12",
    "api_dlp_gpt41mini_seed1_12",
    "api_policy_prompt_gpt41mini_12",
    "api_policy_prompt_gpt41mini_seed1_12",
    "api_traceguard_gpt41mini_12",
    "api_traceguard_gpt41mini_seed1_12",
]

INCLUDE_DIRS = {
    "tracebreak": {".py"},
    "tests": {".py"},
    "paper/tables": {".md", ".tex"},
    "paper/figures": {".svg"},
    "scripts": {".py"},
}

TEXT_SUFFIXES = {
    ".bib",
    ".bst",
    ".csv",
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
