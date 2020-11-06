# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, List
import urllib.parse

from swh.fuse.fs.entry import (
    EntryMode,
    FuseDirEntry,
    FuseEntry,
    FuseFileEntry,
    FuseSymlinkEntry,
)
from swh.model.from_disk import DentryPerms
from swh.model.identifiers import CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT, SWHID


@dataclass
class Content(FuseFileEntry):
    """ Software Heritage content artifact.

    Attributes:
        swhid: Software Heritage persistent identifier
        prefetch: optional prefetched metadata used to set entry attributes

    Content leaves (AKA blobs) are represented on disks as regular files,
    containing the corresponding bytes, as archived.

    Note that permissions are associated to blobs only in the context of
    directories. Hence, when accessing blobs from the top-level `archive/`
    directory, the permissions of the `archive/SWHID` file will be arbitrary and
    not meaningful (e.g., `0x644`). """

    swhid: SWHID
    prefetch: Any = None

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


@dataclass
class Directory(FuseDirEntry):
    """ Software Heritage directory artifact.

    Attributes:
        swhid: Software Heritage persistent identifier

    Directory nodes are represented as directories on the file-system,
    containing one entry for each entry of the archived directory. Entry names
    and other metadata, including permissions, will correspond to the archived
    entry metadata.

    Note that the FUSE mount is read-only, no matter what the permissions say.
    So it is possible that, in the context of a directory, a file is presented
    as writable, whereas actually writing to it will fail with `EPERM`. """

    swhid: SWHID

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
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

            # 1. Regular file
            if swhid.object_type == CONTENT:
                yield self.create_child(
                    Content,
                    name=name,
                    mode=mode,
                    swhid=swhid,
                    # The directory API has extra info we can use to set
                    # attributes without additional Software Heritage API call
                    prefetch=entry,
                )
            # 2. Regular directory
            elif swhid.object_type == DIRECTORY:
                yield self.create_child(
                    Directory, name=name, mode=mode, swhid=swhid,
                )
            # 3. Symlink
            elif mode == DentryPerms.symlink:
                yield self.create_child(
                    FuseSymlinkEntry,
                    name=name,
                    # Symlink target is stored in the blob content
                    target=await self.fuse.get_blob(swhid),
                )
            # 4. Submodule
            elif swhid.object_type == REVISION:
                # Make sure the revision metadata is fetched and create a
                # symlink to distinguish it with regular directories
                await self.fuse.get_metadata(swhid)
                yield self.create_child(
                    FuseSymlinkEntry,
                    name=name,
                    target=Path(self.get_relative_root_path(), f"archive/{swhid}"),
                )
            else:
                raise ValueError("Unknown directory entry type: {swhid.object_type}")


@dataclass
class Revision(FuseDirEntry):
    """ Software Heritage revision artifact.

    Attributes:
        swhid: Software Heritage persistent identifier

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
    - `history`: a virtual directory listing all its revision ancestors, sorted
      in reverse topological order. Each entry is a symlink pointing into
      `archive/SWHID`.
    - `meta.json`: metadata for the current node, as a symlink pointing to the
      relevant `meta/<SWHID>.json` file """

    swhid: SWHID

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        directory = metadata["directory"]
        parents = metadata["parents"]

        root_path = self.get_relative_root_path()

        yield self.create_child(
            FuseSymlinkEntry,
            name="root",
            target=Path(root_path, f"archive/{directory}"),
        )
        yield self.create_child(
            FuseSymlinkEntry,
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
                FuseSymlinkEntry, name="parent", target="parents/1/",
            )

        yield self.create_child(
            RevisionHistory,
            name="history",
            mode=int(EntryMode.RDONLY_DIR),
            swhid=self.swhid,
        )


@dataclass
class RevisionParents(FuseDirEntry):
    """ Revision virtual `parents/` directory """

    parents: List[SWHID]

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        root_path = self.get_relative_root_path()
        for i, parent in enumerate(self.parents):
            yield self.create_child(
                FuseSymlinkEntry,
                name=str(i + 1),
                target=Path(root_path, f"archive/{parent}"),
            )


@dataclass
class RevisionHistory(FuseDirEntry):
    """ Revision virtual `history/` directory """

    swhid: SWHID

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        history = await self.fuse.get_history(self.swhid)
        by_hash = self.create_child(
            RevisionHistoryShardByHash,
            name="by-hash",
            mode=int(EntryMode.RDONLY_DIR),
            history_swhid=self.swhid,
        )
        by_hash.fill_direntry_cache(history)
        yield by_hash


@dataclass
class RevisionHistoryShardByHash(FuseDirEntry):
    """ Revision virtual `history/by-hash` sharded directory """

    history_swhid: SWHID
    prefix: str = field(default="")

    def get_full_sharded_name(self, swhid: SWHID) -> str:
        sharding_depth = self.fuse.conf["sharding"]["depth"]
        sharding_length = self.fuse.conf["sharding"]["length"]
        if sharding_depth <= 0:
            return str(swhid)
        else:
            basename = swhid.object_id
            parts = [
                basename[i * sharding_length : (i + 1) * sharding_length]
                for i in range(sharding_depth)
            ]
            # Always keep the full SWHID as the path basename (otherwise we
            # loose the SWHID object type information)
            parts.append(str(swhid))
            path = Path(*parts)
            return str(path)

    def fill_direntry_cache(self, swhids: List[SWHID]):
        sharding_depth = self.fuse.conf["sharding"]["depth"]
        sharding_length = self.fuse.conf["sharding"]["length"]
        depth = self.prefix.count("/")
        children = []
        if depth == sharding_depth:
            root_path = self.get_relative_root_path()
            for swhid in swhids:
                children.append(
                    self.create_child(
                        FuseSymlinkEntry,
                        name=str(swhid),
                        target=Path(root_path, f"archive/{swhid}"),
                    )
                )
        else:
            subdirs = {}
            prefix_len = len(self.prefix)
            for swhid in swhids:
                name = self.get_full_sharded_name(swhid)
                next_prefix = name[prefix_len : prefix_len + sharding_length]
                subdirs.setdefault(next_prefix, []).append(swhid)

            # Recursive intermediate sharded directories
            for subdir, subentries in subdirs.items():
                child_prefix = f"{self.prefix}{subdir}/"
                child = self.create_child(
                    RevisionHistoryShardByHash,
                    name=subdir,
                    mode=int(EntryMode.RDONLY_DIR),
                    prefix=child_prefix,
                    history_swhid=self.history_swhid,
                )
                children.append(child)
                child.fill_direntry_cache(subentries)
        self.fuse.cache.direntry.set(self, children)
        return children

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        history = await self.fuse.get_history(self.history_swhid)
        hash_prefix = self.prefix.replace("/", "")
        swhids = [s for s in history if s.object_id.startswith(hash_prefix)]

        for entry in self.fill_direntry_cache(swhids):
            yield entry


@dataclass
class Release(FuseDirEntry):
    """ Software Heritage release artifact.

    Attributes:
        swhid: Software Heritage persistent identifier

    Release nodes are represented on the file-system as directories with the
    following entries:

    - `target`: target node, as a symlink to `archive/<SWHID>`
    - `target_type`: regular file containing the type of the target SWHID
    - `root`: present if and only if the release points to something that
      (transitively) resolves to a directory. When present it is a symlink
      pointing into `archive/` to the SWHID of the given directory
    - `meta.json`: metadata for the current node, as a symlink pointing to the
      relevant `meta/<SWHID>.json` file """

    swhid: SWHID

    async def find_root_directory(self, swhid: SWHID) -> SWHID:
        if swhid.object_type == RELEASE:
            metadata = await self.fuse.get_metadata(swhid)
            return await self.find_root_directory(metadata["target"])
        elif swhid.object_type == REVISION:
            metadata = await self.fuse.get_metadata(swhid)
            return metadata["directory"]
        elif swhid.object_type == DIRECTORY:
            return swhid
        else:
            return None

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        root_path = self.get_relative_root_path()

        yield self.create_child(
            FuseSymlinkEntry,
            name="meta.json",
            target=Path(root_path, f"meta/{self.swhid}.json"),
        )

        target = metadata["target"]
        yield self.create_child(
            FuseSymlinkEntry, name="target", target=Path(root_path, f"archive/{target}")
        )
        yield self.create_child(
            ReleaseType,
            name="target_type",
            mode=int(EntryMode.RDONLY_FILE),
            target_type=target.object_type,
        )

        target_dir = await self.find_root_directory(target)
        if target_dir is not None:
            yield self.create_child(
                FuseSymlinkEntry,
                name="root",
                target=Path(root_path, f"archive/{target_dir}"),
            )


@dataclass
class ReleaseType(FuseFileEntry):
    """ Release type virtual file """

    target_type: str

    async def get_content(self) -> bytes:
        return str.encode(self.target_type + "\n")

    async def size(self) -> int:
        return len(await self.get_content())


@dataclass
class Snapshot(FuseDirEntry):
    """ Software Heritage snapshot artifact.

    Attributes:
        swhid: Software Heritage persistent identifier

    Snapshot nodes are represented on the file-system as directories with one
    entry for each branch in the snapshot. Each entry is a symlink pointing into
    `archive/` to the branch target SWHID. Branch names are URL encoded (hence
    '/' are replaced with '%2F'). """

    swhid: SWHID

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        root_path = self.get_relative_root_path()

        for branch_name, branch_meta in metadata.items():
            # Mangle branch name to create a valid UNIX filename
            name = urllib.parse.quote_plus(branch_name)
            yield self.create_child(
                FuseSymlinkEntry,
                name=name,
                target=Path(root_path, f"archive/{branch_meta['target']}"),
            )


OBJTYPE_GETTERS = {
    CONTENT: Content,
    DIRECTORY: Directory,
    REVISION: Revision,
    RELEASE: Release,
    SNAPSHOT: Snapshot,
}
