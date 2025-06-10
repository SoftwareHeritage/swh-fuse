# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information
from pathlib import Path

import pytest


def test_directory(fuse_graph_mountpoint: Path, example_directory: str):
    with pytest.raises(FileNotFoundError):
        # this should not crash the process
        void = fuse_graph_mountpoint / "archive" / example_directory / "not-there"
        void.stat()

    root = fuse_graph_mountpoint / "archive" / example_directory
    assert root.is_dir()

    for item in root.iterdir():
        if item.is_dir():
            # in the test graph, that subfolder only contains two files
            files = list(item.iterdir())
            assert len(files) == 2
            for file in files:
                assert file.is_file()
        elif item.is_file():
            assert item.stat().st_size > 0

        else:
            raise AssertionError(
                f"{item} is not a file or directory, that's unexpected in the test graph"
            )
