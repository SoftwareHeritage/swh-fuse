import json
import os

from swh.fuse.tests.common import check_dir_name_entries, get_data_from_web_archive
from swh.fuse.tests.data.config import (
    REL_TARGET_CNT,
    REL_TARGET_DIR,
    ROOT_DIR,
    ROOT_REL,
    TARGET_CNT,
    TARGET_DIR,
)


def test_access_meta(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / ROOT_REL / "meta.json"
    expected = json.dumps(get_data_from_web_archive(ROOT_REL))
    assert file_path.read_text().strip() == expected.strip()


def test_access_rev_target(fuse_mntdir):
    target_path = fuse_mntdir / "archive" / ROOT_REL / "target"
    expected = set(["meta.json", "root", "parent", "parents", "history"])
    actual = set(os.listdir(target_path))
    assert expected.issubset(actual)


def test_access_dir_target(fuse_mntdir):
    target_path = fuse_mntdir / "archive" / REL_TARGET_DIR / "target"
    check_dir_name_entries(target_path, TARGET_DIR)


def test_access_cnt_target(fuse_mntdir):
    target_path = fuse_mntdir / "archive" / REL_TARGET_CNT / "target"
    expected = get_data_from_web_archive(TARGET_CNT, raw=True)
    assert target_path.read_text() == expected


def test_target_type(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / ROOT_REL / "target_type"
    assert file_path.read_text() == "revision\n"


def test_access_root(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / ROOT_REL / "root"
    check_dir_name_entries(dir_path, ROOT_DIR)
