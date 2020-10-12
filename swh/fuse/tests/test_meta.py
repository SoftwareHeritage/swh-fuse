import json
from os import listdir
from pathlib import Path

from swh.fuse.tests.common import assert_file_content, get_data_from_archive
from swh.fuse.tests.data.config import ALL_ENTRIES


def test_access_meta_file(fuse_mntdir):
    for swhid in ALL_ENTRIES:
        # On the fly mounting
        file_path_archive = Path(fuse_mntdir, "archive", swhid)
        file_path_archive.exists()

        file_path_meta = Path(fuse_mntdir, "meta", f"{swhid}.json")
        assert file_path_meta.exists()
        expected = json.dumps(get_data_from_archive(swhid))
        assert_file_content(file_path_meta, expected)
