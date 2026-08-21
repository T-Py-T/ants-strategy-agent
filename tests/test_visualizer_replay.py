"""Regression coverage for retained replay visualization."""

import re
from pathlib import Path

from visualizer.visualize_locally import generate

ROOT = Path(__file__).resolve().parents[1]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_replay_page_references_loadable_visualizer_assets(tmp_path: Path) -> None:
    """Generated pages must resolve their scripts and required PNG assets."""
    replay = ROOT / "results/current-evidence-v1/replay/four-player-final.replay"
    generated = tmp_path / "nested/replay.html"
    generated.parent.mkdir()

    generate(replay.read_text(), str(generated))

    html = generated.read_text()
    script_path = re.search(r'src="([^"]+visualizer\.js)"', html)
    data_path = re.search(r"options\.data_dir = '([^']+)'", html)
    assert script_path is not None
    assert data_path is not None

    assert (generated.parent / script_path.group(1)).resolve().is_file()
    image_dir = (generated.parent / data_path.group(1) / "img").resolve()
    for image_name in (
        "water.png",
        "hill.png",
        "playback.png",
        "fog.png",
        "toolbar.png",
    ):
        assert (image_dir / image_name).read_bytes().startswith(PNG_SIGNATURE)


def test_png_assets_are_exempt_from_text_normalization() -> None:
    """PNG assets must bypass repository text normalization."""
    attributes = (ROOT / ".gitattributes").read_text().splitlines()
    assert "*.png binary" in attributes
