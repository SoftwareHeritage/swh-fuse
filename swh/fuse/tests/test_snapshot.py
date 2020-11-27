import os
from pathlib import Path

from swh.fuse.tests.common import get_data_from_web_archive
from swh.fuse.tests.data.config import ROOT_SNP


def test_list_branches(fuse_mntdir):
    snp_dir = Path(fuse_mntdir / "archive" / ROOT_SNP)
    snp_meta = get_data_from_web_archive(ROOT_SNP)
    for branch_name in snp_meta.keys():
        assert (snp_dir / branch_name).is_symlink()


def test_access_rev_target(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / ROOT_SNP / "refs/heads/master"
    expected = set(["meta.json", "root", "parent", "parents", "history"])
    actual = set(os.listdir(dir_path))
    assert expected.issubset(actual)
