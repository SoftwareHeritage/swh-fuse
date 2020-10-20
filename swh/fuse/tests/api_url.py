# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from enum import Enum
from typing import Union

from swh.model.identifiers import (
    CONTENT,
    DIRECTORY,
    RELEASE,
    REVISION,
    SNAPSHOT,
    SWHID,
    parse_swhid,
)

GRAPH_API_REQUEST = Enum("GRAPH_API_REQUEST", "HISTORY")


def swhid_to_web_url(swhid: Union[SWHID, str], raw: bool = False) -> str:
    if isinstance(swhid, str):
        swhid = parse_swhid(swhid)

    prefix = {
        CONTENT: "content/sha1_git:",
        DIRECTORY: "directory/",
        REVISION: "revision/",
        RELEASE: "release/",
        SNAPSHOT: "snapshot/",
    }

    url = f"{prefix[swhid.object_type]}{swhid.object_id}/"
    if raw:
        url += "raw/"
    return url


def swhid_to_graph_url(
    swhid: Union[SWHID, str], request_type: GRAPH_API_REQUEST
) -> str:
    if isinstance(swhid, str):
        swhid = parse_swhid(swhid)

    prefix = {
        GRAPH_API_REQUEST.HISTORY: "graph/visit/edges/",
    }

    return f"{prefix[request_type]}{swhid}"
