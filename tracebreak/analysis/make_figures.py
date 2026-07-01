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


SECURITY_UTILITY_CONDITIONS = [
    "api_dlp",
    "api_local",
    "api_policy_prompt",
    "api_traceguard",
]


def security_utility_points(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = summarize(rows)
    by_condition = {row["condition"]: row for row in summary}
    points: list[dict[str, Any]] = []
    for condition in SECURITY_UTILITY_CONDITIONS:
        if condition not in by_condition:
            continue
        row = by_condition[condition]
        points.append(
            {
                "condition": condition,
                "label": condition.removeprefix("api_").replace("_", " "),
                "safe_utility_pct": float(row["safe_utility_pct"]),
                "risky_violation_pct": float(row["risky_global_violation_pct"]),
            }
        )
    return points


def write_security_utility_svg(rows: list[dict[str, Any]], out_path: Path) -> None:
    points = security_utility_points(rows)
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
        _text(plot_x + plot_w / 2, height - 28, "Safe utility (%)", 14, "middle"),
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

    for index, point in enumerate(points):
        x = sx(float(point["safe_utility_pct"]))
        y = sy(float(point["risky_violation_pct"]))
        condition = point["condition"]
        color = COLORS.get(condition, "#2563eb")
        label = "local / DLP" if condition == "api_local" else point["label"]
        label_dx, label_dy = _svg_label_offset(point, index)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}" stroke="white" stroke-width="2"/>')
        if condition == "api_dlp":
            continue
        parts.append(_text(x + label_dx, y + label_dy, label, 12, "start", COLORS["text"]))
        parts.append(_text(x + label_dx, y + label_dy + 16, f'risk {float(point["risky_violation_pct"]):.0f}%', 10, "start", COLORS["muted"]))

    parts.append(_text(width / 2, 24, "Security-utility frontier on the 24-task API subset", 16, "middle"))
    parts.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_security_utility_tikz(rows: list[dict[str, Any]], out_path: Path) -> None:
    points = security_utility_points(rows)

    def coord(value: float) -> float:
        return value / 100.0

    lines = [
        "\\begin{figure}[h]",
        "\\centering",
        "\\small",
        "\\begin{tikzpicture}[x=7.0cm,y=3.0cm,every node/.style={font=\\scriptsize}]",
        "  \\draw[->, gray!70] (0,0) -- (1.07,0) node[right] {Safe utility (\\%)};",
        "  \\draw[->, gray!70] (0,0) -- (0,1.08) node[above] {Risky violation (\\%)};",
    ]
    for tick in [0, 25, 50, 75, 100]:
        x = coord(tick)
        y = coord(tick)
        lines.append(
            f"  \\draw[gray!45] ({x:.2f},0) -- ({x:.2f},-0.025) node[below] {{{tick}}};"
        )
        lines.append(
            f"  \\draw[gray!45] (0,{y:.2f}) -- (-0.025,{y:.2f}) node[left] {{{tick}}};"
        )
        if tick not in {0, 100}:
            lines.append(f"  \\draw[gray!15] (0,{y:.2f}) -- (1,{y:.2f});")
    lines.append("  \\node[anchor=south east, text=gray!70] at (1,0.02) {desired};")
    for index, point in enumerate(points):
        condition = point["condition"]
        label = "local / DLP" if condition == "api_local" else _tex_escape(point["label"])
        color = _tikz_color(condition)
        x = coord(float(point["safe_utility_pct"]))
        y = coord(float(point["risky_violation_pct"]))
        anchor, dx, dy = _tikz_label_offset(point, index)
        lines.append(f"  \\filldraw[{color}, draw=white, line width=0.7pt] ({x:.3f},{y:.3f}) circle (2.4pt);")
        if condition == "api_dlp":
            continue
        lines.append(
            f"  \\node[anchor={anchor}, align=left] at ({x + dx:.3f},{y + dy:.3f})"
            f" {{{label}\\\\{{\\color{{gray}}risk {float(point['risky_violation_pct']):.0f}\\%}}}};"
        )
    lines.extend(
        [
            "\\end{tikzpicture}",
            "\\caption{Security-utility frontier on the 24-task \\texttt{gpt-4.1-mini} API subset. "
            "The desired region is high safe-control utility and low risky-violation rate. "
            "Local guards and DLP preserve utility but violate every risky task; TraceGuard preserves utility while eliminating risky violations.}",
            "\\label{fig:api-security-utility}",
            "\\end{figure}",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _svg_label_offset(point: dict[str, Any], index: int) -> tuple[float, float]:
    if point["condition"] == "api_local":
        return -112, 18
    if point["condition"] == "api_dlp":
        return 0, 0
    if point["condition"] == "api_traceguard":
        return -112, -24
    return 12, -12


def _tikz_label_offset(point: dict[str, Any], index: int) -> tuple[str, float, float]:
    if point["condition"] == "api_local":
        return "east", -0.018, -0.010
    if point["condition"] == "api_dlp":
        return "east", 0.0, 0.0
    if point["condition"] == "api_traceguard":
        return "south east", -0.018, 0.040
    return "west", 0.020, 0.000


def _tikz_color(condition: str) -> str:
    return {
        "api_local": "black!60",
        "api_dlp": "black!35",
        "api_policy_prompt": "orange!80!black",
        "api_traceguard": "green!55!black",
    }.get(condition, "blue!70!black")


def _tex_escape(text: str) -> str:
    return text.replace("_", "\\_")


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
    write_security_utility_tikz(rows, out_dir / "api_security_utility.tex")
    write_trace_schematic_svg(out_dir / "traceguard_schematic.svg")
    print(f"wrote {out_dir / 'api_security_utility.svg'}")
    print(f"wrote {out_dir / 'api_security_utility.tex'}")
    print(f"wrote {out_dir / 'traceguard_schematic.svg'}")


if __name__ == "__main__":
    main()
