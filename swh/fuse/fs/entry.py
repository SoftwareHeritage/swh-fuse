# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from enum import IntEnum
from stat import S_IFDIR, S_IFREG
from typing import Any, Dict

from swh.model.identifiers import SWHID


class EntryMode(IntEnum):
    """ Default entry mode and permissions for the FUSE.

    The FUSE mount is always read-only, even if permissions contradict this
    statement (in a context of a directory, entries are listed with permissions
    taken from the archive).
    """

    RDONLY_FILE = S_IFREG | 0o444
    RDONLY_DIR = S_IFDIR | 0o555


class VirtualEntry:
    """ Main wrapper class to manipulate virtual FUSE entries

    Attributes:
        name: entry filename
        mode: entry permission mode
    """

    def __init__(self, name: str, mode: EntryMode):
        self.name = name
        self.mode = mode


class ArtifactEntry(VirtualEntry):
    """ FUSE virtual entry for a Software Heritage Artifact

    Attributes:
        name: entry filename
        swhid: Software Heritage persistent identifier
        prefetch: optional prefetched metadata used to set entry attributes
    """

    def __init__(self, name: str, swhid: SWHID, prefetch: Dict[str, Any] = None):
        self.name = name
        self.swhid = swhid
        self.prefetch = prefetch


ROOT_ENTRY = VirtualEntry("root", EntryMode.RDONLY_DIR)
ARCHIVE_ENTRY = VirtualEntry("archive", EntryMode.RDONLY_DIR)
META_ENTRY = VirtualEntry("meta", EntryMode.RDONLY_DIR)
