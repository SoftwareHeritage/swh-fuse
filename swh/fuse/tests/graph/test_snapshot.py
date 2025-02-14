# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path


def test_snapshot(fuse_graph_mountpoint: Path, example_snapshot: str):
    root = fuse_graph_mountpoint / "archive" / example_snapshot
    assert root.is_dir()
    subpaths = list(root.iterdir())
    assert len(subpaths) == 1
    assert subpaths[0].name == "refs"
    assert subpaths[0].is_dir()
    refs = subpaths[0]

    subfolders = set(d.name for d in refs.iterdir())
    assert subfolders == {"heads", "tags"}
    assert (refs / "heads").is_dir()
    assert (refs / "heads" / "master").is_symlink()
    assert (refs / "tags").is_dir()
    assert (refs / "tags" / "v1.0").is_symlink()
