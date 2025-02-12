# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import logging
from typing import Any, Dict, List, Tuple

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

    async def get_metadata(self, swhid: CoreSWHID) -> dict:
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

        TODO which fields ?
        """
