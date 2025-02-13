# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import logging
from typing import Any, Dict, List, Tuple
import hashlib
from urllib.parse import unquote_plus
from datetime import date

import grpc

from swh.fuse import LOGGER_NAME
import swh.graph.grpc.swhgraph_pb2 as swhgraph
import swh.graph.grpc.swhgraph_pb2_grpc as swhgraph_grpc
from swh.model.swhids import CoreSWHID

from ..backends import FuseBackend


class GraphBackend(FuseBackend):
    """
    A Backend querying everything via Software Heritage's public API.

    This is simpler to configure and deploy, but expect long response times when
    exploring big directories.
    """

    def __init__(self, conf: dict):
        """
        Only needs the `web-api` key of `conf`, searching for `url` and maybe `auth-token` keys.
        """
        self.grpc_stub = swhgraph_grpc.TraversalServiceStub(
            grpc.insecure_channel(conf["graph"]["grpc-url"])
        )
        self.logger = logging.getLogger(LOGGER_NAME)

    async def get_metadata(self, swhid: CoreSWHID) -> Dict | List:
        """
        Entries in the returned `dict` depend on the `swhid` type.

        TODO detail per type
        """
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            None,
            self.grpc_stub.GetNode,
            swhgraph.GetNodeRequest(swhid=str(swhid)),
        )

        # something like
        # for entry in metadata.successor:
        #   name = entry.label[0].name.decode()
        #   swhid = CoreSWHID.from_string(entry.swhid)
        #   mode = (...
        #     entry.label[0].permission



        return metadata

    async def get_blob(self, swhid: CoreSWHID) -> bytes:
        """
        Fetch the content of a `cnt` object.
        """

    async def get_history(self, swhid: CoreSWHID) -> List[Tuple[str, str]]:
        """
        Return a list of tuples `(swhid, revision swhid)`
        """

    async def get_visits(self, url_encoded: str) -> List[Dict[str, Any]]:
        """
        Return a list of objects

        This GetNode returns:

        swhid: "swh:1:ori:872aeac9f211c8b12c58e6a5092a0ae20e517b11"
        successor {
            swhid: "swh:1:snp:c7d88f7679e29a81440682c558bb439c7628cd20"
            label {
                visit_timestamp: 1677206735
                is_full_visit: true
            }
        }
        successor {
            swhid: "swh:1:snp:a972d1e29dc327c661d7ebc30334b604aff3a96f"
            label {
                visit_timestamp: 1712340909
                is_full_visit: true
            }
            label {
                visit_timestamp: 1712368096
                is_full_visit: true
            }
        }
        ...
        ori {
        url: "https://github.com/ytdl-org/youtube-dl"
        }
        num_successors: 168


        """
        url = unquote_plus(url_encoded).encode()
        swhid = "swh:1:ori:" + hashlib.sha1(url).hexdigest()

        loop = asyncio.get_event_loop()
        ori_node = await loop.run_in_executor(
            None,
            self.grpc_stub.GetNode,
            swhgraph.GetNodeRequest(swhid=str(swhid)),
        )

        origin = ori_node.ori.url
        visits = []
        for entry in ori_node.successor:
            snapshot = CoreSWHID.from_string(entry.swhid)
            for label in entry.label:
                visit_date = date.fromtimestamp(label.visit_timestamp)
                visits.append({
                    "date": visit_date.isoformat(),
                    "origin": origin,
                    "snapshot": snapshot.object_id.hex(),
                })

        return visits