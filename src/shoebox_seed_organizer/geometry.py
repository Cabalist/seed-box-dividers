"""Geometry for shoebox divider cut patterns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SlotEdge = Literal["top", "bottom", "none"]
StripFamily = Literal["horizontal", "vertical"]


@dataclass(frozen=True)
class OrganizerConfig:
    """Validated user inputs for a shoebox divider layout."""

    width_mm: float
    depth_mm: float
    height_mm: float
    rows: int
    cols: int
    material_mm: float
    kerf_mm: float = 0.1
    slot_clearance_mm: float = 0.0
    flap_mm: float = 15.0
    tab_height_mm: float = 12.0
    tab_radius_mm: float = 4.0
    layout_gap_mm: float = 10.0

    def __post_init__(self) -> None:
        positive_values = {
            "width-mm": self.width_mm,
            "depth-mm": self.depth_mm,
            "height-mm": self.height_mm,
            "material-mm": self.material_mm,
            "tab-height-mm": self.tab_height_mm,
            "layout-gap-mm": self.layout_gap_mm,
        }
        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.rows < 1:
            raise ValueError("rows must be at least 1")
        if self.cols < 1:
            raise ValueError("cols must be at least 1")
        if self.kerf_mm < 0:
            raise ValueError("kerf-mm cannot be negative")
        if self.slot_clearance_mm < 0:
            raise ValueError("slot-clearance-mm cannot be negative")
        if self.flap_mm < 0:
            raise ValueError("flap-mm cannot be negative")
        if self.tab_radius_mm < 0:
            raise ValueError("tab-radius-mm cannot be negative")
        if self.effective_slot_width_mm <= 0:
            raise ValueError("material-mm + slot-clearance-mm - kerf-mm must be greater than zero")

    @property
    def effective_slot_width_mm(self) -> float:
        return self.material_mm + self.slot_clearance_mm - self.kerf_mm

    @property
    def slot_depth_mm(self) -> float:
        return self.height_mm / 2


@dataclass(frozen=True)
class TabSegment:
    """A raised tab span measured along the strip body, excluding flaps."""

    start_mm: float
    end_mm: float


@dataclass(frozen=True)
class Strip:
    """A single flat divider strip before placement on the SVG sheet."""

    name: str
    family: StripFamily
    index: int
    length_mm: float
    height_mm: float
    flap_mm: float
    tab_height_mm: float
    tab_radius_mm: float
    tab_segments: tuple[TabSegment, ...]
    slot_positions_mm: tuple[float, ...]
    slot_width_mm: float
    slot_depth_mm: float
    slots_from: SlotEdge

    @property
    def total_width_mm(self) -> float:
        return self.length_mm + (2 * self.flap_mm)

    @property
    def total_height_mm(self) -> float:
        return self.height_mm + self.tab_height_mm


@dataclass(frozen=True)
class PlacedStrip:
    """A strip with an absolute placement on the output SVG sheet."""

    strip: Strip
    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class Layout:
    """A complete laid-out cut sheet."""

    strips: tuple[PlacedStrip, ...]
    width_mm: float
    height_mm: float


def horizontal_tab_segments(length_mm: float, separator_index: int) -> tuple[TabSegment, ...]:
    """Return the alternating seed-box tab pattern for one horizontal separator."""

    quarter = length_mm / 4
    if separator_index % 2 == 1:
        return (TabSegment(quarter, 3 * quarter),)
    return (TabSegment(0, quarter), TabSegment(3 * quarter, length_mm))


def build_strips(config: OrganizerConfig) -> tuple[Strip, ...]:
    """Build all divider strips needed for the requested compartment grid."""

    strips: list[Strip] = []
    horizontal_slot_positions = tuple(config.width_mm * index / config.cols for index in range(1, config.cols))
    vertical_slot_positions = tuple(config.depth_mm * index / config.rows for index in range(1, config.rows))

    for index in range(1, config.rows):
        strips.append(
            Strip(
                name=f"horizontal-{index}",
                family="horizontal",
                index=index,
                length_mm=config.width_mm,
                height_mm=config.height_mm,
                flap_mm=config.flap_mm,
                tab_height_mm=config.tab_height_mm,
                tab_radius_mm=config.tab_radius_mm,
                tab_segments=horizontal_tab_segments(config.width_mm, index),
                slot_positions_mm=horizontal_slot_positions,
                slot_width_mm=config.effective_slot_width_mm,
                slot_depth_mm=config.slot_depth_mm,
                slots_from="bottom",
            )
        )

    for index in range(1, config.cols):
        strips.append(
            Strip(
                name=f"vertical-{index}",
                family="vertical",
                index=index,
                length_mm=config.depth_mm,
                height_mm=config.height_mm,
                flap_mm=config.flap_mm,
                tab_height_mm=config.tab_height_mm,
                tab_radius_mm=config.tab_radius_mm,
                tab_segments=(),
                slot_positions_mm=vertical_slot_positions,
                slot_width_mm=config.effective_slot_width_mm,
                slot_depth_mm=config.slot_depth_mm,
                slots_from="top",
            )
        )

    return tuple(strips)


def layout_strips(strips: tuple[Strip, ...], *, margin_mm: float = 10.0, gap_mm: float = 10.0) -> Layout:
    """Stack strips vertically on an SVG sheet."""

    if not strips:
        return Layout(strips=(), width_mm=2 * margin_mm, height_mm=2 * margin_mm)

    placed: list[PlacedStrip] = []
    y_mm = margin_mm
    for strip in strips:
        placed.append(PlacedStrip(strip=strip, x_mm=margin_mm, y_mm=y_mm))
        y_mm += strip.total_height_mm + gap_mm

    width_mm = max(strip.total_width_mm for strip in strips) + (2 * margin_mm)
    height_mm = y_mm - gap_mm + margin_mm
    return Layout(strips=tuple(placed), width_mm=width_mm, height_mm=height_mm)


def build_layout(config: OrganizerConfig) -> Layout:
    """Build and place all cuttable strips for a config."""

    return layout_strips(build_strips(config), margin_mm=config.layout_gap_mm, gap_mm=config.layout_gap_mm)
