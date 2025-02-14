# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path


def test_origin(fuse_graph_mountpoint: Path, example_origin: str):
    root = fuse_graph_mountpoint / "origin" / example_origin
    assert root.is_dir()
    empty = True
    for d in root.iterdir():
        empty = False
        assert d.is_dir()
    if empty:
        raise AssertionError(f"No directories in {root}")
    assert (d / "meta.json").is_file()
    assert (d / "snapshot").is_symlink()
