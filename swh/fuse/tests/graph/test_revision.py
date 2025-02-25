# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from pathlib import Path


def test_revision(fuse_graph_mountpoint: Path, example_revision: str):
    root = fuse_graph_mountpoint / "archive" / example_revision
    assert root.is_dir()
    assert (root / "meta.json").is_symlink()

    with (root / "meta.json").open() as f:
        parsed = json.loads(f.read())
        assert parsed["id"] in example_revision
        assert "author" in parsed
        assert "committer" in parsed
        assert "message" in parsed
        assert "parents" in parsed
        assert "directory" in parsed
        assert parsed["date"] == "2005-03-18T13:14:00+02:00"
        assert parsed["committer_date"] == "2005-03-18T16:19:10+02:00"

    assert (root / "parents").is_dir()
    assert (root / "parent").is_symlink()
    assert (root / "root").is_symlink()

    assert (root / "history").is_dir()
    # TODO
