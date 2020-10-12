import json
from os import listdir, readlink
from pathlib import Path

from swh.fuse.tests.common import assert_file_content, get_data_from_archive
from swh.fuse.tests.data.config import ROOT_DIR, ROOT_REV


def test_access_meta(fuse_mntdir):
    file_path = Path(fuse_mntdir, "archive", ROOT_REV, "meta.json")
    expected = json.dumps(get_data_from_archive(ROOT_REV))
    assert_file_content(file_path, expected)


def test_list_root(fuse_mntdir):
    dir_path = Path(fuse_mntdir, "archive", ROOT_REV, "root")
    dir_meta = get_data_from_archive(ROOT_DIR)
    expected = [x["name"] for x in dir_meta]
    actual = listdir(dir_path)
    assert set(actual) == set(expected)


def test_list_parents(fuse_mntdir):
    rev_meta = get_data_from_archive(ROOT_REV)
    dir_path = Path(fuse_mntdir, "archive", ROOT_REV, "parents")
    for i, parent in enumerate(rev_meta["parents"]):
        parent_path = Path(dir_path, str(i + 1))
        parent_swhid = f"swh:1:rev:{parent['id']}"
        assert parent_path.is_symlink()
        assert readlink(parent_path) == f"../../../archive/{parent_swhid}"


def test_list_parent(fuse_mntdir):
    file_path = Path(fuse_mntdir, "archive", ROOT_REV, "parent")
    assert file_path.is_symlink()
    assert readlink(file_path) == "parents/1/"
