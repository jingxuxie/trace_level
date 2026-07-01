"""Run the no-spend TraceBreak paper and artifact release checks."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paper"
DEFAULT_BUNDLE = ROOT / "dist" / "tracebreak_submission_bundle.zip"

LATEX_PROBLEM_RE = re.compile(
    r"(^!|LaTeX Error|Undefined control sequence|Citation .* undefined|"
    r"Reference .* undefined|There were undefined|Rerun to get cross-references)"
)

REQUIRED_BUNDLE_ENTRIES = {
    "README.md",
    "REPRODUCIBILITY.md",
    "SUBMISSION_CHECKLIST.md",
    "paper/main.pdf",
    "paper/related_work_notes.md",
    "paper/supplement.pdf",
    "results/tables/research_readiness_report.md",
    "results/tables/api_paid_smoke_next_step.md",
    "results/raw_traces/traceguard_inferred_injection_overlay.jsonl",
    "results/raw_traces/traceguard_inferred_decoy_stress.jsonl",
    "scripts/run_release_checks.py",
    "tests/test_release_checks.py",
}

FORBIDDEN_BUNDLE_PARTS = {
    ".agents/",
    ".codex/",
    ".git/",
    "__pycache__/",
    "results/api_cache/",
    "paper/main.log",
    "paper/supplement.log",
}


def run_command(args: list[str], *, cwd: Path = ROOT) -> None:
    print("+ " + " ".join(args), flush=True)
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        raise subprocess.CalledProcessError(
            completed.returncode,
            args,
            output=completed.stdout,
            stderr=completed.stderr,
        )

    stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    stderr_lines = [line for line in completed.stderr.splitlines() if line.strip()]
    if stdout_lines:
        print(stdout_lines[-1])
    if stderr_lines:
        print(stderr_lines[-1], file=sys.stderr)


def find_latex_log_problems(log_paths: list[Path]) -> list[str]:
    problems: list[str] = []
    for path in log_paths:
        if not path.exists():
            problems.append(f"{path.name}:missing")
            continue
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            start=1,
        ):
            if LATEX_PROBLEM_RE.search(line):
                problems.append(f"{path.name}:{line_number}:{line.strip()}")
    return problems


def pdf_page_count(path: Path) -> int:
    completed = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
    if match is None:
        raise ValueError(f"could not parse page count for {path}")
    return int(match.group(1))


def verify_pdf_pages() -> None:
    expected = {
        PAPER_DIR / "main.pdf": 7,
        PAPER_DIR / "supplement.pdf": 5,
    }
    for path, pages in expected.items():
        actual = pdf_page_count(path)
        if actual != pages:
            raise AssertionError(f"{path.relative_to(ROOT)} has {actual} pages, expected {pages}")
        print(f"ok - {path.relative_to(ROOT)} has {pages} pages")


def verify_latex_logs() -> None:
    problems = find_latex_log_problems([PAPER_DIR / "main.log", PAPER_DIR / "supplement.log"])
    if problems:
        raise AssertionError("LaTeX log problems:\n" + "\n".join(problems))
    print("ok - LaTeX logs have no hard errors or unresolved refs/citations")


def inspect_bundle(path: Path = DEFAULT_BUNDLE) -> tuple[list[str], list[str]]:
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
    missing = sorted(REQUIRED_BUNDLE_ENTRIES - names)
    forbidden = sorted(
        name
        for name in names
        if any(part in name for part in FORBIDDEN_BUNDLE_PARTS)
    )
    return missing, forbidden


def verify_bundle(path: Path = DEFAULT_BUNDLE) -> None:
    missing, forbidden = inspect_bundle(path)
    failures = []
    if missing:
        failures.append("missing required bundle entries:\n" + "\n".join(missing))
    if forbidden:
        failures.append("forbidden bundle entries:\n" + "\n".join(forbidden))
    if failures:
        raise AssertionError("\n\n".join(failures))
    print(f"ok - {path.relative_to(ROOT)} contains required release artifacts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-latex", action="store_true")
    parser.add_argument("--skip-bundle", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not args.skip_tests:
            run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
            run_command([sys.executable, "-m", "compileall", "-q", "tracebreak", "tests"])
        if not args.skip_latex:
            run_command(
                [
                    "latexmk",
                    "-g",
                    "-pdf",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "main.tex",
                    "supplement.tex",
                ],
                cwd=PAPER_DIR,
            )
            verify_latex_logs()
            verify_pdf_pages()
        run_command([sys.executable, "-m", "tracebreak.analysis.verify_claims"])
        if not args.skip_bundle:
            run_command([sys.executable, "scripts/build_submission_bundle.py"])
            verify_bundle(DEFAULT_BUNDLE)
    except Exception as exc:
        print(f"release checks failed: {exc}", file=sys.stderr)
        return 1
    print("release checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
