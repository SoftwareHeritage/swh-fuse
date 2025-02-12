# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path


def test_directory(fuse_graph_mountpoint: Path):
    test_file = (
        fuse_graph_mountpoint
        / "archive"
        / "swh:1:cnt:0000000000000000000000000000000000000001"
    )
    assert test_file.is_file()
