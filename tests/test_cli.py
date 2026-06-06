from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from shoebox_seed_organizer.cli import main

if TYPE_CHECKING:
    from pathlib import Path


def test_cli_writes_svg_file(tmp_path: Path) -> None:
    output_path = tmp_path / "organizer.svg"

    result = main(
        [
            "--width-mm",
            "300",
            "--depth-mm",
            "180",
            "--height-mm",
            "80",
            "--rows",
            "2",
            "--cols",
            "6",
            "--material-mm",
            "0.8",
            "--tab-radius-mm",
            "6",
            "--output",
            str(output_path),
        ]
    )

    assert result == 0
    assert output_path.exists()
    assert "<svg" in output_path.read_text(encoding="utf-8")


def test_cli_rejects_invalid_effective_slot_width(tmp_path: Path) -> None:
    output_path = tmp_path / "organizer.svg"

    with redirect_stderr(StringIO()), pytest.raises(SystemExit) as exit_context:
        main(
            [
                "--width-mm",
                "300",
                "--depth-mm",
                "180",
                "--height-mm",
                "80",
                "--rows",
                "2",
                "--cols",
                "6",
                "--material-mm",
                "0.8",
                "--kerf-mm",
                "1.0",
                "--output",
                str(output_path),
            ]
        )

    assert exit_context.value.code == 2
