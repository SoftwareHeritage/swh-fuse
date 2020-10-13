import os

from swh.fuse.tests.common import check_dir_name_entries
from swh.fuse.tests.data.config import DIR_WITH_SUBMODULES, ROOT_DIR


def test_list_dir(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / ROOT_DIR
    check_dir_name_entries(dir_path, ROOT_DIR)


def test_access_file(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / ROOT_DIR / "README.md"
    assert file_path.is_file()


def test_access_subdir(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / ROOT_DIR / "src"
    assert dir_path.is_dir()


def test_access_submodule_entries(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / DIR_WITH_SUBMODULES
    submodules = {
        "book": "swh:1:rev:87dd6843678575f8dda962f239d14ef4be14b352",
        "edition-guide": "swh:1:rev:1a2390247ad6d08160e0dd74f40a01a9578659c2",
        "embedded-book": "swh:1:rev:4d78994915af1bde9a95c04a8c27d8dca066232a",
        "nomicon": "swh:1:rev:3e6e1001dc6e095dbd5c88005e80969f60e384e1",
        "reference": "swh:1:rev:11e893fc1357bc688418ddf1087c2b7aa25d154d",
        "rust-by-example": "swh:1:rev:1c2bd024d13f8011307e13386cf1fea2180352b5",
        "rustc-guide": "swh:1:rev:92baf7293dd2d418d2ac4b141b0faa822075d9f7",
    }
    for filename, swhid in submodules.items():
        target = f"../../archive/{swhid}"
        assert os.readlink(dir_path / filename) == target
