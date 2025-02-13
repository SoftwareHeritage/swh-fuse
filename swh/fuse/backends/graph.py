# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
from datetime import date, datetime, timedelta, timezone
import hashlib
import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import unquote_plus

from google.protobuf.field_mask_pb2 import FieldMask
import grpc

from swh.fuse import LOGGER_NAME
import swh.graph.grpc.swhgraph_pb2 as swhgraph
import swh.graph.grpc.swhgraph_pb2_grpc as swhgraph_grpc
from swh.model.swhids import CoreSWHID, ObjectType

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
        loop = asyncio.get_event_loop()
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

            case _:
                raise NotImplementedError(
                    f"get_metadata({swhid.object_type}) not supported"
                )

    def _snapshot_metadata(self, raw) -> Dict:
        metadata = {}
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            branch = successor.label[0].name.decode()
            metadata[branch] = {
                "target": target.object_id.hex(),
                "target_type": target.object_type.name.lower(),
            }
        return metadata

    def _revision_metadata(self, swhid: CoreSWHID, raw) -> Dict:
        parents = []
        directory = None
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            if target.object_type == ObjectType.DIRECTORY:
                directory = target.object_id.hex()
            else:
                parent = CoreSWHID.from_string(successor.swhid)
                parents.append({"id": parent.object_id.hex()})
        # we also provide fields from protobuf message RevisionData
        author_date = datetime.fromtimestamp(raw.rev.author_date, tz=timezone.utc)
        author_tz = timezone(timedelta(seconds=raw.rev.author_date_offset))
        author_date = author_date.astimezone(author_tz)
        committer_date = datetime.fromtimestamp(raw.rev.committer_date, tz=timezone.utc)
        committer_tz = timezone(timedelta(seconds=raw.rev.committer_date_offset))
        committer_date = committer_date.astimezone(committer_tz)
        metadata = {
            "author": raw.rev.author,
            "committer": raw.rev.committer,
            "message": raw.rev.message.decode(),
            "date": author_date.isoformat(),
            "committer_date": committer_date.isoformat(),
            "parents": parents,
            "directory": directory,
            "id": swhid.object_id.hex(),
        }
        return metadata

    def _release_metadata(self, swhid: CoreSWHID, raw) -> Dict:
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            break
        else:
            raise ValueError(f"Cannot find target for release {swhid}")

        rel_date = datetime.fromtimestamp(raw.rel.author_date, tz=timezone.utc)
        rel_tz = timezone(timedelta(seconds=raw.rel.author_date_offset))
        rel_date = rel_date.astimezone(rel_tz)

        metadata = {
            "target": target.object_id.hex(),
            "target_type": target.object_type.name.lower(),
            "id": swhid.object_id.hex(),
            "message": raw.rel.message.decode(),
            "name": raw.rel.name.decode(),
            "author": raw.rel.author,
            "date": rel_date.isoformat(),
        }
        return metadata

    async def _directory_metadata(self, swhid: CoreSWHID, raw) -> List:
        loop = asyncio.get_event_loop()
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
        # something like
        for successor in raw.successor:
            target = CoreSWHID.from_string(successor.swhid)
            target_type = target.object_type.value
            if target_type == ObjectType.CONTENT.value:
                # complying with swh-web-client.typify_json is hard
                target_type = "file"
            entry = {
                "dir_id": swhid.object_id.hex(),
                "name": successor.label[0].name.decode(),
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
                visits.append(
                    {
                        "date": visit_date.isoformat(),
                        "origin": origin,
                        "snapshot": snapshot.object_id.hex(),
                    }
                )

        return visits
