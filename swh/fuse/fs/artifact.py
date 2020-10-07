# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, AsyncIterator

from swh.fuse.fs.entry import EntryMode, FuseEntry
from swh.model.identifiers import CONTENT, DIRECTORY, SWHID

# Avoid cycling import
Fuse = "Fuse"


class ArtifactEntry(FuseEntry):
    """ FUSE virtual entry for a Software Heritage Artifact

    Attributes:
        swhid: Software Heritage persistent identifier
        prefetch: optional prefetched metadata used to set entry attributes
    """

    def __init__(
        self, name: str, mode: int, fuse: Fuse, swhid: SWHID, prefetch: Any = None
    ):
        super().__init__(name, mode, fuse)
        self.swhid = swhid
        self.prefetch = prefetch


def typify(
    name: str, mode: int, fuse: Fuse, swhid: SWHID, prefetch: Any = None
) -> ArtifactEntry:
    """ Create an artifact entry corresponding to the given artifact type """

    getters = {CONTENT: Content, DIRECTORY: Directory}
    return getters[swhid.object_type](name, mode, fuse, swhid, prefetch)


class Content(ArtifactEntry):
    """ Software Heritage content artifact.

    Content leaves (AKA blobs) are represented on disks as regular files,
    containing the corresponding bytes, as archived.

    Note that permissions are associated to blobs only in the context of
    directories. Hence, when accessing blobs from the top-level `archive/`
    directory, the permissions of the `archive/SWHID` file will be arbitrary and
    not meaningful (e.g., `0x644`). """

    async def content(self) -> bytes:
        return await self.fuse.get_blob(self.swhid)

    async def length(self) -> int:
        # When listing entries from a directory, the API already gave us information
        if self.prefetch:
            return self.prefetch["length"]
        return len(await self.content())

    async def __aiter__(self):
        raise ValueError("Cannot iterate over a content type artifact")


class Directory(ArtifactEntry):
    """ Software Heritage directory artifact.

    Directory nodes are represented as directories on the file-system,
    containing one entry for each entry of the archived directory. Entry names
    and other metadata, including permissions, will correspond to the archived
    entry metadata.

    Note that the FUSE mount is read-only, no matter what the permissions say.
    So it is possible that, in the context of a directory, a file is presented
    as writable, whereas actually writing to it will fail with `EPERM`. """

    async def __aiter__(self) -> AsyncIterator[ArtifactEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        for entry in metadata:
            yield typify(
                name=entry["name"],
                # Use default read-only permissions for directories, and
                # archived permissions for contents
                mode=(
                    entry["perms"]
                    if entry["target"].object_type == CONTENT
                    else int(EntryMode.RDONLY_DIR)
                ),
                fuse=self.fuse,
                swhid=entry["target"],
                # The directory API has extra info we can use to set attributes
                # without additional Software Heritage API call
                prefetch=entry,
            )
