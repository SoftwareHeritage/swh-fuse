# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass, field
import json
from typing import AsyncIterator

from swh.fuse.fs.artifact import OBJTYPE_GETTERS
from swh.fuse.fs.entry import EntryMode, FuseEntry
from swh.model.identifiers import CONTENT, SWHID


@dataclass
class Root(FuseEntry):
    """ The FUSE mountpoint, consisting of the archive/ and meta/ directories """

    name: str = field(init=False, default=None)
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))
    depth: int = field(init=False, default=1)

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        yield self.create_child(ArchiveDir)
        yield self.create_child(MetaDir)


@dataclass
class ArchiveDir(FuseEntry):
    """ The archive/ directory is lazily populated with one entry per accessed
    SWHID, having actual SWHIDs as names """

    name: str = field(init=False, default="archive")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        async for swhid in self.fuse.cache.get_cached_swhids():
            if swhid.object_type == CONTENT:
                mode = EntryMode.RDONLY_FILE
            else:
                mode = EntryMode.RDONLY_DIR
            yield self.create_child(
                OBJTYPE_GETTERS[swhid.object_type],
                name=str(swhid),
                mode=int(mode),
                swhid=swhid,
            )


@dataclass
class MetaDir(FuseEntry):
    """ The meta/ directory contains one SWHID.json file for each SWHID entry
    under archive/. The JSON file contain all available meta information about
    the given SWHID, as returned by the Software Heritage Web API for that
    object. Note that, in case of pagination (e.g., snapshot objects with many
    branches) the JSON file will contain a complete version with all pages
    merged together. """

    name: str = field(init=False, default="meta")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        async for swhid in self.fuse.cache.get_cached_swhids():
            yield self.create_child(
                MetaEntry,
                name=f"{swhid}.json",
                mode=int(EntryMode.RDONLY_FILE),
                swhid=swhid,
            )


@dataclass
class MetaEntry(FuseEntry):
    """ An entry from the meta/ directory, containing for each accessed SWHID a
    corresponding SWHID.json file with all the metadata from the Software
    Heritage archive. """

    swhid: SWHID

    async def get_content(self) -> bytes:
        # Get raw JSON metadata from API (un-typified)
        metadata = await self.fuse.cache.metadata.get(self.swhid, typify=False)
        return json.dumps(metadata).encode()

    async def size(self) -> int:
        return len(await self.get_content())
