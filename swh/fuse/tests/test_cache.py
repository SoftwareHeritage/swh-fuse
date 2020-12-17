# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from swh.fuse.tests.data.config import REGULAR_FILE
from swh.model.identifiers import parse_swhid


def test_cache_artifact(fuse_mntdir):
    assert os.listdir(fuse_mntdir / "cache") == ["origin"]

    (fuse_mntdir / "archive" / REGULAR_FILE).is_file()

    swhid = parse_swhid(REGULAR_FILE)
    assert os.listdir(fuse_mntdir / "cache") == [swhid.object_id[:2], "origin"]


def test_purge_artifact(fuse_mntdir):
    DEFAULT_CACHE_CONTENT = ["origin"]

    assert os.listdir(fuse_mntdir / "cache") == DEFAULT_CACHE_CONTENT

    # Access a content artifact...
    (fuse_mntdir / "archive" / REGULAR_FILE).is_file()
    assert os.listdir(fuse_mntdir / "cache") != DEFAULT_CACHE_CONTENT
    # ... and remove it from cache
    swhid = parse_swhid(REGULAR_FILE)
    os.unlink(fuse_mntdir / "cache" / swhid.object_id[:2] / str(swhid))

    assert os.listdir(fuse_mntdir / "cache") == DEFAULT_CACHE_CONTENT
