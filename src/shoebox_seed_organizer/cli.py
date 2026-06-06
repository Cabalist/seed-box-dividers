"""Command-line interface for the shoebox seed organizer generator."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from . import __version__
from .geometry import OrganizerConfig
from .svg import write_svg

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shoebox-seed-organizer",
        description="Generate SVG laser-cut divider inserts for a shoebox seed organizer.",
    )
    parser.add_argument("--width-mm", type=_positive_float, required=True)
    parser.add_argument("--depth-mm", type=_positive_float, required=True)
    parser.add_argument("--height-mm", type=_positive_float, required=True)
    parser.add_argument("--rows", type=_positive_int, required=True)
    parser.add_argument("--cols", type=_positive_int, required=True)
    parser.add_argument("--material-mm", type=_positive_float, required=True)
    parser.add_argument("--kerf-mm", type=_non_negative_float, default=0.1)
    parser.add_argument("--slot-clearance-mm", type=_non_negative_float, default=0.0)
    parser.add_argument("--flap-mm", type=_non_negative_float, default=15.0)
    parser.add_argument("--tab-height-mm", type=_positive_float, default=12.0)
    parser.add_argument("--tab-radius-mm", type=_non_negative_float, default=4.0)
    parser.add_argument("--output", required=True, help="Path to write the SVG output.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = OrganizerConfig(
            width_mm=args.width_mm,
            depth_mm=args.depth_mm,
            height_mm=args.height_mm,
            rows=args.rows,
            cols=args.cols,
            material_mm=args.material_mm,
            kerf_mm=args.kerf_mm,
            slot_clearance_mm=args.slot_clearance_mm,
            flap_mm=args.flap_mm,
            tab_height_mm=args.tab_height_mm,
            tab_radius_mm=args.tab_radius_mm,
        )
        write_svg(args.output, config)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("cannot be negative")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
