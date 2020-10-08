import json
from os import listdir
from pathlib import Path

from .api_data import MOCK_ARCHIVE, ROOTDIR_SWHID, ROOTDIR_URL


def get_rootdir_entries():
    rootdir_resp = json.loads(MOCK_ARCHIVE[ROOTDIR_URL])
    return [entry["name"] for entry in rootdir_resp]


def test_ls_rootdir(fuse_mntdir):
    expected = get_rootdir_entries()

    rootdir_path = Path(fuse_mntdir, "archive", ROOTDIR_SWHID)
    actual = listdir(rootdir_path)
    assert actual == expected
