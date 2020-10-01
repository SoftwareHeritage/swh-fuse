# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from abc import ABC
from contextlib import closing
import json
import sqlite3
from typing import Any, Dict, Optional, Set

from swh.model.identifiers import SWHID, parse_swhid
from swh.web.client.client import typify


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

    def __enter__(self):
        self.metadata = MetadataCache(self.cache_conf["metadata"])
        self.metadata.__enter__()
        self.blob = BlobCache(self.cache_conf["blob"])
        self.blob.__enter__()
        return self

    def __exit__(self, type=None, val=None, tb=None) -> None:
        self.metadata.__exit__()
        self.blob.__exit__()

    def get_cached_swhids(self) -> Set[SWHID]:
        """ Return a list of all previously cached SWHID """

        with closing(self.metadata.conn.cursor()) as metadata_cursor, (
            closing(self.blob.conn.cursor())
        ) as blob_cursor:
            # Some entries can be in one cache but not in the other so create a
            # set from all caches
            metadata_cursor.execute("select swhid from metadata_cache")
            blob_cursor.execute("select swhid from blob_cache")
            swhids = metadata_cursor.fetchall() + blob_cursor.fetchall()
            swhids = [parse_swhid(x[0]) for x in swhids]
            return set(swhids)


class AbstractCache(ABC):
    """ Abstract cache implementation to share common behavior between cache
    types (such as: YAML config parsing, SQLite context manager) """

    def __init__(self, conf: Dict[str, Any]):
        self.conf = conf

    def __enter__(self):
        # In-memory (thus temporary) caching is useful for testing purposes
        if self.conf.get("in-memory", False):
            path = ":memory:"
        else:
            path = self.conf["path"]
        self.conn = sqlite3.connect(path)
        return self

    def __exit__(self, type=None, val=None, tb=None) -> None:
        self.conn.close()


class MetadataCache(AbstractCache):
    """ The metadata cache map each SWHID to the complete metadata of the
    referenced object. This is analogous to what is available in
    `meta/<SWHID>.json` file (and generally used as data source for returning
    the content of those files). """

    def __enter__(self):
        super().__enter__()
        with self.conn as conn:
            conn.execute("create table if not exists metadata_cache (swhid, metadata)")
        return self

    def __getitem__(self, swhid: SWHID) -> Any:
        with self.conn as conn, closing(conn.cursor()) as cursor:
            cursor.execute(
                "select metadata from metadata_cache where swhid=?", (str(swhid),)
            )
            cache = cursor.fetchone()
            if cache:
                metadata = json.loads(cache[0])
                return typify(metadata, swhid.object_type)
            else:
                return None

    def __setitem__(self, swhid: SWHID, metadata: Any) -> None:
        with self.conn as conn:
            conn.execute(
                "insert into metadata_cache values (?, ?)",
                (
                    str(swhid),
                    json.dumps(
                        metadata,
                        # Converts the typified JSON to plain str version
                        default=lambda x: (
                            x.object_id if isinstance(x, SWHID) else x.__dict__
                        ),
                    ),
                ),
            )


class BlobCache(AbstractCache):
    """ The blob cache map SWHIDs of type `cnt` to the bytes of their archived
    content.

    The blob cache entry for a given content object is populated, at the latest,
    the first time the object is `read()`-d. It might be populated earlier on
    due to prefetching, e.g., when a directory pointing to the given content is
    listed for the first time. """

    def __enter__(self):
        super().__enter__()
        with self.conn as conn:
            conn.execute("create table if not exists blob_cache (swhid, blob)")
        return self

    def __getitem__(self, swhid: SWHID) -> Optional[str]:
        with self.conn as conn, closing(conn.cursor()) as cursor:
            cursor.execute("select blob from blob_cache where swhid=?", (str(swhid),))
            cache = cursor.fetchone()
            if cache:
                blob = cache[0]
                return blob
            else:
                return None

    def __setitem__(self, swhid: SWHID, blob: str) -> None:
        with self.conn as conn:
            conn.execute("insert into blob_cache values (?, ?)", (str(swhid), blob))
