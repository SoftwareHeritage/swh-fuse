# Copyright (C) 2020-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
import re
from stat import S_IFDIR, S_IFLNK, S_IFREG
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, Optional, Pattern, Union

if TYPE_CHECKING:  # avoid cyclic import
    from swh.fuse.fuse import Fuse


class EntryMode(IntEnum):
    """ Default entry mode and permissions for the FUSE.

    The FUSE mount is always read-only, even if permissions contradict this
    statement (in a context of a directory, entries are listed with permissions
    taken from the archive).
    """

    RDONLY_FILE = S_IFREG | 0o444
    RDONLY_DIR = S_IFDIR | 0o555
    RDONLY_LNK = S_IFLNK | 0o444

    # `cache/` sub-directories need the write permission in order to invalidate
    # cached artifacts using `rm {SWHID}`
    RDWR_DIR = S_IFDIR | 0o755


@dataclass
class FuseEntry:
    """ Main wrapper class to manipulate virtual FUSE entries

    Attributes:
        name: entry filename
        mode: entry permission mode
        fuse: internal reference to the main FUSE class
        inode: unique integer identifying the entry
    """

    name: str
    mode: int
    depth: int
    fuse: Fuse
    inode: int = field(init=False)
    file_info_attrs: Dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.inode = self.fuse._alloc_inode(self)
        # By default, let the kernel cache previously accessed data
        self.file_info_attrs["keep_cache"] = True

    async def size(self) -> int:
        """ Return the size (in bytes) of an entry """

        raise NotImplementedError

    async def unlink(self, name: str) -> None:
        raise NotImplementedError

    def get_relative_root_path(self) -> str:
        return "../" * (self.depth - 1)

    def create_child(self, constructor: Any, **kwargs) -> FuseEntry:
        return constructor(depth=self.depth + 1, fuse=self.fuse, **kwargs)


@dataclass
class FuseFileEntry(FuseEntry):
    """ FUSE virtual file entry """

    async def get_content(self) -> bytes:
        """ Return the content of a file entry """

        raise NotImplementedError

    async def size(self) -> int:
        return len(await self.get_content())


@dataclass
class FuseDirEntry(FuseEntry):
    """ FUSE virtual directory entry """

    ENTRIES_REGEXP: Optional[Pattern] = field(init=False, default=None)

    async def size(self) -> int:
        return 0

    def validate_entry(self, name: str) -> bool:
        """ Return true if the name matches the directory entries regular
        expression, and false otherwise """

        if self.ENTRIES_REGEXP:
            return bool(re.match(self.ENTRIES_REGEXP, name))
        else:
            return True

    async def compute_entries(self):
        """ Return the child entries of a directory entry """

        raise NotImplementedError

    async def get_entries(self, offset: int = 0) -> AsyncIterator[FuseEntry]:
        """ Return the child entries of a directory entry using direntry cache """

        cache = self.fuse.cache.direntry.get(self)
        if cache:
            entries = cache
        else:
            entries = [x async for x in self.compute_entries()]
            self.fuse.cache.direntry.set(self, entries)

        # Avoid copy by manual iteration (instead of slicing) and use of a
        # generator (instead of returning the full list every time)
        for i in range(offset, len(entries)):
            yield entries[i]

    async def lookup(self, name: str) -> Optional[FuseEntry]:
        """ Look up a FUSE entry by name """

        async for entry in self.get_entries():
            if entry.name == name:
                return entry
        return None


@dataclass
class FuseSymlinkEntry(FuseEntry):
    """ FUSE virtual symlink entry

    Attributes:
        target: path to symlink target
    """

    mode: int = field(init=False, default=int(EntryMode.RDONLY_LNK))
    target: Union[str, bytes, Path]

    async def size(self) -> int:
        return len(str(self.target))

    def get_target(self) -> Union[str, bytes, Path]:
        """ Return the path target of a symlink entry """

        return self.target
