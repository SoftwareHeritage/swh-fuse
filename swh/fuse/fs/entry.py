# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from enum import IntEnum
from stat import S_IFDIR, S_IFREG

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


class FuseEntry:
    """ Main wrapper class to manipulate virtual FUSE entries

    Attributes:
        name: entry filename
        mode: entry permission mode
        fuse: internal reference to the main FUSE class
        inode: unique integer identifying the entry
    """

    def __init__(self, name: str, mode: int, fuse: Fuse):
        self.name = name
        self.mode = mode
        self.fuse = fuse
        self.inode = fuse._alloc_inode(self)

    async def length(self) -> int:
        return 0

    async def content(self):
        return None

    async def __aiter__(self):
        return None
