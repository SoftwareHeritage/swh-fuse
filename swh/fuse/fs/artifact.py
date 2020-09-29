# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, Iterator, List

from swh.fuse.fs.entry import ArtifactEntry, VirtualEntry


class Content:
    """ Software Heritage content artifact.

    Content leaves (AKA blobs) are represented on disks as regular files,
    containing the corresponding bytes, as archived.

    Note that permissions are associated to blobs only in the context of
    directories. Hence, when accessing blobs from the top-level `archive/`
    directory, the permissions of the `archive/SWHID` file will be arbitrary and
    not meaningful (e.g., `0x644`). """

    def __init__(self, json: Dict[str, Any]):
        self.json = json


class Directory:
    """ Software Heritage directory artifact.

    Directory nodes are represented as directories on the file-system,
    containing one entry for each entry of the archived directory. Entry names
    and other metadata, including permissions, will correspond to the archived
    entry metadata.

    Note that the FUSE mount is read-only, no matter what the permissions say.
    So it is possible that, in the context of a directory, a file is presented
    as writable, whereas actually writing to it will fail with `EPERM`. """

    def __init__(self, json: List[Dict[str, Any]]):
        self.json = json

    def __iter__(self) -> Iterator[VirtualEntry]:
        entries = []
        for entry in self.json:
            name, swhid = entry["name"], entry["target"]
            # The directory API has extra info we can use to set attributes
            # without additional Software Heritage API call
            prefetch = entry
            entries.append(ArtifactEntry(name, swhid, prefetch))
        return iter(entries)
