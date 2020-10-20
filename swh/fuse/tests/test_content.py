from swh.fuse.tests.common import get_data_from_web_archive
from swh.fuse.tests.data.config import REGULAR_FILE


def test_access_file(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / REGULAR_FILE
    assert file_path.is_file()


def test_cat_file(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / REGULAR_FILE
    expected = get_data_from_web_archive(REGULAR_FILE, raw=True)
    assert file_path.read_text() == expected
