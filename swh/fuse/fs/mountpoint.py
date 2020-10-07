# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from typing import AsyncIterator

from swh.fuse.fs.artifact import typify
from swh.fuse.fs.entry import EntryMode, FuseEntry
from swh.model.identifiers import CONTENT, SWHID

# Avoid cycling import
Fuse = "Fuse"


class Root(FuseEntry):
    """ The FUSE mountpoint, consisting of the archive/ and meta/ directories """

    def __init__(self, fuse: Fuse):
        super().__init__(name="root", mode=int(EntryMode.RDONLY_DIR), fuse=fuse)

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        for entry in [ArchiveDir(self.fuse), MetaDir(self.fuse)]:
            yield entry


class ArchiveDir(FuseEntry):
    """ The archive/ directory is lazily populated with one entry per accessed
    SWHID, having actual SWHIDs as names """

    def __init__(self, fuse: Fuse):
        super().__init__(name="archive", mode=int(EntryMode.RDONLY_DIR), fuse=fuse)

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        async for swhid in self.fuse.cache.get_cached_swhids():
            if swhid.object_type == CONTENT:
                mode = EntryMode.RDONLY_FILE
            else:
                mode = EntryMode.RDONLY_DIR
            yield typify(str(swhid), int(mode), self.fuse, swhid)


class MetaDir(FuseEntry):
    """ The meta/ directory contains one SWHID.json file for each SWHID entry
    under archive/. The JSON file contain all available meta information about
    the given SWHID, as returned by the Software Heritage Web API for that
    object. Note that, in case of pagination (e.g., snapshot objects with many
    branches) the JSON file will contain a complete version with all pages
    merged together. """

    def __init__(self, fuse: Fuse):
        super().__init__(name="meta", mode=int(EntryMode.RDONLY_DIR), fuse=fuse)

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        async for swhid in self.fuse.cache.get_cached_swhids():
            yield MetaEntry(swhid, self.fuse)


class MetaEntry(FuseEntry):
    """ An entry from the meta/ directory, containing for each accessed SWHID a
    corresponding SWHID.json file with all the metadata from the Software
    Heritage archive. """

    def __init__(self, swhid: SWHID, fuse: Fuse):
        super().__init__(
            name=str(swhid) + ".json", mode=int(EntryMode.RDONLY_FILE), fuse=fuse
        )
        self.swhid = swhid

    async def content(self) -> bytes:
        # Get raw JSON metadata from API (un-typified)
        metadata = await self.fuse.cache.metadata.get(self.swhid, typify=False)
        return json.dumps(metadata).encode()

    async def length(self) -> int:
        return len(await self.content())
