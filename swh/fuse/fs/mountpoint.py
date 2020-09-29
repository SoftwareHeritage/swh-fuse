# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Iterator

from swh.fuse.cache import Cache
from swh.fuse.fs.entry import (
    ARCHIVE_DIRENTRY,
    META_DIRENTRY,
    ArtifactEntry,
    EntryMode,
    VirtualEntry,
)


class Root:
    """ The FUSE mountpoint, consisting of the archive/ and meta/ directories """

    def __iter__(self) -> Iterator[VirtualEntry]:
        entries = [ARCHIVE_DIRENTRY, META_DIRENTRY]
        return iter(entries)


class Archive:
    """ The archive/ directory is lazily populated with one entry per accessed
    SWHID, having actual SWHIDs as names """

    def __init__(self, cache: Cache):
        self.cache = cache

    def __iter__(self) -> Iterator[VirtualEntry]:
        entries = []
        for swhid in self.cache.get_metadata_swhids():
            entries.append(ArtifactEntry(str(swhid), swhid))
        return iter(entries)


class Meta:
    """ The meta/ directory contains one SWHID.json file for each SWHID entry
    under archive/. The JSON file contain all available meta information about
    the given SWHID, as returned by the Software Heritage Web API for that
    object. Note that, in case of pagination (e.g., snapshot objects with many
    branches) the JSON file will contain a complete version with all pages
    merged together. """

    def __init__(self, cache: Cache):
        self.cache = cache

    def __iter__(self) -> Iterator[VirtualEntry]:
        entries = []
        for swhid in self.cache.get_metadata_swhids():
            filename = str(swhid) + ".json"
            entries.append(VirtualEntry(filename, EntryMode.RDONLY_FILE))
        return iter(entries)
