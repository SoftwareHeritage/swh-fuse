# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path
from typing import Any

from swh.fuse.tests.data.api_data import MOCK_ARCHIVE, SWHID2URL


def get_data_from_archive(swhid: str, raw: bool = False) -> Any:
    url = SWHID2URL[swhid]
    if raw:
        url += "raw/"
    return MOCK_ARCHIVE[url]


def assert_file_content(path: Path, expected: str) -> None:
    with open(path, "r") as f:
        actual = f.read()
        assert actual == expected
