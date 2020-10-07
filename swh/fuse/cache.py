# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from abc import ABC
import json
from typing import Any, AsyncGenerator, Dict, Optional

import aiosqlite

from swh.model.identifiers import SWHID, parse_swhid
from swh.web.client.client import typify_json


class FuseCache:
    """ SWH FUSE retrieves both metadata and file contents from the Software
    Heritage archive via the network. In order to obtain reasonable performances
    several caches are used to minimize network transfer.

    Caches are stored on disk in SQLite databases located at
    `$XDG_CACHE_HOME/swh/fuse/`.

    All caches are persistent (i.e., they survive the restart of the SWH FUSE
    process) and global (i.e., they are shared by concurrent SWH FUSE
    processes).

    We assume that no cache *invalidation* is necessary, due to intrinsic
    properties of the Software Heritage archive, such as integrity verification
    and append-only archive changes. To clean the caches one can just remove the
    corresponding files from disk. """

    def __init__(self, cache_conf: Dict[str, Any]):
        self.cache_conf = cache_conf

    async def __aenter__(self):
        self.metadata = MetadataCache(self.cache_conf["metadata"])
        self.blob = BlobCache(self.cache_conf["blob"])
        await self.metadata.__aenter__()
        await self.blob.__aenter__()
        return self

    async def __aexit__(self, type=None, val=None, tb=None) -> None:
        await self.metadata.__aexit__()
        await self.blob.__aexit__()

    async def get_cached_swhids(self) -> AsyncGenerator[SWHID, None]:
        """ Return a list of all previously cached SWHID """

        # Use the metadata db since it should always contain all accessed SWHIDs
        metadata_cursor = await self.metadata.conn.execute(
            "select swhid from metadata_cache"
        )
        swhids = await metadata_cursor.fetchall()
        for raw_swhid in swhids:
            yield parse_swhid(raw_swhid[0])


class AbstractCache(ABC):
    """ Abstract cache implementation to share common behavior between cache
    types (such as: YAML config parsing, SQLite context manager) """

    def __init__(self, conf: Dict[str, Any]):
        self.conf = conf

    async def __aenter__(self):
        # In-memory (thus temporary) caching is useful for testing purposes
        if self.conf.get("in-memory", False):
            path = ":memory:"
        else:
            path = self.conf["path"]
        self.conn = await aiosqlite.connect(path)
        return self

    async def __aexit__(self, type=None, val=None, tb=None) -> None:
        await self.conn.close()


class MetadataCache(AbstractCache):
    """ The metadata cache map each SWHID to the complete metadata of the
    referenced object. This is analogous to what is available in
    `meta/<SWHID>.json` file (and generally used as data source for returning
    the content of those files). """

    async def __aenter__(self):
        await super().__aenter__()
        await self.conn.execute(
            "create table if not exists metadata_cache (swhid, metadata)"
        )
        return self

    async def get(self, swhid: SWHID, typify: bool = True) -> Any:
        cursor = await self.conn.execute(
            "select metadata from metadata_cache where swhid=?", (str(swhid),)
        )
        cache = await cursor.fetchone()
        if cache:
            metadata = json.loads(cache[0])
            return typify_json(metadata, swhid.object_type) if typify else metadata
        else:
            return None

    async def set(self, swhid: SWHID, metadata: Any) -> None:
        await self.conn.execute(
            "insert into metadata_cache values (?, ?)",
            (str(swhid), json.dumps(metadata)),
        )


class BlobCache(AbstractCache):
    """ The blob cache map SWHIDs of type `cnt` to the bytes of their archived
    content.

    The blob cache entry for a given content object is populated, at the latest,
    the first time the object is `read()`-d. It might be populated earlier on
    due to prefetching, e.g., when a directory pointing to the given content is
    listed for the first time. """

    async def __aenter__(self):
        await super().__aenter__()
        await self.conn.execute("create table if not exists blob_cache (swhid, blob)")
        return self

    async def get(self, swhid: SWHID) -> Optional[bytes]:
        cursor = await self.conn.execute(
            "select blob from blob_cache where swhid=?", (str(swhid),)
        )
        cache = await cursor.fetchone()
        if cache:
            blob = cache[0]
            return blob
        else:
            return None

    async def set(self, swhid: SWHID, blob: bytes) -> None:
        await self.conn.execute(
            "insert into blob_cache values (?, ?)", (str(swhid), blob)
        )
