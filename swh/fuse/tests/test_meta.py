import json

from swh.fuse.tests.common import get_data_from_web_archive
from swh.fuse.tests.data.config import ALL_ENTRIES


def test_access_meta_file(fuse_mntdir):
    for swhid in ALL_ENTRIES:
        # On the fly mounting
        file_path_meta = fuse_mntdir / f"archive/{swhid}.json"
        expected = json.dumps(get_data_from_web_archive(swhid))
        assert file_path_meta.read_text().strip() == expected.strip()
