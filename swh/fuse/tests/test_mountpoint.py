# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from swh.fuse.tests.data.config import ORIGIN_URL_ENCODED, REGULAR_FILE
from swh.model.identifiers import CoreSWHID


def test_mountpoint(fuse_mntdir):
    assert {"archive", "cache", "origin", "README"} <= set(os.listdir(fuse_mntdir))


def test_on_the_fly_mounting(fuse_mntdir):
    assert os.listdir(fuse_mntdir / "archive") == []
    assert (fuse_mntdir / "archive" / REGULAR_FILE).is_file()
    assert (fuse_mntdir / "archive" / (REGULAR_FILE + ".json")).is_file()

    assert os.listdir(fuse_mntdir / "origin") == []
    assert (fuse_mntdir / "origin" / ORIGIN_URL_ENCODED).is_dir()

    sharded_dir = CoreSWHID.from_string(REGULAR_FILE).object_id.hex()[:2]
    assert os.listdir(fuse_mntdir / "cache") == [sharded_dir, "origin"]
    assert os.listdir(fuse_mntdir / "cache" / sharded_dir) == [
        REGULAR_FILE,
        REGULAR_FILE + ".json",
    ]
    assert os.listdir(fuse_mntdir / "cache/origin") == [ORIGIN_URL_ENCODED]
