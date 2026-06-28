from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tracebreak.analysis.compute_metrics import read_runs, summarize


COLORS = {
    "api_local": "#4b5563",
    "api_dlp": "#9ca3af",
    "api_policy_prompt": "#d97706",
    "api_traceguard": "#059669",
    "block": "#dc2626",
    "allow": "#16a34a",
    "line": "#374151",
    "text": "#111827",
    "muted": "#6b7280",
}


def write_security_utility_svg(rows: list[dict[str, Any]], out_path: Path) -> None:
    summary = summarize(rows)
    by_condition = {row["condition"]: row for row in summary}
    conditions = ["api_local", "api_dlp", "api_policy_prompt", "api_traceguard"]
    width, height = 760, 360
    plot_x, plot_y = 90, 40
    plot_w, plot_h = 610, 240

    def sx(value: float) -> float:
        return plot_x + (value / 100.0) * plot_w

    def sy(value: float) -> float:
        return plot_y + plot_h - (value / 100.0) * plot_h

    parts = [
        _svg_header(width, height),
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<line x1="{plot_x}" y1="{plot_y + plot_h}" x2="{plot_x + plot_w}" y2="{plot_y + plot_h}" stroke="{COLORS["line"]}" stroke-width="1.5"/>',
        f'<line x1="{plot_x}" y1="{plot_y}" x2="{plot_x}" y2="{plot_y + plot_h}" stroke="{COLORS["line"]}" stroke-width="1.5"/>',
        _text(plot_x + plot_w / 2, height - 28, "Safe false-block rate (%)", 14, "middle"),
        _text(22, plot_y + plot_h / 2, "Risky violation rate (%)", 14, "middle", rotate=-90),
    ]
    for tick in [0, 25, 50, 75, 100]:
        x = sx(tick)
        y = sy(tick)
        parts.append(f'<line x1="{x:.1f}" y1="{plot_y + plot_h}" x2="{x:.1f}" y2="{plot_y + plot_h + 5}" stroke="{COLORS["line"]}"/>')
        parts.append(_text(x, plot_y + plot_h + 22, str(tick), 11, "middle", COLORS["muted"]))
        parts.append(f'<line x1="{plot_x - 5}" y1="{y:.1f}" x2="{plot_x}" y2="{y:.1f}" stroke="{COLORS["line"]}"/>')
        parts.append(_text(plot_x - 12, y + 4, str(tick), 11, "end", COLORS["muted"]))
        if tick not in {0, 100}:
            parts.append(f'<line x1="{plot_x}" y1="{y:.1f}" x2="{plot_x + plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')

    for condition in conditions:
        if condition not in by_condition:
            continue
        row = by_condition[condition]
        x = sx(float(row["safe_false_block_pct"]))
        y = sy(float(row["risky_global_violation_pct"]))
        color = COLORS.get(condition, "#2563eb")
        label = condition.removeprefix("api_").replace("_", " ")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}" stroke="white" stroke-width="2"/>')
        parts.append(_text(x + 12, y - 10, label, 12, "start", COLORS["text"]))
        parts.append(_text(x + 12, y + 7, f'utility {float(row["safe_utility_pct"]):.0f}%', 10, "start", COLORS["muted"]))

    parts.append(_text(width / 2, 24, "Utility/security tradeoff on the 24-task API subset", 16, "middle"))
    parts.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_trace_schematic_svg(out_path: Path) -> None:
    width, height = 860, 300
    steps = [
        ("search", "search docs"),
        ("read", "read doc"),
        ("summarize", "summarize"),
        ("recipient", "find recipient"),
        ("send", "send email"),
    ]
    x0, dx = 90, 165
    y_local, y_guard = 105, 210
    parts = [
        _svg_header(width, height),
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        _text(width / 2, 26, "Local calls allowed; trace-level sink blocked", 17, "middle"),
        _text(28, y_local + 5, "Local", 13, "start", COLORS["muted"]),
        _text(28, y_guard + 5, "TraceGuard", 13, "start", COLORS["muted"]),
    ]
    for idx, (_, label) in enumerate(steps):
        x = x0 + idx * dx
        if idx > 0:
            parts.append(f'<line x1="{x - dx + 46}" y1="{y_local}" x2="{x - 46}" y2="{y_local}" stroke="{COLORS["line"]}" stroke-width="1.5"/>')
            parts.append(f'<line x1="{x - dx + 46}" y1="{y_guard}" x2="{x - 46}" y2="{y_guard}" stroke="{COLORS["line"]}" stroke-width="1.5"/>')
        local_color = COLORS["allow"]
        guard_color = COLORS["block"] if idx == len(steps) - 1 else COLORS["allow"]
        parts.extend(_node(x, y_local, label, local_color, "allow"))
        guard_status = "block" if idx == len(steps) - 1 else "allow"
        parts.extend(_node(x, y_guard, label, guard_color, guard_status))
    parts.append(_text(x0 + 2 * dx, 64, "hidden tag: confidential, AtlasCo, external_share=false", 12, "middle", COLORS["muted"]))
    parts.append(_text(x0 + 4 * dx, y_guard + 55, "reason: internal_data_to_external_recipient", 12, "middle", COLORS["block"]))
    parts.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _node(x: float, y: float, label: str, color: str, status: str) -> list[str]:
    symbol = "check" if status == "allow" else "block"
    return [
        f'<rect x="{x - 52}" y="{y - 28}" width="104" height="56" rx="6" fill="#f9fafb" stroke="{color}" stroke-width="2"/>',
        f'<circle cx="{x - 35}" cy="{y}" r="11" fill="{color}"/>',
        _text(x - 35, y + 4, "OK" if symbol == "check" else "X", 10, "middle", "white"),
        _text(x + 8, y - 2, label, 12, "middle", COLORS["text"]),
        _text(x + 8, y + 14, status, 10, "middle", color),
    ]


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
    )


def _text(
    x: float,
    y: float,
    text: str,
    size: int,
    anchor: str,
    color: str = "#111827",
    rotate: int | None = None,
) -> str:
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
        f'fill="{color}"{transform}>{safe}</text>'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out-dir", default="paper/figures")
    args = parser.parse_args()
    rows = read_runs(args.runs)
    out_dir = Path(args.out_dir)
    write_security_utility_svg(rows, out_dir / "api_security_utility.svg")
    write_trace_schematic_svg(out_dir / "traceguard_schematic.svg")
    print(f"wrote {out_dir / 'api_security_utility.svg'}")
    print(f"wrote {out_dir / 'traceguard_schematic.svg'}")


if __name__ == "__main__":
    main()
