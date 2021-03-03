# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from swh.fuse.tests.data.config import REGULAR_FILE
from swh.model.hashutil import hash_to_hex
from swh.model.identifiers import CoreSWHID


def test_cache_artifact(fuse_mntdir):
    assert os.listdir(fuse_mntdir / "cache") == ["origin"]

    (fuse_mntdir / "archive" / REGULAR_FILE).is_file()

    swhid = CoreSWHID.from_string(REGULAR_FILE)
    assert os.listdir(fuse_mntdir / "cache") == [
        hash_to_hex(swhid.object_id)[:2],
        "origin",
    ]


def test_purge_artifact(fuse_mntdir):
    DEFAULT_CACHE_CONTENT = ["origin"]

    assert os.listdir(fuse_mntdir / "cache") == DEFAULT_CACHE_CONTENT

    # Access a content artifact...
    (fuse_mntdir / "archive" / REGULAR_FILE).is_file()
    assert os.listdir(fuse_mntdir / "cache") != DEFAULT_CACHE_CONTENT
    # ... and remove it from cache
    swhid = CoreSWHID.from_string(REGULAR_FILE)
    os.unlink(fuse_mntdir / "cache" / hash_to_hex(swhid.object_id)[:2] / str(swhid))

    assert os.listdir(fuse_mntdir / "cache") == DEFAULT_CACHE_CONTENT
