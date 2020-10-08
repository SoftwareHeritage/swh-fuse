from os import listdir
from pathlib import Path

from swh.fuse.tests.test_directory import get_rootdir_entries

from .api_data import ROOTREV_SWHID


def test_symlinks_exist(fuse_mntdir):
    rootrev_dir = Path(fuse_mntdir, "archive", ROOTREV_SWHID)
    assert Path(rootrev_dir, "root").is_symlink()
    assert Path(rootrev_dir, "parent").is_symlink()
    assert Path(rootrev_dir, "parents").is_dir()
    assert Path(rootrev_dir, "meta.json").is_symlink()


def test_ls_rootdir(fuse_mntdir):
    expected = get_rootdir_entries()

    rootdir_path = Path(fuse_mntdir, "archive", ROOTREV_SWHID, "root")
    actual = listdir(rootdir_path)
    assert actual == expected
