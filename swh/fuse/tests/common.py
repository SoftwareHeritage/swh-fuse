# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
from pathlib import Path
from typing import Any, List

from swh.fuse.tests.data.api_data import MOCK_ARCHIVE, SWHID2URL


def get_data_from_archive(swhid: str, raw: bool = False) -> Any:
    url = SWHID2URL[swhid]
    if raw:
        url += "raw/"
    return MOCK_ARCHIVE[url]


def get_dir_name_entries(swhid: str) -> List[str]:
    dir_meta = get_data_from_archive(swhid)
    return [x["name"] for x in dir_meta]


def check_dir_name_entries(dir_path: Path, dir_swhid: str) -> None:
    expected = get_dir_name_entries(dir_swhid)
    actual = os.listdir(dir_path)
    assert set(actual) == set(expected)
