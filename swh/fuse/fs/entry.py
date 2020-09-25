# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from enum import IntEnum
from stat import S_IFDIR, S_IFREG

from swh.model.identifiers import SWHID


class EntryMode(IntEnum):
    RDONLY_FILE = S_IFREG | 0o444
    RDONLY_DIR = S_IFDIR | 0o555


class VirtualEntry:
    def __init__(self, name: str, mode: EntryMode):
        self.name = name
        self.mode = mode


class ArtifactEntry(VirtualEntry):
    def __init__(self, name: str, swhid: SWHID):
        self.name = name
        self.swhid = swhid


ROOT_ENTRY = VirtualEntry("root", EntryMode.RDONLY_DIR)
ARCHIVE_ENTRY = VirtualEntry("archive", EntryMode.RDONLY_DIR)
META_ENTRY = VirtualEntry("meta", EntryMode.RDONLY_DIR)
