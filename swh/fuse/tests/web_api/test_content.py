# Copyright (C) 2020-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from .common import get_data_from_web_archive
from .data.config import REGULAR_FILE


def test_access_file(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / REGULAR_FILE
    assert file_path.is_file()


def test_cat_file(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / REGULAR_FILE
    expected = get_data_from_web_archive(REGULAR_FILE, raw=True)
    assert file_path.read_text() == expected
