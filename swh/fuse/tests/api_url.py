# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from enum import Enum
from typing import Union

from swh.model.hashutil import hash_to_hex
from swh.model.identifiers import CoreSWHID, ObjectType

GRAPH_API_REQUEST = Enum("GRAPH_API_REQUEST", "HISTORY")


def swhid_to_web_url(swhid: Union[CoreSWHID, str], raw: bool = False) -> str:
    if isinstance(swhid, str):
        swhid = CoreSWHID.from_string(swhid)

    prefix = {
        ObjectType.CONTENT: "content/sha1_git:",
        ObjectType.DIRECTORY: "directory/",
        ObjectType.REVISION: "revision/",
        ObjectType.RELEASE: "release/",
        ObjectType.SNAPSHOT: "snapshot/",
    }

    url = f"{prefix[swhid.object_type]}{hash_to_hex(swhid.object_id)}/"
    if raw:
        url += "raw/"
    return url


def swhid_to_graph_url(
    swhid: Union[CoreSWHID, str], request_type: GRAPH_API_REQUEST
) -> str:
    if isinstance(swhid, str):
        swhid = CoreSWHID.from_string(swhid)

    prefix = {
        GRAPH_API_REQUEST.HISTORY: "graph/visit/edges/",
    }

    return f"{prefix[request_type]}{swhid}"
