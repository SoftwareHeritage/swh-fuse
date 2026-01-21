# Copyright (C) 2020-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from .common import get_data_from_web_archive
from .data.config import ALL_ENTRIES


def test_access_meta_file(fuse_mntdir):
    for swhid in ALL_ENTRIES:
        # On the fly mounting
        file_path_meta = fuse_mntdir / f"archive/{swhid}.json"
        expected = json.dumps(get_data_from_web_archive(swhid))
        assert file_path_meta.read_text().strip() == expected.strip()
