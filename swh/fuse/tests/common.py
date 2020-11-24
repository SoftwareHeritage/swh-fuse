# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
from pathlib import Path
from typing import Any, List

from swh.fuse.tests.api_url import (
    GRAPH_API_REQUEST,
    swhid_to_graph_url,
    swhid_to_web_url,
)
from swh.fuse.tests.data.api_data import MOCK_ARCHIVE


def get_data_from_web_archive(swhid: str, raw: bool = False) -> Any:
    url = swhid_to_web_url(swhid, raw)

    # Special case: snapshots Web API and Web Client API differ a bit in format
    if url.startswith("snapshot"):
        return MOCK_ARCHIVE[url]["branches"]
    else:
        return MOCK_ARCHIVE[url]


def get_origin_data_from_web_archive(url: str) -> Any:
    return MOCK_ARCHIVE[f"origin/{url}/visits/"]


def get_data_from_graph_archive(swhid: str, request_type: GRAPH_API_REQUEST) -> Any:
    url = swhid_to_graph_url(swhid, request_type)
    return MOCK_ARCHIVE[url]


def get_dir_name_entries(swhid: str) -> List[str]:
    dir_meta = get_data_from_web_archive(swhid)
    return [x["name"] for x in dir_meta]


def check_dir_name_entries(dir_path: Path, dir_swhid: str) -> None:
    expected = get_dir_name_entries(dir_swhid)
    actual = os.listdir(dir_path)
    assert set(actual) == set(expected)
