import json
import os

import requests_mock

from .test_revision import wait_check_no_status
from .unusual_data import (
    API_URL,
    BROKEN_RELEASE_SWHID,
    BROKEN_REVISION_SWHID,
    MOCK_ARCHIVE,
    REVISION_SWHID,
)


def test_unusual_cases(fuse_mntdir):
    with requests_mock.Mocker() as mocker:
        for api_call, data in MOCK_ARCHIVE.items():
            mocker.get(f"{API_URL}/{api_call}", text=data)

        release_path = fuse_mntdir / "archive" / BROKEN_RELEASE_SWHID

        meta_path = release_path / "meta.json"
        meta_content = json.loads(meta_path.read_text())
        assert meta_content["target_type"] == "revision"
        assert meta_content["target"] in REVISION_SWHID
        assert meta_content["date"] is None

        target_path = release_path / "target"
        expected = set(["meta.json", "root", "parent", "parents", "history"])
        actual = set(os.listdir(target_path))
        assert expected.issubset(actual)

        target_history_bydate = target_path / "history" / "by-date"
        wait_check_no_status(target_history_bydate)

        history = list(os.listdir(target_history_bydate))
        assert history == ["1970"]
        broken_date_path = target_history_bydate / "1970" / "01" / "01"
        broken_rev_path = list(os.listdir(broken_date_path))[0]
        broken_rev_meta = json.loads(
            (broken_date_path / broken_rev_path / "meta.json").read_text()
        )
        assert broken_rev_meta["id"] in BROKEN_REVISION_SWHID
