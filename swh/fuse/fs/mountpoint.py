# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass, field
import json
from typing import AsyncIterator

from swh.fuse.fs.artifact import OBJTYPE_GETTERS, Origin
from swh.fuse.fs.entry import EntryMode, FuseDirEntry, FuseEntry, FuseFileEntry
from swh.model.exceptions import ValidationError
from swh.model.identifiers import CONTENT, SWHID, parse_swhid


@dataclass
class Root(FuseDirEntry):
    """ The FUSE mountpoint, consisting of the archive/ and meta/ directories """

    name: str = field(init=False, default=None)
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))
    depth: int = field(init=False, default=1)

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        yield self.create_child(ArchiveDir)
        yield self.create_child(MetaDir)
        yield self.create_child(OriginDir)


@dataclass
class ArchiveDir(FuseDirEntry):
    """ The archive/ directory is lazily populated with one entry per accessed
    SWHID, having actual SWHIDs as names """

    name: str = field(init=False, default="archive")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))

    def create_child(self, swhid: SWHID) -> FuseEntry:
        if swhid.object_type == CONTENT:
            mode = EntryMode.RDONLY_FILE
        else:
            mode = EntryMode.RDONLY_DIR
        return super().create_child(
            OBJTYPE_GETTERS[swhid.object_type],
            name=str(swhid),
            mode=int(mode),
            swhid=swhid,
        )

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        async for swhid in self.fuse.cache.get_cached_swhids():
            yield self.create_child(swhid)

    async def lookup(self, name: str) -> FuseEntry:
        entry = await super().lookup(name)
        if entry:
            return entry

        # On the fly mounting of a new artifact
        try:
            swhid = parse_swhid(name)
            await self.fuse.get_metadata(swhid)
            return self.create_child(swhid)
        except ValidationError:
            return None


@dataclass
class MetaDir(FuseDirEntry):
    """ The meta/ directory contains one SWHID.json file for each SWHID entry
    under archive/. The JSON file contain all available meta information about
    the given SWHID, as returned by the Software Heritage Web API for that
    object. Note that, in case of pagination (e.g., snapshot objects with many
    branches) the JSON file will contain a complete version with all pages
    merged together. """

    name: str = field(init=False, default="meta")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        async for swhid in self.fuse.cache.get_cached_swhids():
            yield self.create_child(
                MetaEntry,
                name=f"{swhid}.json",
                mode=int(EntryMode.RDONLY_FILE),
                swhid=swhid,
            )


@dataclass
class MetaEntry(FuseFileEntry):
    """ An entry from the meta/ directory, containing for each accessed SWHID a
    corresponding SWHID.json file with all the metadata from the Software
    Heritage archive. """

    swhid: SWHID

    async def get_content(self) -> bytes:
        # Get raw JSON metadata from API (un-typified)
        metadata = await self.fuse.cache.metadata.get(self.swhid, typify=False)
        json_str = json.dumps(metadata, indent=self.fuse.conf["json-indent"])
        return (json_str + "\n").encode()

    async def size(self) -> int:
        return len(await self.get_content())


@dataclass
class OriginDir(FuseDirEntry):
    """ The origin/ directory is lazily populated with one entry per accessed
    origin URL (mangled to create a valid UNIX filename). The URL encoding is
    done using the percent-encoding mechanism described in RFC 3986. """

    name: str = field(init=False, default="origin")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))

    def create_child(self, url_encoded: str) -> FuseEntry:
        return super().create_child(
            Origin, name=url_encoded, mode=int(EntryMode.RDONLY_DIR),
        )

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        async for url in self.fuse.cache.get_cached_visits():
            yield self.create_child(url)

    async def lookup(self, name: str) -> FuseEntry:
        entry = await super().lookup(name)
        if entry:
            return entry

        # On the fly mounting of new origin url
        try:
            url_encoded = name
            await self.fuse.get_visits(url_encoded)
            return self.create_child(url_encoded)
        except ValueError:
            return None
