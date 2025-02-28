# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path
import re

import requests_mock

from . import WEB_API_URL


def test_content(fuse_graph_mountpoint: Path, example_content: str):
    root = fuse_graph_mountpoint / "archive" / example_content
    with requests_mock.Mocker() as mocker:
        pattern = re.compile(f"{WEB_API_URL}/content/sha1_git:[0-9a-f]+/raw/")
        mocker.get(pattern, text="Hello world")

        assert root.is_file()
        with root.open("rb") as f:
            content = f.read()
            assert len(content) > 0
