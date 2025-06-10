# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path

from swh.model.model import Content


def test_content(
    fuse_graph_mountpoint: Path, example_content_swhid: str, example_content: Content
):
    root = fuse_graph_mountpoint / "archive" / example_content_swhid

    assert root.is_file()
    with root.open("rb") as f:
        content = f.read()
        assert content == example_content.data
