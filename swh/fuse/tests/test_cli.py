# Copyright (C) 2020 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pathlib import Path

from .api_data import ROOT_SWHID


def test_mountpoint(fuse_mntdir):
    archive_dir = Path(fuse_mntdir, "archive")
    meta_dir = Path(fuse_mntdir, "meta")
    swhid_dir = Path(fuse_mntdir, "archive", ROOT_SWHID)
    assert archive_dir.is_dir()
    assert meta_dir.is_dir()
    assert swhid_dir.is_dir()
