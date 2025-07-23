# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import base64
from datetime import date, datetime, timedelta, timezone
import hashlib
import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import unquote_plus

from google.protobuf.field_mask_pb2 import FieldMask
import grpc

from swh.core.statsd import Statsd, TimedContextManagerDecorator
from swh.fuse import LOGGER_NAME
import swh.graph.grpc.swhgraph_pb2 as swhgraph
import swh.graph.grpc.swhgraph_pb2_grpc as swhgraph_grpc
from swh.model.swhids import CoreSWHID, ObjectType

from . import GraphBackend


def decode_or_base64(data: bytes) -> str:
    """
    If ``data`` is not proper UTF-8, return it as base64.
    """
    try:
        return data.decode()
    except UnicodeDecodeError:
        return base64.b64encode(data).decode()


class CompressedGraphBackend(GraphBackend):
    """
    A Backend querying a compressed graph instance via gRPC.
    """

    def __init__(self, conf: dict):
        """
        Only needs ``graph.grpc-url``.
        """
        self.grpc_stub = swhgraph_grpc.TraversalServiceStub(
            grpc.insecure_channel(
                conf["graph"]["grpc-url"],
                [
                    # advanced options are listed in
                    # github.com/grpc/grpc/blob/master/include/grpc/impl/channel_arg_names.h
                    #
                    # disable the limit on message length, because listing some folders
                    # may exceed the default value
                    ("grpc.max_receive_message_length", -1),
                ],
            )
        )
        self.logger = logging.getLogger(LOGGER_NAME)
        self.time_tracker = TimedContextManagerDecorator(
            Statsd(), "swhfuse_waiting_graph"
        )

    def shutdown(self) -> None:
        self.logger.info(
            "Spent %f ms waiting for graph server",
            self.time_tracker.total_elapsed,
        )

    async def get_metadata(self, swhid: CoreSWHID) -> Dict | List:
        loop = asyncio.get_event_loop()
        with self.time_tracker:
            raw = await loop.run_in_executor(
                None,
                self.grpc_stub.GetNode,
                swhgraph.GetNodeRequest(swhid=str(swhid)),
            )

        match swhid.object_type:
            case ObjectType.SNAPSHOT:
                return self._snapshot_metadata(raw)

            case ObjectType.REVISION:
                return self._revision_metadata(swhid, raw)

            case ObjectType.RELEASE:
                return self._release_metadata(swhid, raw)

            case ObjectType.DIRECTORY:
                return await self._directory_metadata(swhid, raw)

            case ObjectType.CONTENT:
                return await self._content_metadata(swhid, raw)

            case _:
                raise NotImplementedError(
                    f"get_metadata({swhid.object_type}) not supported"
                )

    def _snapshot_metadata(self, raw: swhgraph.Node) -> Dict:
        metadata = {}
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            for branch in successor.label:
                branch_name = decode_or_base64(branch.name)
                metadata[branch_name] = {
                    "target": target.object_id.hex(),
                    "target_type": target.object_type.name.lower(),
                }
        return metadata

    def _revision_metadata(self, swhid: CoreSWHID, raw: swhgraph.Node) -> Dict:
        parents = []
        directory = None
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            if target.object_type == ObjectType.DIRECTORY:
                directory = target.object_id.hex()
            elif target.object_type == ObjectType.REVISION:
                parent = CoreSWHID.from_string(successor.swhid)
                parents.append({"id": parent.object_id.hex()})
            else:
                raise ValueError(
                    f"Unsupported successor type for {swhid}: {target.object_type}"
                )
        # we also provide fields from protobuf message RevisionData
        try:
            author_date = datetime.fromtimestamp(raw.rev.author_date, tz=timezone.utc)
            author_tz = timezone(timedelta(minutes=raw.rev.author_date_offset))
            author_date = author_date.astimezone(author_tz)
            author_date_str = author_date.isoformat()
        except ValueError:
            author_date_str = None

        try:
            committer_date = datetime.fromtimestamp(
                raw.rev.committer_date, tz=timezone.utc
            )
            committer_tz = timezone(timedelta(minutes=raw.rev.committer_date_offset))
            committer_date = committer_date.astimezone(committer_tz)
            committer_date_str = committer_date.isoformat()
        except ValueError:
            committer_date_str = None

        message = decode_or_base64(raw.rev.message)
        metadata = {
            "author": raw.rev.author,
            "committer": raw.rev.committer,
            "message": message,
            "date": author_date_str,
            "committer_date": committer_date_str,
            "parents": parents,
            "directory": directory,
            "id": swhid.object_id.hex(),
        }
        return metadata

    def _release_metadata(self, swhid: CoreSWHID, raw: swhgraph.Node) -> Dict:
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            break
        else:
            raise ValueError(f"Cannot find target for release {swhid}")

        try:
            rel_date = datetime.fromtimestamp(raw.rel.author_date, tz=timezone.utc)
            rel_tz = timezone(timedelta(minutes=raw.rel.author_date_offset))
            rel_date = rel_date.astimezone(rel_tz)
            rel_date_str = rel_date.isoformat()
        except ValueError:
            rel_date_str = None

        message = decode_or_base64(raw.rel.message)
        name = decode_or_base64(raw.rel.name)

        metadata = {
            "target": target.object_id.hex(),
            "target_type": target.object_type.name.lower(),
            "id": swhid.object_id.hex(),
            "message": message,
            "name": name,
            "author": raw.rel.author,
            "date": rel_date_str,
        }
        return metadata

    async def _directory_metadata(self, swhid: CoreSWHID, raw: swhgraph.Node) -> List:
        """
        In this case the ``raw`` object obtained from ``getNode`` is not enough,
        because we also need each successors' ``length`` property (if it's a content) to
        be on par with the WebAPI. We use a filtered traversal request to obtain lengths
        in a single gRPC call.
        """

        loop = asyncio.get_event_loop()
        with self.time_tracker:
            raw_cnt = await loop.run_in_executor(
                None,
                self.grpc_stub.Traverse,
                swhgraph.TraversalRequest(
                    src=[str(swhid)],
                    max_depth=1,
                    edges="dir:cnt",
                    mask=FieldMask(paths=["swhid", "cnt"]),
                ),
            )
        cnt_metadata = {}
        for item in raw_cnt:
            if item.HasField("cnt"):
                cnt_metadata[item.swhid] = {
                    "length": item.cnt.length,
                    "status": "skipped" if item.cnt.is_skipped else "visible",
                }

        metadata = []
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            target_type = target.object_type.value
            if target_type == ObjectType.CONTENT.value:
                # complying with swh-web-client.typify_json is hard
                target_type = "file"
            name = decode_or_base64(successor.label[0].name)
            entry = {
                "dir_id": swhid.object_id.hex(),
                "name": name,
                "perms": successor.label[0].permission,
                "type": target_type,
                "target": target.object_id.hex(),
            }
            if target.object_type == ObjectType.CONTENT:
                if successor.swhid in cnt_metadata:
                    entry.update(cnt_metadata[successor.swhid])
                else:
                    self.logger.warning(
                        "%s listed as successor of %s, but not fetched by raw_cnt",
                        target,
                        swhid,
                    )
            metadata.append(entry)

        return metadata

    async def _content_metadata(self, swhid: CoreSWHID, raw: swhgraph.Node) -> Dict:
        return {
            "length": raw.cnt.length,
            "status": "skipped" if raw.cnt.is_skipped else "visible",
        }

    async def get_history(self, swhid: CoreSWHID) -> List[Tuple[str, str]]:
        loop = asyncio.get_event_loop()
        with self.time_tracker:
            raw_cnt = await loop.run_in_executor(
                None,
                self.grpc_stub.Traverse,
                swhgraph.TraversalRequest(
                    src=[str(swhid)],
                    edges="rev:rev",
                    mask=FieldMask(paths=["swhid"]),
                ),
            )
        str_swhid = str(swhid)
        return [(str_swhid, str(entry.swhid)) for entry in raw_cnt]

    async def get_visits(self, url_encoded: str) -> List[Dict[str, Any]]:
        url = unquote_plus(url_encoded)
        swhid = "swh:1:ori:" + hashlib.sha1(url.encode()).hexdigest()

        loop = asyncio.get_event_loop()
        with self.time_tracker:
            ori_node = await loop.run_in_executor(
                None,
                self.grpc_stub.GetNode,
                swhgraph.GetNodeRequest(swhid=str(swhid)),
            )

        origin = url
        visits = []
        for entry in ori_node.successor:
            snapshot = CoreSWHID.from_string(entry.swhid)
            for label in entry.label:
                visit_date = date.fromtimestamp(label.visit_timestamp)
                visits.append(
                    {
                        "date": visit_date.isoformat(),
                        "origin": origin,
                        "snapshot": snapshot.object_id.hex(),
                    }
                )

        return visits
