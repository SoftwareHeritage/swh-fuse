# Copyright (C) 2020-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, AsyncIterator, Dict, List, Optional, cast

from swh.fuse.fs.entry import (
    EntryMode,
    FuseDirEntry,
    FuseEntry,
    FuseFileEntry,
    FuseSymlinkEntry,
)
from swh.model.from_disk import DentryPerms
from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.swhids import CoreSWHID, ObjectType

SWHID_REGEXP = r"swh:1:(cnt|dir|rel|rev|snp):[0-9a-f]{40}"


@dataclass
class Content(FuseFileEntry):
    """Software Heritage content artifact.

    Content leaves (AKA blobs) are represented on disks as regular files,
    containing the corresponding bytes, as archived.

    Note that permissions are associated to blobs only in the context of
    directories. Hence, when accessing blobs from the top-level `archive/`
    directory, the permissions of the `archive/SWHID` file will be arbitrary and
    not meaningful (e.g., `0x644`)."""

    swhid: CoreSWHID
    prefetch: Any = None
    """optional prefetched metadata used to set entry attributes"""

    async def get_content(self) -> bytes:
        data = await self.fuse.get_blob(self.swhid)
        if not self.prefetch:
            self.prefetch = {"length": len(data)}
        return data

    async def size(self) -> int:
        if self.prefetch:
            return self.prefetch["length"]
        else:
            return await super().size()


@dataclass
class Directory(FuseDirEntry):
    """Software Heritage directory artifact.

    Directory nodes are represented as directories on the file-system,
    containing one entry for each entry of the archived directory. Entry names
    and other metadata, including permissions, will correspond to the archived
    entry metadata.

    Note that the FUSE mount is read-only, no matter what the permissions say.
    So it is possible that, in the context of a directory, a file is presented
    as writable, whereas actually writing to it will fail with `EPERM`."""

    swhid: CoreSWHID

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        for entry in metadata:
            name = entry["name"]
            swhid = entry["target"]
            mode = (
                # Archived permissions for directories are always set to
                # 0o040000 so use a read-only permission instead
                int(EntryMode.RDONLY_DIR)
                if swhid.object_type == ObjectType.DIRECTORY
                else entry["perms"]
            )

            # 1. Symlink (check symlink first because condition is less restrictive)
            if mode == DentryPerms.symlink:
                target = b""
                try:
                    # Symlink target is stored in the blob content
                    target = await self.fuse.get_blob(swhid)
                except Exception:
                    pass  # Ignore error and create a (broken) symlink anyway

                yield self.create_child(
                    FuseSymlinkEntry,
                    name=name,
                    target=target,
                )
            # 2. Regular file
            elif swhid.object_type == ObjectType.CONTENT:
                yield self.create_child(
                    Content,
                    name=name,
                    mode=mode,
                    swhid=swhid,
                    # The directory API has extra info we can use to set
                    # attributes without additional Software Heritage API call
                    prefetch=entry,
                )
            # 3. Regular directory
            elif swhid.object_type == ObjectType.DIRECTORY:
                yield self.create_child(
                    Directory,
                    name=name,
                    mode=mode,
                    swhid=swhid,
                )
            # 4. Submodule
            elif swhid.object_type == ObjectType.REVISION:
                try:
                    # Make sure the revision metadata is fetched and create a
                    # symlink to distinguish it with regular directories
                    await self.fuse.get_metadata(swhid)
                except Exception:
                    pass  # Ignore error and create a (broken) symlink anyway

                yield self.create_child(
                    FuseSymlinkEntry,
                    name=name,
                    target=Path(self.get_relative_root_path(), f"archive/{swhid}"),
                )
            else:
                raise ValueError("Unknown directory entry type: {swhid.object_type}")


@dataclass
class Revision(FuseDirEntry):
    """Software Heritage revision artifact.

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
      in reverse topological order. The history can be listed through
      `by-date/`, `by-hash/` or `by-page/` with each its own sharding policy.
    - `meta.json`: metadata for the current node, as a symlink pointing to the
      relevant `archive/<SWHID>.json` file"""

    swhid: CoreSWHID

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
            target=Path(root_path, f"archive/{self.swhid}.json"),
        )
        yield self.create_child(
            RevisionParents,
            name="parents",
            mode=int(EntryMode.RDONLY_DIR),
            parents=[x["id"] for x in parents],
        )

        if len(parents) >= 1:
            yield self.create_child(
                FuseSymlinkEntry,
                name="parent",
                target="parents/1/",
            )

        yield self.create_child(
            RevisionHistory,
            name="history",
            mode=int(EntryMode.RDONLY_DIR),
            swhid=self.swhid,
        )


@dataclass
class RevisionParents(FuseDirEntry):
    """Revision virtual `parents/` directory"""

    parents: List[CoreSWHID]

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
    """Revision virtual `history/` directory"""

    swhid: CoreSWHID

    async def prefill_by_date_cache(self, by_date_dir: FuseDirEntry) -> None:
        history = await self.fuse.get_history(self.swhid)
        nb_api_calls = 0
        for swhid in history:
            cache = await self.fuse.cache.metadata.get(swhid)
            if cache:
                continue

            await self.fuse.get_metadata(swhid)
            # The by-date/ directory is cached temporarily in direntry, and
            # invalidated + updated every 100 API calls
            nb_api_calls += 1
            if nb_api_calls % 100 == 0:
                self.fuse.cache.direntry.invalidate(by_date_dir)
        # Make sure to have the latest entries once the prefilling is done
        self.fuse.cache.direntry.invalidate(by_date_dir)

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        by_date_dir = cast(
            RevisionHistoryShardByDate,
            self.create_child(
                RevisionHistoryShardByDate,
                name="by-date",
                mode=int(EntryMode.RDONLY_DIR),
                history_swhid=self.swhid,
            ),
        )

        # Run it concurrently because of the many API calls necessary
        asyncio.create_task(self.prefill_by_date_cache(by_date_dir))

        yield by_date_dir

        yield self.create_child(
            RevisionHistoryShardByHash,
            name="by-hash",
            mode=int(EntryMode.RDONLY_DIR),
            history_swhid=self.swhid,
        )

        yield self.create_child(
            RevisionHistoryShardByPage,
            name="by-page",
            mode=int(EntryMode.RDONLY_DIR),
            history_swhid=self.swhid,
        )


@dataclass
class RevisionHistoryShardByDate(FuseDirEntry):
    """Revision virtual `history/by-date` sharded directory"""

    history_swhid: CoreSWHID
    prefix: str = field(default="")
    is_status_done: bool = field(default=False)

    DATE_FMT = "{year:04d}/{month:02d}/{day:02d}/"
    ENTRIES_REGEXP = re.compile(r"^([0-9]{2,4})|(" + SWHID_REGEXP + ")$")

    @dataclass
    class StatusFile(FuseFileEntry):
        """Temporary file used to indicate loading progress in by-date/"""

        name: str = field(init=False, default=".status")
        mode: int = field(init=False, default=int(EntryMode.RDONLY_FILE))
        history_swhid: CoreSWHID

        def __post_init__(self):
            super().__post_init__()
            # This is the only case where we do not want the kernel to cache the file
            self.file_info_attrs["keep_cache"] = False
            self.file_info_attrs["direct_io"] = True

        async def get_content(self) -> bytes:
            history_full = await self.fuse.get_history(self.history_swhid)
            history_cached = await self.fuse.cache.history.get_with_date_prefix(
                self.history_swhid, date_prefix=""
            )
            fmt = f"Done: {len(history_cached)}/{len(history_full)}\n"
            return fmt.encode()

    def __post_init__(self):
        super().__post_init__()
        # Create the status file only once so we can easily remove it when the
        # entire history is fetched
        self.status_file = self.create_child(
            RevisionHistoryShardByDate.StatusFile, history_swhid=self.history_swhid
        )

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        history_full = await self.fuse.get_history(self.history_swhid)
        # Only check for cached revisions with the appropriate prefix, since
        # fetching all of them with the Web API would take too long
        history_cached = await self.fuse.cache.history.get_with_date_prefix(
            self.history_swhid, date_prefix=self.prefix
        )

        depth = self.prefix.count("/")
        root_path = self.get_relative_root_path()
        sharded_dirs = set()

        for swhid, sharded_name in history_cached:
            if not sharded_name.startswith(self.prefix):
                continue

            if depth == 3:
                yield self.create_child(
                    FuseSymlinkEntry,
                    name=str(swhid),
                    target=Path(root_path, f"archive/{swhid}"),
                )
            # Create sharded directories
            else:
                next_prefix = sharded_name.split("/")[depth]
                if next_prefix not in sharded_dirs:
                    sharded_dirs.add(next_prefix)
                    yield self.create_child(
                        RevisionHistoryShardByDate,
                        name=next_prefix,
                        mode=int(EntryMode.RDONLY_DIR),
                        prefix=f"{self.prefix}{next_prefix}/",
                        history_swhid=self.history_swhid,
                    )

        self.is_status_done = len(history_cached) == len(history_full)
        if self.is_status_done:
            self.fuse._remove_inode(self.status_file.inode)
        elif not self.is_status_done and depth == 0:
            yield self.status_file


@dataclass
class RevisionHistoryShardByHash(FuseDirEntry):
    """Revision virtual `history/by-hash` sharded directory"""

    history_swhid: CoreSWHID
    prefix: str = field(default="")

    SHARDING_LENGTH = 2
    ENTRIES_REGEXP = re.compile(r"^([a-f0-9]+)|(" + SWHID_REGEXP + ")$")

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        history = await self.fuse.get_history(self.history_swhid)

        if self.prefix:
            root_path = self.get_relative_root_path()
            for swhid in history:
                if swhid.object_id.startswith(hash_to_bytes(self.prefix)):
                    yield self.create_child(
                        FuseSymlinkEntry,
                        name=str(swhid),
                        target=Path(root_path, f"archive/{swhid}"),
                    )
        # Create sharded directories
        else:
            sharded_dirs = set()
            for swhid in history:
                next_prefix = hash_to_hex(swhid.object_id)[: self.SHARDING_LENGTH]
                if next_prefix not in sharded_dirs:
                    sharded_dirs.add(next_prefix)
                    yield self.create_child(
                        RevisionHistoryShardByHash,
                        name=next_prefix,
                        mode=int(EntryMode.RDONLY_DIR),
                        prefix=next_prefix,
                        history_swhid=self.history_swhid,
                    )


@dataclass
class RevisionHistoryShardByPage(FuseDirEntry):
    """Revision virtual `history/by-page` sharded directory"""

    history_swhid: CoreSWHID
    prefix: Optional[int] = field(default=None)

    PAGE_SIZE = 10_000
    PAGE_FMT = "{page_number:03d}"
    ENTRIES_REGEXP = re.compile(r"^([0-9]+)|(" + SWHID_REGEXP + ")$")

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        history = await self.fuse.get_history(self.history_swhid)

        if self.prefix is not None:
            current_page = self.prefix
            root_path = self.get_relative_root_path()
            max_idx = min(len(history), (current_page + 1) * self.PAGE_SIZE)
            for i in range(current_page * self.PAGE_SIZE, max_idx):
                swhid = history[i]
                yield self.create_child(
                    FuseSymlinkEntry,
                    name=str(swhid),
                    target=Path(root_path, f"archive/{swhid}"),
                )
        # Create sharded directories
        else:
            for i in range(0, len(history), self.PAGE_SIZE):
                page_number = i // self.PAGE_SIZE
                yield self.create_child(
                    RevisionHistoryShardByPage,
                    name=self.PAGE_FMT.format(page_number=page_number),
                    mode=int(EntryMode.RDONLY_DIR),
                    history_swhid=self.history_swhid,
                    prefix=page_number,
                )


@dataclass
class Release(FuseDirEntry):
    """Software Heritage release artifact.

    Release nodes are represented on the file-system as directories with the
    following entries:

    - `target`: target node, as a symlink to `archive/<SWHID>`
    - `target_type`: regular file containing the type of the target SWHID
    - `root`: present if and only if the release points to something that
      (transitively) resolves to a directory. When present it is a symlink
      pointing into `archive/` to the SWHID of the given directory
    - `meta.json`: metadata for the current node, as a symlink pointing to the
      relevant `archive/<SWHID>.json` file"""

    swhid: CoreSWHID

    async def find_root_directory(self, swhid: CoreSWHID) -> Optional[CoreSWHID]:
        if swhid.object_type == ObjectType.RELEASE:
            metadata = await self.fuse.get_metadata(swhid)
            return await self.find_root_directory(metadata["target"])
        elif swhid.object_type == ObjectType.REVISION:
            metadata = await self.fuse.get_metadata(swhid)
            return metadata["directory"]
        elif swhid.object_type == ObjectType.DIRECTORY:
            return swhid
        else:
            return None

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        root_path = self.get_relative_root_path()

        yield self.create_child(
            FuseSymlinkEntry,
            name="meta.json",
            target=Path(root_path, f"archive/{self.swhid}.json"),
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
    """Release type virtual file"""

    target_type: ObjectType

    async def get_content(self) -> bytes:
        return str.encode(self.target_type.name.lower() + "\n")


@dataclass
class Snapshot(FuseDirEntry):
    """Software Heritage snapshot artifact.

    Snapshot nodes are represented on the file-system as recursive directories
    following the branch names structure. For example, a branch named
    ``refs/tags/v1.0`` will be represented as a ``refs`` directory containing a
    ``tags`` directory containing a ``v1.0`` symlink pointing to the branch
    target SWHID."""

    swhid: CoreSWHID
    prefix: str = field(default="")

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        metadata = await self.fuse.get_metadata(self.swhid)
        root_path = self.get_relative_root_path()

        subdirs = set()
        for branch_name, branch_meta in metadata.items():
            if not branch_name.startswith(self.prefix):
                continue

            next_subdirs = branch_name[len(self.prefix) :].split("/")
            next_prefix = next_subdirs[0]

            if len(next_subdirs) == 1:
                # Non-alias targets are symlinks to their corresponding archived
                # artifact, whereas alias targets are relative symlinks to the
                # corresponding snapshot directory entry.
                target_type = branch_meta["target_type"]
                target_raw = branch_meta["target"]
                if target_type == "alias":
                    prefix = Path(branch_name).parent
                    target = os.path.relpath(target_raw, prefix)
                else:
                    target = f"{root_path}/archive/{target_raw}"

                yield self.create_child(
                    FuseSymlinkEntry,
                    name=next_prefix,
                    target=Path(target),
                )
            else:
                subdirs.add(next_prefix)

        for subdir in subdirs:
            yield self.create_child(
                Snapshot,
                name=subdir,
                mode=int(EntryMode.RDONLY_DIR),
                swhid=self.swhid,
                prefix=f"{self.prefix}{subdir}/",
            )


@dataclass
class Origin(FuseDirEntry):
    """Software Heritage origin artifact.

    Origin nodes are represented on the file-system as directories with one
    entry for each origin visit.

    The visits directories are named after the visit date (`YYYY-MM-DD`, if
    multiple visits occur the same day only the first one is kept). Each visit
    directory contains a `meta.json` with associated metadata for the origin
    node, and potentially a `snapshot` symlink pointing to the visit's snapshot
    node."""

    DATE_FMT = "{year:04d}-{month:02d}-{day:02d}"
    ENTRIES_REGEXP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        # The origin's name is always its URL (encoded to create a valid UNIX filename)
        visits = await self.fuse.get_visits(self.name)

        seen_date = set()
        for visit in visits:
            date = visit["date"]
            name = self.DATE_FMT.format(year=date.year, month=date.month, day=date.day)

            if name in seen_date:
                logging.debug(
                    "Conflict date on origin: %s, %s", visit["origin"], str(name)
                )
            else:
                seen_date.add(name)
                yield self.create_child(
                    OriginVisit,
                    name=name,
                    mode=int(EntryMode.RDONLY_DIR),
                    meta=visit,
                )


@dataclass
class OriginVisit(FuseDirEntry):
    """Origin visit virtual directory"""

    meta: Dict[str, Any]

    @dataclass
    class MetaFile(FuseFileEntry):
        content: str

        async def get_content(self) -> bytes:
            return str.encode(self.content + "\n")

    async def compute_entries(self) -> AsyncIterator[FuseEntry]:
        snapshot_swhid = self.meta["snapshot"]
        if snapshot_swhid:
            root_path = self.get_relative_root_path()
            yield self.create_child(
                FuseSymlinkEntry,
                name="snapshot",
                target=Path(root_path, f"archive/{snapshot_swhid}"),
            )

        yield self.create_child(
            OriginVisit.MetaFile,
            name="meta.json",
            mode=int(EntryMode.RDONLY_FILE),
            content=json.dumps(
                self.meta,
                indent=self.fuse.conf["json-indent"],
                default=lambda x: str(x),
            ),
        )


OBJTYPE_GETTERS = {
    ObjectType.CONTENT: Content,
    ObjectType.DIRECTORY: Directory,
    ObjectType.REVISION: Revision,
    ObjectType.RELEASE: Release,
    ObjectType.SNAPSHOT: Snapshot,
}
