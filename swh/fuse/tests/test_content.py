from pathlib import Path

from swh.fuse.tests.common import assert_file_content, get_data_from_archive
from swh.fuse.tests.data.config import REGULAR_FILE


def test_access_file(fuse_mntdir):
    file_path = Path(fuse_mntdir, "archive", REGULAR_FILE)
    assert file_path.is_file()


def test_cat_file(fuse_mntdir):
    file_path = Path(fuse_mntdir, "archive", REGULAR_FILE)
    expected = get_data_from_archive(REGULAR_FILE, raw=True)
    assert_file_content(file_path, expected)
