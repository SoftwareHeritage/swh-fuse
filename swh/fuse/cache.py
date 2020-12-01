# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from abc import ABC
from collections import OrderedDict
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import aiosqlite
import dateutil.parser
from psutil import virtual_memory

from swh.fuse.fs.artifact import RevisionHistoryShardByDate
from swh.fuse.fs.entry import FuseDirEntry, FuseEntry
from swh.fuse.fs.mountpoint import ArchiveDir, MetaDir, OriginDir
from swh.model.exceptions import ValidationError
from swh.model.identifiers import REVISION, SWHID, parse_swhid
from swh.web.client.client import ORIGIN_VISIT, typify_json


class FuseCache:
    """SwhFS retrieves both metadata and file contents from the Software Heritage archive
    via the network. In order to obtain reasonable performances several caches are used
    to minimize network transfer.

    Caches are stored on disk in SQLite databases located at
    `$XDG_CACHE_HOME/swh/fuse/`.

    All caches are persistent (i.e., they survive the restart of the SwhFS process) and
    global (i.e., they are shared by concurrent SwhFS processes).

    We assume that no cache *invalidation* is necessary, due to intrinsic
    properties of the Software Heritage archive, such as integrity verification
    and append-only archive changes. To clean the caches one can just remove the
    corresponding files from disk.

    """

    def __init__(self, cache_conf: Dict[str, Any]):
        self.cache_conf = cache_conf

    async def __aenter__(self):
        # History and raw metadata share the same SQLite db
        self.metadata = MetadataCache(self.cache_conf["metadata"])
        self.history = HistoryCache(self.cache_conf["metadata"])
        self.blob = BlobCache(self.cache_conf["blob"])
        self.direntry = DirEntryCache(self.cache_conf["direntry"])
        await self.metadata.__aenter__()
        await self.blob.__aenter__()
        await self.history.__aenter__()
        return self

    async def __aexit__(self, type=None, val=None, tb=None) -> None:
        await self.metadata.__aexit__()
        await self.blob.__aexit__()
        await self.history.__aexit__()

    async def get_cached_swhids(self) -> AsyncGenerator[SWHID, None]:
        """ Return a list of all previously cached SWHID """

        # Use the metadata db since it should always contain all accessed SWHIDs
        metadata_cursor = await self.metadata.conn.execute(
            "select swhid from metadata_cache"
        )
        swhids = await metadata_cursor.fetchall()
        for raw_swhid in swhids:
            yield parse_swhid(raw_swhid[0])

    async def get_cached_visits(self) -> AsyncGenerator[str, None]:
        """ Return a list of all previously cached visit URL """

        cursor = await self.metadata.conn.execute("select url from visits_cache")
        urls = await cursor.fetchall()
        for raw_url in urls:
            yield raw_url[0]


class AbstractCache(ABC):
    """ Abstract cache implementation to share common behavior between cache
    types (such as: YAML config parsing, SQLite context manager) """

    def __init__(self, conf: Dict[str, Any]):
        self.conf = conf

    async def __aenter__(self):
        # In-memory (thus temporary) caching is useful for testing purposes
        if self.conf.get("in-memory", False):
            path = "file::memory:?cache=shared"
            uri = True
        else:
            path = Path(self.conf["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            uri = False
        self.conn = await aiosqlite.connect(path, uri=uri)
        return self

    async def __aexit__(self, type=None, val=None, tb=None) -> None:
        await self.conn.close()


class MetadataCache(AbstractCache):
    """ The metadata cache map each artifact to the complete metadata of the
    referenced object. This is analogous to what is available in
    `meta/<SWHID>.json` file (and generally used as data source for returning
    the content of those files). Artifacts are identified using their SWHIDs, or
    in the case of origin visits, using their URLs. """

    DB_SCHEMA = """
        create table if not exists metadata_cache (
            swhid text,
            metadata blob,
            date text
        );
        create index if not exists idx_metadata on metadata_cache(swhid);

        create table if not exists visits_cache (
            url text,
            metadata blob
        );
        create index if not exists idx_visits on visits_cache(url);
    """

    async def __aenter__(self):
        await super().__aenter__()
        await self.conn.executescript(self.DB_SCHEMA)
        await self.conn.commit()
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

    async def get_visits(self, url_encoded: str) -> Optional[List[Dict[str, Any]]]:
        cursor = await self.conn.execute(
            "select metadata from visits_cache where url=?", (url_encoded,)
        )
        cache = await cursor.fetchone()
        if cache:
            visits = json.loads(cache[0])
            visits_typed = [typify_json(v, ORIGIN_VISIT) for v in visits]
            return visits_typed
        else:
            return None

    async def set(self, swhid: SWHID, metadata: Any) -> None:
        # Fill in the date column for revisions (used as cache for history/by-date/)
        swhid_date = ""
        if swhid.object_type == REVISION:
            date = dateutil.parser.parse(metadata["date"])
            swhid_date = RevisionHistoryShardByDate.DATE_FMT.format(
                year=date.year, month=date.month, day=date.day
            )

        await self.conn.execute(
            "insert into metadata_cache values (?, ?, ?)",
            (str(swhid), json.dumps(metadata), swhid_date),
        )
        await self.conn.commit()

    async def set_visits(self, url_encoded: str, visits: List[Dict[str, Any]]) -> None:
        await self.conn.execute(
            "insert into visits_cache values (?, ?)", (url_encoded, json.dumps(visits)),
        )
        await self.conn.commit()


class BlobCache(AbstractCache):
    """ The blob cache map SWHIDs of type `cnt` to the bytes of their archived
    content.

    The blob cache entry for a given content object is populated, at the latest,
    the first time the object is `read()`-d. It might be populated earlier on
    due to prefetching, e.g., when a directory pointing to the given content is
    listed for the first time. """

    DB_SCHEMA = """
        create table if not exists blob_cache (
            swhid text,
            blob blob
        );
        create index if not exists idx_blob on blob_cache(swhid);
    """

    async def __aenter__(self):
        await super().__aenter__()
        await self.conn.executescript(self.DB_SCHEMA)
        await self.conn.commit()
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
        await self.conn.commit()


class HistoryCache(AbstractCache):
    """ The history cache map SWHIDs of type `rev` to a list of `rev` SWHIDs
    corresponding to all its revision ancestors, sorted in reverse topological
    order. As the parents cache, the history cache is lazily populated and can
    be prefetched. To efficiently store the ancestor lists, the history cache
    represents ancestors as graph edges (a pair of two SWHID nodes), meaning the
    history cache is shared amongst all revisions parents. """

    DB_SCHEMA = """
        create table if not exists history_graph (
            src text not null,
            dst text not null,
            unique(src, dst)
        );
        create index if not exists idx_history on history_graph(src);
    """

    async def __aenter__(self):
        await super().__aenter__()
        await self.conn.executescript(self.DB_SCHEMA)
        await self.conn.commit()
        return self

    HISTORY_REC_QUERY = """
        with recursive
        dfs(node) AS (
            values(?)
            union
            select history_graph.dst
            from history_graph
            join dfs on history_graph.src = dfs.node
        )
        -- Do not keep the root node since it is not an ancestor
        select * from dfs limit -1 offset 1
    """

    async def get(self, swhid: SWHID) -> Optional[List[SWHID]]:
        cursor = await self.conn.execute(self.HISTORY_REC_QUERY, (str(swhid),),)
        cache = await cursor.fetchall()
        if not cache:
            return None
        history = []
        for row in cache:
            parent = row[0]
            try:
                history.append(parse_swhid(parent))
            except ValidationError:
                logging.warning("Cannot parse object from history cache: %s", parent)
        return history

    async def get_with_date_prefix(
        self, swhid: SWHID, date_prefix: str
    ) -> List[Tuple[SWHID, str]]:
        cursor = await self.conn.execute(
            f"""
            select swhid, date from ( {self.HISTORY_REC_QUERY} ) as history
            join metadata_cache on history.node = metadata_cache.swhid
            where metadata_cache.date like '{date_prefix}%'
            """,
            (str(swhid),),
        )
        cache = await cursor.fetchall()
        if not cache:
            return []

        history = []
        for row in cache:
            parent, date = row[0], row[1]
            try:
                history.append((parse_swhid(parent), date))
            except ValidationError:
                logging.warning("Cannot parse object from history cache: %s", parent)
        return history

    async def set(self, history: str) -> None:
        history = history.strip()
        if history:
            edges = [edge.split(" ") for edge in history.split("\n")]
            await self.conn.executemany(
                "insert or ignore into history_graph values (?, ?)", edges
            )
            await self.conn.commit()


class DirEntryCache:
    """ The direntry cache map inode representing directories to the entries
    they contain. Each entry comes with its name as well as file attributes
    (i.e., all its needed to perform a detailed directory listing).

    Additional attributes of each directory entry should be looked up on a entry
    by entry basis, possibly hitting other caches.

    The direntry cache for a given dir is populated, at the latest, when the
    content of the directory is listed. More aggressive prefetching might
    happen. For instance, when first opening a dir a recursive listing of it can
    be retrieved from the remote backend and used to recursively populate the
    direntry cache for all (transitive) sub-directories. """

    @dataclass
    class LRU(OrderedDict):
        max_ram: int
        used_ram: int = field(init=False, default=0)

        def sizeof(self, value: Any) -> int:
            # Rough size estimate in bytes for a list of entries
            return len(value) * 1000

        def __getitem__(self, key: Any) -> Any:
            value = super().__getitem__(key)
            self.move_to_end(key)
            return value

        def __setitem__(self, key: Any, value: Any) -> None:
            if key in self:
                self.move_to_end(key)
            else:
                self.used_ram += self.sizeof(value)

            super().__setitem__(key, value)

            while self.used_ram > self.max_ram and self:
                oldest = next(iter(self))
                self.used_ram -= self.sizeof(oldest)
                del self[oldest]

    def __init__(self, conf: Dict[str, Any]):
        m = re.match(r"(\d+)\s*(.+)\s*", conf["maxram"])
        if not m:
            logging.error("Cannot parse direntry maxram config: %s", conf["maxram"])
            sys.exit(1)

        num = float(m.group(1))
        unit = m.group(2).upper()

        if unit == "%":
            max_ram = int(num * virtual_memory().available / 100)
        else:
            units = {"B": 1, "KB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9}
            max_ram = int(float(num) * units[unit])

        self.lru_cache = self.LRU(max_ram)

    def get(self, direntry: FuseDirEntry) -> Optional[List[FuseEntry]]:
        return self.lru_cache.get(direntry.inode, None)

    def set(self, direntry: FuseDirEntry, entries: List[FuseEntry]) -> None:
        if isinstance(direntry, (ArchiveDir, MetaDir, OriginDir)):
            # The `archive/`, `meta/`, and `origin/` are populated on the fly so
            # we should never cache them
            pass
        elif (
            isinstance(direntry, RevisionHistoryShardByDate)
            and not direntry.is_status_done
        ):
            # The `by-date/' directory is populated in parallel so only cache it
            # once it has finished fetching all data from the API
            pass
        else:
            self.lru_cache[direntry.inode] = entries
