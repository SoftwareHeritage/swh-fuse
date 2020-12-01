# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from swh.fuse.tests.data.config import ORIGIN_URL_ENCODED, REGULAR_FILE


def test_mountpoint(fuse_mntdir):
    assert os.listdir(fuse_mntdir) == ["archive", "meta", "origin"]


def test_on_the_fly_mounting(fuse_mntdir):
    assert os.listdir(fuse_mntdir / "archive") == []
    assert os.listdir(fuse_mntdir / "meta") == []
    assert (fuse_mntdir / "archive" / REGULAR_FILE).is_file()
    assert (fuse_mntdir / "meta" / (REGULAR_FILE + ".json")).is_file()

    assert os.listdir(fuse_mntdir / "origin") == []
    assert (fuse_mntdir / "origin" / ORIGIN_URL_ENCODED).is_dir()
