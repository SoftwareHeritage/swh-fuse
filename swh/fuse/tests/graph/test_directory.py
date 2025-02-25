# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path
import re

import requests_mock

from . import WEB_API_URL


def test_directory(fuse_graph_mountpoint: Path, example_directory: str):
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

            with requests_mock.Mocker() as mocker:
                pattern = re.compile(f"{WEB_API_URL}/content/sha1_git:[0-9a-f]+/raw/")
                mocker.get(pattern, text="Hello world")
                with item.open("rb") as f:
                    content = f.read()
                    assert len(content) > 0
        else:
            raise AssertionError(
                f"{item} is not a file or directory, that's unexpected in the test graph"
            )
