from __future__ import annotations

from xml.etree import ElementTree

from shoebox_seed_organizer.geometry import OrganizerConfig, build_strips
from shoebox_seed_organizer.svg import generate_svg, strip_cut_path, strip_score_paths

SVG_NS = "{http://www.w3.org/2000/svg}"


def test_svg_groups_cut_and_score_paths_by_panel() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
    )

    svg = generate_svg(config)
    root = ElementTree.fromstring(svg)
    groups = {group.attrib["id"]: group for group in root.findall(f"{SVG_NS}g")}
    horizontal_panel = groups["panel-horizontal-1"]
    horizontal_paths = horizontal_panel.findall(f"{SVG_NS}path")

    assert "cut" not in groups
    assert "score" not in groups
    assert horizontal_panel.attrib["transform"] == "translate(10 10)"
    assert [path.attrib["id"] for path in horizontal_paths] == [
        "cut-horizontal-1",
        "score-horizontal-1-1",
        "score-horizontal-1-2",
    ]
    assert [path.attrib["data-operation"] for path in horizontal_paths] == ["cut", "score", "score"]
    assert all("transform" not in path.attrib for path in horizontal_paths)
    assert 'stroke="#ff0000"' in svg
    assert 'stroke="#0066ff"' in svg
    assert "2 by 6 compartment divider insert" in svg


def test_horizontal_cut_path_includes_middle_half_tab_and_bottom_slots() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
    )
    horizontal = next(strip for strip in build_strips(config) if strip.family == "horizontal")

    cut_path = strip_cut_path(horizontal)

    assert "L 90 4 A 4 4 0 0 1 94 0 L 236 0" in cut_path
    assert "A 4 4 0 0 1 240 4 L 240 12" in cut_path
    assert "L 265.35 52" in cut_path
    assert "L 264.65 92" in cut_path


def test_zero_tab_radius_keeps_square_tab_corners() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
        tab_radius_mm=0,
    )
    horizontal = next(strip for strip in build_strips(config) if strip.family == "horizontal")

    cut_path = strip_cut_path(horizontal)

    assert "L 90 0 L 240 0" in cut_path
    assert " A " not in cut_path


def test_vertical_cut_path_includes_top_slots() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
    )
    vertical = next(strip for strip in build_strips(config) if strip.family == "vertical")

    cut_path = strip_cut_path(vertical)

    assert "L 104.65 12 L 104.65 52" in cut_path
    assert "L 105.35 52 L 105.35 12" in cut_path


def test_score_paths_mark_only_flap_fold_lines() -> None:
    config = OrganizerConfig(
        width_mm=300,
        depth_mm=180,
        height_mm=80,
        rows=2,
        cols=6,
        material_mm=0.8,
    )
    horizontal = next(strip for strip in build_strips(config) if strip.family == "horizontal")

    assert strip_score_paths(horizontal) == ("M 15 12 L 15 92", "M 315 12 L 315 92")
