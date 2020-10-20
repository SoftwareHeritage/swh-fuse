import os
import urllib.parse

from swh.fuse.tests.common import get_data_from_web_archive
from swh.fuse.tests.data.config import ROOT_SNP


def test_list_branches(fuse_mntdir):
    snp_meta = get_data_from_web_archive(ROOT_SNP)
    expected = snp_meta.keys()
    # Mangle branch name to create a valid UNIX filename
    expected = [urllib.parse.quote_plus(x) for x in expected]
    actual = os.listdir(fuse_mntdir / "archive" / ROOT_SNP)
    assert set(actual) == set(expected)


def test_access_rev_target(fuse_mntdir):
    branch_name = urllib.parse.quote_plus("refs/heads/master")
    dir_path = fuse_mntdir / "archive" / ROOT_SNP / branch_name
    expected = set(["meta.json", "root", "parent", "parents", "history"])
    actual = set(os.listdir(dir_path))
    assert expected.issubset(actual)
