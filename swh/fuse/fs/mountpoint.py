# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass, field
import json
import re
from typing import AsyncIterator

from swh.fuse.fs.artifact import OBJTYPE_GETTERS, SWHID_REGEXP, Origin
from swh.fuse.fs.entry import EntryMode, FuseDirEntry, FuseEntry, FuseFileEntry
from swh.model.exceptions import ValidationError
from swh.model.identifiers import CONTENT, SWHID, parse_swhid


@dataclass
class Root(FuseDirEntry):
    """ The FUSE mountpoint, consisting of the archive/ and origin/ directories """

    name: str = field(init=False, default=None)
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))
    depth: int = field(init=False, default=1)

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        yield self.create_child(ArchiveDir)
        yield self.create_child(OriginDir)


@dataclass
class ArchiveDir(FuseDirEntry):
    """ The `archive/` virtual directory allows to mount any artifact on the fly
    using its SWHID as name. The associated metadata of the artifact from the
    Software Heritage Web API can also be accessed through the `SWHID.json` file
    (in case of pagination, the JSON file will contain a complete version with
    all pages merged together). Note: the archive directory cannot be listed
    with ls, but entries in it can be accessed (e.g., using cat or cd). """

    name: str = field(init=False, default="archive")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))

    ENTRIES_REGEXP = re.compile(r"^(" + SWHID_REGEXP + ")(.json)?$")
    JSON_SUFFIX = ".json"

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        return
        yield

    async def lookup(self, name: str) -> FuseEntry:
        # On the fly mounting of a new artifact
        try:
            if name.endswith(self.JSON_SUFFIX):
                swhid = parse_swhid(name[: -len(self.JSON_SUFFIX)])
                return self.create_child(
                    MetaEntry,
                    name=f"{swhid}{self.JSON_SUFFIX}",
                    mode=int(EntryMode.RDONLY_FILE),
                    swhid=swhid,
                )
            else:
                swhid = parse_swhid(name)
                await self.fuse.get_metadata(swhid)
                return self.create_child(
                    OBJTYPE_GETTERS[swhid.object_type],
                    name=str(swhid),
                    mode=int(
                        EntryMode.RDONLY_FILE
                        if swhid.object_type == CONTENT
                        else EntryMode.RDONLY_DIR
                    ),
                    swhid=swhid,
                )
        except ValidationError:
            return None


@dataclass
class MetaEntry(FuseFileEntry):
    """ An entry for a `archive/<SWHID>.json` file, containing all the SWHID's
    metadata from the Software Heritage archive. """

    swhid: SWHID

    async def get_content(self) -> bytes:
        # Make sure the metadata is in cache
        await self.fuse.get_metadata(self.swhid)
        # Retrieve raw JSON metadata from cache (un-typified)
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

    ENTRIES_REGEXP = re.compile(r"^.*%3A.*$")  # %3A is the encoded version of ':'

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
