from os import listdir
from pathlib import Path

from swh.fuse.tests.common import get_data_from_archive
from swh.fuse.tests.data.config import ROOT_DIR


def test_list_dir(fuse_mntdir):
    dir_path = Path(fuse_mntdir, "archive", ROOT_DIR)
    dir_meta = get_data_from_archive(ROOT_DIR)
    expected = [x["name"] for x in dir_meta]
    actual = listdir(dir_path)
    assert set(actual) == set(expected)


def test_access_file(fuse_mntdir):
    file_path = Path(fuse_mntdir, "archive", ROOT_DIR, "README.md")
    assert file_path.is_file()


def test_access_subdir(fuse_mntdir):
    dir_path = Path(fuse_mntdir, "archive", ROOT_DIR, "src")
    assert dir_path.is_dir()
