# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Any, Optional, Set

from swh.model.identifiers import SWHID, parse_swhid
from swh.web.client.client import typify


class Cache:
    """ SWH FUSE retrieves both metadata and file contents from the Software
    Heritage archive via the network. In order to obtain reasonable performances
    several caches are used to minimize network transfer.

    Caches are stored on disk in SQLite databases located at
    `$XDG_CACHE_HOME/swh/fuse/cache.sqlite`.

    All caches are persistent (i.e., they survive the restart of the SWH FUSE
    process) and global (i.e., they are shared by concurrent SWH FUSE
    processes).

    We assume that no cache *invalidation* is necessary, due to intrinsic
    properties of the Software Heritage archive, such as integrity verification
    and append-only archive changes. To clean the caches one can just remove the
    corresponding files from disk. """

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def __enter__(self):
        # In-memory (thus temporary) caching is useful for testing purposes
        in_memory = ":memory:"
        if str(self.cache_dir) == in_memory:
            metadata_cache_path = in_memory
            blob_cache_path = in_memory
        else:
            metadata_cache_path = self.cache_dir / "metadata.sqlite"
            blob_cache_path = self.cache_dir / "blob.sqlite"

        self.metadata = MetadataCache(metadata_cache_path)
        self.metadata.__enter__()
        self.blob = BlobCache(blob_cache_path)
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


class MetadataCache:
    """ The metadata cache map each SWHID to the complete metadata of the
    referenced object. This is analogous to what is available in
    `meta/<SWHID>.json` file (and generally used as data source for returning
    the content of those files). """

    def __init__(self, path: str):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        with self.conn:
            self.conn.execute(
                "create table if not exists metadata_cache (swhid, metadata)"
            )
        return self

    def __exit__(self, type=None, val=None, tb=None) -> None:
        self.conn.close()

    def __getitem__(self, swhid: SWHID) -> Any:
        with closing(self.conn.cursor()) as cursor:
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
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(
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


class BlobCache:
    """ The blob cache map SWHIDs of type `cnt` to the bytes of their archived
    content.

    The blob cache entry for a given content object is populated, at the latest,
    the first time the object is `read()`-d. It might be populated earlier on
    due to prefetching, e.g., when a directory pointing to the given content is
    listed for the first time. """

    def __init__(self, path: str):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        with self.conn:
            self.conn.execute("create table if not exists blob_cache (swhid, blob)")
        return self

    def __exit__(self, type=None, val=None, tb=None) -> None:
        self.conn.close()

    def __getitem__(self, swhid: SWHID) -> Optional[str]:
        with closing(self.conn.cursor()) as cursor:
            cursor.execute("select blob from blob_cache where swhid=?", (str(swhid),))
            cache = cursor.fetchone()
            if cache:
                blob = cache[0]
                return blob
            else:
                return None

    def __setitem__(self, swhid: SWHID, blob: str) -> None:
        with closing(self.conn.cursor()) as cursor:
            cursor.execute("insert into blob_cache values (?, ?)", (str(swhid), blob))
