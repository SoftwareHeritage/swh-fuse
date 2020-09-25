# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.fuse.fs.entry import (
    ARCHIVE_ENTRY,
    META_ENTRY,
    ArtifactEntry,
    EntryMode,
    VirtualEntry,
)


class Root:
    def __iter__(self):
        entries = [ARCHIVE_ENTRY, META_ENTRY]
        return iter(entries)


class Archive:
    def __init__(self, cache):
        self.cache = cache

    def __iter__(self):
        entries = []
        for swhid in self.cache.get_metadata_swhids():
            entries.append(ArtifactEntry(str(swhid), swhid))
        return iter(entries)


class Meta:
    def __init__(self, cache):
        self.cache = cache

    def __iter__(self):
        entries = []
        for swhid in self.cache.get_metadata_swhids():
            filename = str(swhid) + ".json"
            entries.append(VirtualEntry(filename, EntryMode.RDONLY_FILE))
        return iter(entries)
