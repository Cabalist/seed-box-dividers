"""SVG output for shoebox divider cut patterns."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .geometry import Layout, OrganizerConfig, Strip, build_layout

if TYPE_CHECKING:
    from .geometry import PlacedStrip

CUT_STROKE = "#ff0000"
SCORE_STROKE = "#0066ff"
LINE_WIDTH_MM = 0.2


def generate_svg(config: OrganizerConfig) -> str:
    """Generate a complete SVG document for the requested divider layout."""

    return layout_to_svg(build_layout(config), config)


def write_svg(path: str | Path, config: OrganizerConfig) -> None:
    """Write the generated SVG to disk."""

    output_path = Path(path)
    output_path.write_text(generate_svg(config), encoding="utf-8")


def layout_to_svg(layout: Layout, config: OrganizerConfig) -> str:
    """Render a precomputed layout as SVG."""

    panel_groups = [_panel_group(placed) for placed in layout.strips]
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{_num(layout.width_mm)}mm" height="{_num(layout.height_mm)}mm" '
                f'viewBox="0 0 {_num(layout.width_mm)} {_num(layout.height_mm)}">'
            ),
            "  <title>Shoebox seed organizer cut pattern</title>",
            (
                "  <desc>"
                f"{config.rows} by {config.cols} compartment divider insert; "
                "red paths are cuts and blue paths are fold scores."
                "</desc>"
            ),
            *panel_groups,
            "</svg>",
            "",
        ]
    )


def _panel_group(placed: PlacedStrip) -> str:
    strip = placed.strip
    lines = [
        f'  <g id="panel-{strip.name}" transform="{_translate(placed.x_mm, placed.y_mm)}">',
        "    "
        + _element(
            "path",
            {
                "id": f"cut-{strip.name}",
                "data-operation": "cut",
                "fill": "none",
                "stroke": CUT_STROKE,
                "stroke-width": _num(LINE_WIDTH_MM),
                "stroke-linecap": "square",
                "stroke-linejoin": "miter",
                "d": strip_cut_path(strip),
            },
        ),
    ]
    for score_index, score_path in enumerate(strip_score_paths(strip), start=1):
        lines.append(
            "    "
            + _element(
                "path",
                {
                    "id": f"score-{strip.name}-{score_index}",
                    "data-operation": "score",
                    "fill": "none",
                    "stroke": SCORE_STROKE,
                    "stroke-width": _num(LINE_WIDTH_MM),
                    "stroke-linecap": "square",
                    "d": score_path,
                },
            )
        )
    lines.append("  </g>")
    return "\n".join(lines)


def strip_cut_path(strip: Strip) -> str:
    """Return a closed SVG path for the strip outline, tabs, and edge slots."""

    top_y = strip.tab_height_mm
    bottom_y = strip.tab_height_mm + strip.height_mm
    right_x = strip.total_width_mm
    commands = [f"M {_num(0)} {_num(top_y)}"]

    commands.extend(_top_edge_commands(strip))
    commands.append(f"L {_num(right_x)} {_num(bottom_y)}")
    commands.extend(_bottom_edge_commands(strip))
    commands.append("Z")
    return " ".join(commands)


def strip_score_paths(strip: Strip) -> tuple[str, ...]:
    """Return fold/score paths for the strip's outer end flaps."""

    if strip.flap_mm <= 0:
        return ()

    top_y = strip.tab_height_mm
    bottom_y = strip.tab_height_mm + strip.height_mm
    left_score_x = strip.flap_mm
    right_score_x = strip.flap_mm + strip.length_mm
    return (
        _move_line(left_score_x, top_y, left_score_x, bottom_y),
        _move_line(right_score_x, top_y, right_score_x, bottom_y),
    )


def _top_edge_commands(strip: Strip) -> list[str]:
    top_y = strip.tab_height_mm
    if strip.slots_from == "top":
        return _top_slot_commands(strip)
    if strip.tab_segments:
        return _tab_commands(strip)
    return [f"L {_num(strip.total_width_mm)} {_num(top_y)}"]


def _bottom_edge_commands(strip: Strip) -> list[str]:
    bottom_y = strip.tab_height_mm + strip.height_mm
    if strip.slots_from != "bottom":
        return [f"L {_num(0)} {_num(bottom_y)}"]

    commands: list[str] = []
    half_width = strip.slot_width_mm / 2
    for position in sorted(strip.slot_positions_mm, reverse=True):
        left_x = strip.flap_mm + position - half_width
        right_x = strip.flap_mm + position + half_width
        notch_top_y = bottom_y - strip.slot_depth_mm
        commands.extend(
            [
                f"L {_num(right_x)} {_num(bottom_y)}",
                f"L {_num(right_x)} {_num(notch_top_y)}",
                f"L {_num(left_x)} {_num(notch_top_y)}",
                f"L {_num(left_x)} {_num(bottom_y)}",
            ]
        )

    commands.append(f"L {_num(0)} {_num(bottom_y)}")
    return commands


def _top_slot_commands(strip: Strip) -> list[str]:
    commands: list[str] = []
    top_y = strip.tab_height_mm
    half_width = strip.slot_width_mm / 2
    for position in strip.slot_positions_mm:
        left_x = strip.flap_mm + position - half_width
        right_x = strip.flap_mm + position + half_width
        notch_bottom_y = top_y + strip.slot_depth_mm
        commands.extend(
            [
                f"L {_num(left_x)} {_num(top_y)}",
                f"L {_num(left_x)} {_num(notch_bottom_y)}",
                f"L {_num(right_x)} {_num(notch_bottom_y)}",
                f"L {_num(right_x)} {_num(top_y)}",
            ]
        )

    commands.append(f"L {_num(strip.total_width_mm)} {_num(top_y)}")
    return commands


def _tab_commands(strip: Strip) -> list[str]:
    commands: list[str] = []
    top_y = strip.tab_height_mm
    for tab in strip.tab_segments:
        start_x = strip.flap_mm + tab.start_mm
        end_x = strip.flap_mm + tab.end_mm
        radius = min(strip.tab_radius_mm, strip.tab_height_mm, (end_x - start_x) / 2)
        if radius <= 0:
            commands.extend(
                [
                    f"L {_num(start_x)} {_num(top_y)}",
                    f"L {_num(start_x)} {_num(0)}",
                    f"L {_num(end_x)} {_num(0)}",
                    f"L {_num(end_x)} {_num(top_y)}",
                ]
            )
            continue

        commands.extend(
            [
                f"L {_num(start_x)} {_num(top_y)}",
                f"L {_num(start_x)} {_num(radius)}",
                (f"A {_num(radius)} {_num(radius)} 0 0 1 {_num(start_x + radius)} {_num(0)}"),
                f"L {_num(end_x - radius)} {_num(0)}",
                (f"A {_num(radius)} {_num(radius)} 0 0 1 {_num(end_x)} {_num(radius)}"),
                f"L {_num(end_x)} {_num(top_y)}",
            ]
        )

    commands.append(f"L {_num(strip.total_width_mm)} {_num(top_y)}")
    return commands


def _move_line(x1: float, y1: float, x2: float, y2: float) -> str:
    return f"M {_num(x1)} {_num(y1)} L {_num(x2)} {_num(y2)}"


def _translate(x_mm: float, y_mm: float) -> str:
    return f"translate({_num(x_mm)} {_num(y_mm)})"


def _element(tag: str, attributes: dict[str, str]) -> str:
    rendered = " ".join(f'{name}="{_escape(value)}"' for name, value in attributes.items())
    return f"<{tag} {rendered}/>"


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _num(value: float) -> str:
    rounded = round(value, 6)
    if rounded == 0:
        return "0"
    return f"{rounded:.6f}".rstrip("0").rstrip(".")
