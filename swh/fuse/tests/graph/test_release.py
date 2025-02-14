# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from pathlib import Path


def test_release(fuse_graph_mountpoint: Path, example_release: str):
    root = fuse_graph_mountpoint / "archive" / example_release
    assert root.is_dir()

    meta = root / "meta.json"
    assert meta.is_symlink()
    with meta.open() as f:
        parsed = json.loads(f.read())
        assert parsed["id"] in example_release
        assert "name" in parsed
        assert "author" in parsed
        assert "message" in parsed
        assert parsed["date"] == "2009-02-14T01:31:30+02:00"

    assert (root / "root").is_symlink()
    assert (root / "target").is_symlink()

    with (root / "target_type").open() as f:
        assert f.read() == "revision\n"
