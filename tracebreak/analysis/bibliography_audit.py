from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any


CITE_RE = re.compile(r"\\(?:cite|citep|citet|citealp|citealt|citeauthor|citeyear)\*?(?:\[[^\]]*\])*{([^}]+)}")
BIB_KEY_RE = re.compile(r"@\w+\s*{\s*([^,\s]+)\s*,", re.MULTILINE)
BBL_KEY_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?{([^}]+)}")
EPRINT_RE = re.compile(r"eprint\s*=\s*[{]([^}]+)[}]", re.IGNORECASE)
UNDEFINED_RE = re.compile(r"(undefined citations?|Citation `[^']+' .*undefined|I didn't find a database entry)", re.IGNORECASE)
STALE_DENYLIST = {"wang2026safeskillscollide"}


def build_bibliography_audit_rows(paper_dir: str | Path = "paper") -> list[dict[str, Any]]:
    paper = Path(paper_dir)
    tex_paths = [paper / "main.tex", paper / "supplement.tex"]
    bib_path = paper / "references.bib"
    bbl_path = paper / "main.bbl"
    log_path = paper / "main.log"
    blg_path = paper / "main.blg"

    cited_keys = sorted(
        {
            key
            for path in tex_paths
            for key in _extract_cited_keys(path.read_text(encoding="utf-8"))
        }
    )
    bib_text = bib_path.read_text(encoding="utf-8")
    bib_keys = _extract_bib_keys(bib_text)
    bbl_keys = (
        sorted(set(BBL_KEY_RE.findall(bbl_path.read_text(encoding="utf-8"))))
        if bbl_path.exists()
        else []
    )
    warning_sources = []
    for path in [log_path, blg_path]:
        if not path.exists():
            continue
        warnings = _undefined_warnings(path.read_text(encoding="utf-8", errors="replace"))
        warning_sources.extend(f"{path.name}:{warning}" for warning in warnings)

    cited_set = set(cited_keys)
    bib_set = set(bib_keys)
    bbl_set = set(bbl_keys)
    duplicate_keys = sorted(_duplicates(bib_keys))
    undefined_keys = sorted(cited_set - bib_set)
    stale_bbl_keys = sorted(bbl_set - cited_set)
    missing_bbl_keys = sorted(cited_set - bbl_set)
    stale_denied_keys = sorted((cited_set | bib_set | bbl_set) & STALE_DENYLIST)
    invalid_arxiv = _invalid_arxiv_entries(bib_text)
    pass_value = not any(
        [
            duplicate_keys,
            undefined_keys,
            stale_bbl_keys,
            missing_bbl_keys,
            stale_denied_keys,
            invalid_arxiv,
            warning_sources,
        ]
    )

    return [
        {
            "tex_files": ";".join(str(path) for path in tex_paths),
            "bib_file": str(bib_path),
            "bbl_file": str(bbl_path),
            "cited_keys": len(cited_keys),
            "bib_entries": len(bib_set),
            "bbl_entries": len(bbl_set),
            "undefined_keys": ";".join(undefined_keys),
            "duplicate_bib_keys": ";".join(duplicate_keys),
            "stale_bbl_keys": ";".join(stale_bbl_keys),
            "missing_bbl_keys": ";".join(missing_bbl_keys),
            "stale_denied_keys": ";".join(stale_denied_keys),
            "invalid_arxiv_entries": ";".join(invalid_arxiv),
            "undefined_warning_sources": ";".join(warning_sources),
            "pass": pass_value,
        }
    ]


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
    lines = [
        "# Bibliography Integrity Audit",
        "",
        "No API calls are used. This audit checks that the TeX citation keys, "
        "BibTeX database, generated bibliography, and LaTeX/BibTeX logs agree. "
        "It also catches malformed arXiv identifiers and removed unsupported "
        "citation keys.",
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _extract_cited_keys(tex: str) -> list[str]:
    keys: list[str] = []
    for match in CITE_RE.finditer(_strip_tex_comments(tex)):
        keys.extend(key.strip() for key in match.group(1).split(",") if key.strip())
    return sorted(set(keys))


def _extract_bib_keys(bib_text: str) -> list[str]:
    return [key.strip() for key in BIB_KEY_RE.findall(bib_text)]


def _strip_tex_comments(tex: str) -> str:
    lines = []
    for line in tex.splitlines():
        escaped = False
        chars = []
        for char in line:
            if char == "%" and not escaped:
                break
            chars.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        lines.append("".join(chars))
    return "\n".join(lines)


def _undefined_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    for line in text.splitlines():
        if UNDEFINED_RE.search(line):
            warnings.append(" ".join(line.strip().split()))
    return warnings


def _duplicates(items: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return sorted(duplicates)


def _invalid_arxiv_entries(bib_text: str) -> list[str]:
    invalid: list[str] = []
    for entry in re.split(r"\n@", "\n" + bib_text):
        if not entry.strip():
            continue
        entry_text = entry if entry.startswith("@") else "@" + entry
        key_match = BIB_KEY_RE.search(entry_text)
        if not key_match:
            continue
        key = key_match.group(1).strip()
        if "archivePrefix = {arXiv}" not in entry_text and "archivePrefix={arXiv}" not in entry_text:
            continue
        eprint_match = EPRINT_RE.search(entry_text)
        if not eprint_match or not re.fullmatch(r"\d{4}\.\d{4,5}", eprint_match.group(1).strip()):
            invalid.append(key)
    return sorted(invalid)


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "cited": str(row["cited_keys"]),
        "bib": str(row["bib_entries"]),
        "bbl": str(row["bbl_entries"]),
        "undefined": row["undefined_keys"] or "none",
        "duplicates": row["duplicate_bib_keys"] or "none",
        "stale bbl": row["stale_bbl_keys"] or "none",
        "missing bbl": row["missing_bbl_keys"] or "none",
        "invalid arXiv": row["invalid_arxiv_entries"] or "none",
        "denied keys": row["stale_denied_keys"] or "none",
        "log warnings": row["undefined_warning_sources"] or "none",
        "pass": "yes" if row["pass"] else "no",
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
    parser.add_argument("--paper-dir", default="paper")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = build_bibliography_audit_rows(args.paper_dir)
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
