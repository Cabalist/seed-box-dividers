from __future__ import annotations

import pytest

from shoebox_seed_organizer.geometry import OrganizerConfig, build_strips


def test_grid_strip_counts_for_two_by_six() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
    )

    strips = build_strips(config)
    horizontal = [strip for strip in strips if strip.family == "horizontal"]
    vertical = [strip for strip in strips if strip.family == "vertical"]

    assert len(horizontal) == 1
    assert len(vertical) == 5
    assert horizontal[0].slot_positions_mm == (50, 100, 150, 200, 250)
    assert horizontal[0].slots_from == "bottom"
    assert vertical[0].slot_positions_mm == (90,)
    assert vertical[0].slots_from == "top"


def test_one_by_one_grid_has_no_internal_strips() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=1,
        cols=1,
        material_mm=0.8,
    )

    assert build_strips(config) == ()


def test_alternating_seed_box_tabs_on_horizontal_separators() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=4,
        cols=6,
        material_mm=0.8,
    )

    horizontal = [strip for strip in build_strips(config) if strip.family == "horizontal"]

    assert [(tab.start_mm, tab.end_mm) for tab in horizontal[0].tab_segments] == [(75, 225)]
    assert [(tab.start_mm, tab.end_mm) for tab in horizontal[1].tab_segments] == [(0, 75), (225, 300)]
    assert [(tab.start_mm, tab.end_mm) for tab in horizontal[2].tab_segments] == [(75, 225)]


def test_effective_slot_width_uses_material_clearance_and_kerf() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=1.2,
        slot_clearance_mm=0.3,
        kerf_mm=0.1,
    )

    assert config.effective_slot_width_mm == pytest.approx(1.4)


def test_default_kerf_is_tenth_millimeter() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
    )

    assert config.kerf_mm == pytest.approx(0.1)
    assert config.slot_clearance_mm == pytest.approx(0)
    assert config.effective_slot_width_mm == pytest.approx(0.7)


def test_default_tab_radius_is_applied_to_strips() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
    )

    horizontal = next(strip for strip in build_strips(config) if strip.family == "horizontal")

    assert horizontal.tab_radius_mm == 4


def test_rejects_invalid_counts_and_slot_width() -> None:
    with pytest.raises(ValueError, match="rows must be at least 1"):
        OrganizerConfig(
            width_mm=300,
            depth_mm=180,
            height_mm=80,
            rows=0,
            cols=6,
            material_mm=0.8,
        )

    with pytest.raises(ValueError, match="must be greater than zero"):
        OrganizerConfig(
            width_mm=300,
            depth_mm=180,
            height_mm=80,
            rows=2,
            cols=6,
            material_mm=0.8,
            kerf_mm=1.0,
            slot_clearance_mm=0.2,
        )

    with pytest.raises(ValueError, match="tab-radius-mm cannot be negative"):
        OrganizerConfig(
            width_mm=300,
            depth_mm=180,
            height_mm=80,
            rows=2,
            cols=6,
            material_mm=0.8,
            tab_radius_mm=-1,
        )
