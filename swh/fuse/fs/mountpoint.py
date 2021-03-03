# Copyright (C) 2020-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import AsyncIterator, Optional

from swh.fuse.fs.artifact import OBJTYPE_GETTERS, SWHID_REGEXP, Origin
from swh.fuse.fs.entry import (
    EntryMode,
    FuseDirEntry,
    FuseEntry,
    FuseFileEntry,
    FuseSymlinkEntry,
)
from swh.model.exceptions import ValidationError
from swh.model.hashutil import hash_to_hex
from swh.model.identifiers import CoreSWHID, ObjectType

JSON_SUFFIX = ".json"


@dataclass
class Root(FuseDirEntry):
    """ The FUSE mountpoint, consisting of the archive/ and origin/ directories """

    name: str = field(init=False, default="")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))
    depth: int = field(init=False, default=1)

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        yield self.create_child(ArchiveDir)
        yield self.create_child(OriginDir)
        yield self.create_child(CacheDir)
        yield self.create_child(Readme)


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

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        return
        yield

    async def lookup(self, name: str) -> Optional[FuseEntry]:
        # On the fly mounting of a new artifact
        try:
            if name.endswith(JSON_SUFFIX):
                swhid = CoreSWHID.from_string(name[: -len(JSON_SUFFIX)])
                return self.create_child(
                    MetaEntry,
                    name=f"{swhid}{JSON_SUFFIX}",
                    mode=int(EntryMode.RDONLY_FILE),
                    swhid=swhid,
                )
            else:
                swhid = CoreSWHID.from_string(name)
                await self.fuse.get_metadata(swhid)
                return self.create_child(
                    OBJTYPE_GETTERS[swhid.object_type],
                    name=str(swhid),
                    mode=int(
                        EntryMode.RDONLY_FILE
                        if swhid.object_type == ObjectType.CONTENT
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

    swhid: CoreSWHID

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

    def create_origin_child(self, url_encoded: str) -> FuseEntry:
        return super().create_child(
            Origin, name=url_encoded, mode=int(EntryMode.RDONLY_DIR),
        )

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        async for url in self.fuse.cache.get_cached_visits():
            yield self.create_origin_child(url)

    async def lookup(self, name: str) -> Optional[FuseEntry]:
        entry = await super().lookup(name)
        if entry:
            return entry

        # On the fly mounting of new origin url
        try:
            url_encoded = name
            await self.fuse.get_visits(url_encoded)
            return self.create_origin_child(url_encoded)
        except ValueError:
            return None


@dataclass
class CacheDir(FuseDirEntry):
    """ The cache/ directory is an on-disk representation of locally cached
    objects and metadata. Via this directory you can browse cached data and
    selectively remove them from the cache, freeing disk space. (See `swh fs
    clean` in the {ref}`CLI <swh-fuse-cli>` to completely empty the cache). The
    directory is populated with symlinks to: all artifacts, identified by their
    SWHIDs and sharded by the first two character of their object id, the
    metadata identified by a `SWHID.json` entry, and the `origin/` directory.
    """

    name: str = field(init=False, default="cache")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_DIR))

    ENTRIES_REGEXP = re.compile(r"^([a-f0-9]{2})|(" + OriginDir.name + ")$")

    @dataclass
    class ArtifactShardBySwhid(FuseDirEntry):
        ENTRIES_REGEXP = re.compile(r"^(" + SWHID_REGEXP + ")$")

        prefix: str = field(default="")

        async def compute_entries(self) -> AsyncIterator[FuseEntry]:
            root_path = self.get_relative_root_path()
            async for swhid in self.fuse.cache.get_cached_swhids():
                if not hash_to_hex(swhid.object_id).startswith(self.prefix):
                    continue

                yield self.create_child(
                    FuseSymlinkEntry,
                    name=str(swhid),
                    target=Path(root_path, f"archive/{swhid}"),
                )
                yield self.create_child(
                    FuseSymlinkEntry,
                    name=f"{swhid}{JSON_SUFFIX}",
                    target=Path(root_path, f"archive/{swhid}{JSON_SUFFIX}"),
                )

        async def unlink(self, name: str) -> None:
            try:
                if name.endswith(JSON_SUFFIX):
                    name = name[: -len(JSON_SUFFIX)]
                swhid = CoreSWHID.from_string(name)
                await self.fuse.cache.metadata.remove(swhid)
                await self.fuse.cache.blob.remove(swhid)
            except ValidationError:
                raise

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        prefixes = set()
        async for swhid in self.fuse.cache.get_cached_swhids():
            prefixes.add(hash_to_hex(swhid.object_id)[:2])

        for prefix in prefixes:
            yield self.create_child(
                CacheDir.ArtifactShardBySwhid,
                name=prefix,
                mode=int(EntryMode.RDWR_DIR),
                prefix=prefix,
            )

        yield self.create_child(
            FuseSymlinkEntry,
            name=OriginDir.name,
            target=Path(self.get_relative_root_path(), OriginDir.name),
        )


@dataclass
class Readme(FuseFileEntry):
    """ Top-level README to explain briefly what is SwhFS. """

    name: str = field(init=False, default="README")
    mode: int = field(init=False, default=int(EntryMode.RDONLY_FILE))

    CONTENT = """Welcome to the Software Heritage Filesystem (SwhFS)!

This is a user-space POSIX filesystem to browse the Software Heritage archive,
as if it were locally available. The SwhFS mount point contains 3 directories,
all initially empty and lazily populated:

- "archive": virtual directory to mount any Software Heritage artifact on the
  fly using its SWHID as name. Note: this directory cannot be listed with ls,
  but entries in it can be accessed (e.g., using cat or cd).
- "origin": virtual directory to mount any origin using its encoded URL as name.
- "cache": on-disk representation of locally cached objects and metadata.

Try it yourself:

    $ cat archive/swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2
    #include <stdio.h>

    int main(void) {
        printf("Hello, World!\\n");
    }

You can find more details and examples in the SwhFS online documentation:
https://docs.softwareheritage.org/devel/swh-fuse/ """

    async def get_content(self) -> bytes:
        return self.CONTENT.encode()
