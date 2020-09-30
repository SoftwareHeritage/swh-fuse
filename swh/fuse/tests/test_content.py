from pathlib import Path

from .api_data import MOCK_ARCHIVE, README_RAW_URL, ROOT_SWHID


def test_file_exists(fuse_mntdir):
    readme_path = Path(fuse_mntdir, "archive", ROOT_SWHID, "README")
    assert readme_path.is_file()


def test_cat_file(fuse_mntdir):
    readme_path = Path(fuse_mntdir, "archive", ROOT_SWHID, "README")
    expected = MOCK_ARCHIVE[README_RAW_URL]
    with open(readme_path, "r") as f:
        actual = f.read()
        assert actual == expected
