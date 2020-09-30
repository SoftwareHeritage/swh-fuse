import json
from os import listdir
from pathlib import Path

from .api_data import MOCK_ARCHIVE, ROOT_SWHID, ROOT_URL


def test_ls_root_swhid(fuse_mntdir):
    root_resp = json.loads(MOCK_ARCHIVE[ROOT_URL])
    expected = [entry["name"] for entry in root_resp]

    swhid_dir = Path(fuse_mntdir, "archive", ROOT_SWHID)
    actual = listdir(swhid_dir)
    assert actual == expected
