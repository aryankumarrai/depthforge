from pathlib import Path

import numpy as np

from depthforge.io_utils import write_ply


def test_write_ply(tmp_path: Path):
    points = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
    colors = np.array([[0, 10, 20], [30, 40, 50]], dtype=np.uint8)
    path = tmp_path / "test.ply"
    write_ply(path, points, colors)
    text = path.read_text(encoding="utf-8")
    assert "element vertex 2" in text
    assert text.count("\n") >= 10
