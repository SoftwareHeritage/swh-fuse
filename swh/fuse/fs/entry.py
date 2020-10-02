# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass
from enum import IntEnum
from stat import S_IFDIR, S_IFREG
from typing import Any

from swh.model.identifiers import SWHID

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


@dataclass
class FuseEntry:
    """ Main wrapper class to manipulate virtual FUSE entries

    Attributes:
        name: entry filename
        mode: entry permission mode
        fuse: internal reference to the main FUSE class
    """

    name: str
    mode: int
    fuse: Fuse

    def __len__(self) -> int:
        return 0

    # TODO: type hint?
    def __iter__(self):
        return None

    # TODO: remove
    def __hash__(self):
        return hash((self.name, self.mode))


@dataclass
class ArtifactEntry(FuseEntry):
    """ FUSE virtual entry for a Software Heritage Artifact

    Attributes:
        swhid: Software Heritage persistent identifier
        prefetch: optional prefetched metadata used to set entry attributes
    """

    swhid: SWHID
    prefetch: Any = None

    # TODO: remove
    def __hash__(self):
        return hash((self.name, self.mode, self.swhid))
