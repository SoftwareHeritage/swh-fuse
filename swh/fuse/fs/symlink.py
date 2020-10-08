# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from swh.fuse.fs.entry import EntryMode, FuseEntry


@dataclass
class SymlinkEntry(FuseEntry):
    """ FUSE virtual entry for symlinks

    Attributes:
        target: path to symlink target
    """

    mode: int = field(init=False, default=int(EntryMode.SYMLINK))
    target: Union[str, bytes, Path]

    async def size(self) -> int:
        return len(str(self.target))

    def get_target(self) -> Union[str, bytes, Path]:
        return self.target
