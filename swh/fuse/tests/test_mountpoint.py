# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from swh.fuse.tests.data.config import REGULAR_FILE


def test_mountpoint(fuse_mntdir):
    archive_dir = fuse_mntdir / "archive"
    meta_dir = fuse_mntdir / "meta"
    assert os.listdir(archive_dir) == []
    assert os.listdir(meta_dir) == []
    # On the fly mounting
    file_path = archive_dir / REGULAR_FILE
    assert file_path.is_file()
