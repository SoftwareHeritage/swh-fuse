# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, List

from swh.fuse.fs.entry import EntryMode, FuseEntry
from swh.fuse.fs.symlink import SymlinkEntry
from swh.model.from_disk import DentryPerms
from swh.model.identifiers import CONTENT, DIRECTORY, REVISION, SWHID


@dataclass
class ArtifactEntry(FuseEntry):
    """ FUSE virtual entry for a Software Heritage Artifact

    Attributes:
        swhid: Software Heritage persistent identifier
        prefetch: optional prefetched metadata used to set entry attributes
    """

    swhid: SWHID
    prefetch: Any = None


class Content(ArtifactEntry):
    """ Software Heritage content artifact.

    Content leaves (AKA blobs) are represented on disks as regular files,
    containing the corresponding bytes, as archived.

    Note that permissions are associated to blobs only in the context of
    directories. Hence, when accessing blobs from the top-level `archive/`
    directory, the permissions of the `archive/SWHID` file will be arbitrary and
    not meaningful (e.g., `0x644`). """

    async def get_content(self) -> bytes:
        data = await self.fuse.get_blob(self.swhid)
        if not self.prefetch:
            self.prefetch = {"length": len(data)}
        return data

    async def size(self) -> int:
        if self.prefetch:
            return self.prefetch["length"]
        else:
            return len(await self.get_content())

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

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        for entry in metadata:
            name = entry["name"]
            swhid = entry["target"]
            mode = (
                # Archived permissions for directories are always set to
                # 0o040000 so use a read-only permission instead
                int(EntryMode.RDONLY_DIR)
                if swhid.object_type == DIRECTORY
                else entry["perms"]
            )

            # 1. Symlinks
            if mode == DentryPerms.symlink:
                yield self.create_child(
                    SymlinkEntry,
                    name=name,
                    # Symlink target is stored in the blob content
                    target=await self.fuse.get_blob(swhid),
                )
            # 2. Submodules
            elif swhid.object_type == REVISION:
                # Make sure the revision metadata is fetched and create a
                # symlink to distinguish it with regular directories
                await self.fuse.get_metadata(swhid)
                yield self.create_child(
                    SymlinkEntry,
                    name=name,
                    target=Path(self.get_relative_root_path(), f"archive/{swhid}"),
                )
            # 3. Regular entries (directories, contents)
            else:
                yield self.create_child(
                    OBJTYPE_GETTERS[swhid.object_type],
                    name=name,
                    mode=mode,
                    swhid=swhid,
                    # The directory API has extra info we can use to set
                    # attributes without additional Software Heritage API call
                    prefetch=entry,
                )


class Revision(ArtifactEntry):
    """ Software Heritage revision artifact.

    Revision (AKA commit) nodes are represented on the file-system as
    directories with the following entries:

    - `root`: source tree at the time of the commit, as a symlink pointing into
      `archive/`, to a SWHID of type `dir`
    - `parents/` (note the plural): a virtual directory containing entries named
      `1`, `2`, `3`, etc., one for each parent commit. Each of these entry is a
      symlink pointing into `archive/`, to the SWHID file for the given parent
      commit
    - `parent` (note the singular): present if and only if the current commit
      has at least one parent commit (which is the most common case). When
      present it is a symlink pointing into `parents/1/`
    - `meta.json`: metadata for the current node, as a symlink pointing to the
      relevant `meta/<SWHID>.json` file """

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        directory = metadata["directory"]
        parents = metadata["parents"]

        # Make sure all necessary metadatas are fetched
        await self.fuse.get_metadata(directory)
        for parent in parents:
            await self.fuse.get_metadata(parent["id"])

        root_path = self.get_relative_root_path()

        yield self.create_child(
            SymlinkEntry, name="root", target=Path(root_path, f"archive/{directory}"),
        )
        yield self.create_child(
            SymlinkEntry,
            name="meta.json",
            target=Path(root_path, f"meta/{self.swhid}.json"),
        )
        yield self.create_child(
            RevisionParents,
            name="parents",
            mode=int(EntryMode.RDONLY_DIR),
            parents=[x["id"] for x in parents],
        )

        if len(parents) >= 1:
            yield self.create_child(
                SymlinkEntry, name="parent", target="parents/1/",
            )


@dataclass
class RevisionParents(FuseEntry):
    """ Revision virtual `parents/` directory """

    parents: List[SWHID]

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        root_path = self.get_relative_root_path()
        for i, parent in enumerate(self.parents):
            yield self.create_child(
                SymlinkEntry,
                name=str(i + 1),
                target=Path(root_path, f"archive/{parent}"),
            )


OBJTYPE_GETTERS = {CONTENT: Content, DIRECTORY: Directory, REVISION: Revision}
