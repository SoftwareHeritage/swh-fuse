# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from stat import S_IFDIR, S_IFLNK, S_IFREG
from typing import Any, AsyncIterator, Union

# Avoid cycling import
Fuse = "Fuse"


class EntryMode(IntEnum):
    """ Default entry mode and permissions for the FUSE.

    The FUSE mount is always read-only, even if permissions contradict this
    statement (in a context of a directory, entries are listed with permissions
    taken from the archive).
    """

    RDONLY_FILE = S_IFREG | 0o444
    RDONLY_DIR = S_IFDIR | 0o555
    SYMLINK = S_IFLNK | 0o444


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

    def __post_init__(self):
        self.inode = self.fuse._alloc_inode(self)

    async def get_content(self) -> bytes:
        """ Return the content of a file entry """

        return None

    async def size(self) -> int:
        """ Return the size of a file entry """

        return 0

    async def __aiter__(self) -> AsyncIterator[FuseEntry]:
        """ Return the child entries of a directory entry """

        yield None

    def get_target(self) -> Union[str, bytes, Path]:
        """ Return the path target of a symlink entry """

        return None

    def get_relative_root_path(self) -> str:
        return "../" * (self.depth - 1)

    def create_child(self, constructor: Any, **kwargs) -> FuseEntry:
        return constructor(depth=self.depth + 1, fuse=self.fuse, **kwargs)
