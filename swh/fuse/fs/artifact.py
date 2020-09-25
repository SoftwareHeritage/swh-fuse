# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.fuse.fs.entry import ArtifactEntry


class Content:
    def __init__(self, json):
        self.json = json


class Directory:
    def __init__(self, json):
        self.json = json

    def __iter__(self):
        entries = []
        for entry in self.json:
            name, swhid = entry["name"], entry["target"]
            entries.append(ArtifactEntry(name, swhid))
        return iter(entries)
