# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time

from click.testing import CliRunner
import pytest

from swh.fuse import fuse
import swh.fuse.cli as cli
from swh.fuse.tests.data.api_data import API_URL, MOCK_ARCHIVE


@pytest.fixture
def web_api_mock(requests_mock):
    for api_call, data in MOCK_ARCHIVE.items():
        # Convert Python dict JSON into a string (only for non-raw API call)
        if not api_call.endswith("raw/") and not api_call.startswith("graph/"):
            data = json.dumps(data)

        http_method = requests_mock.get
        if api_call.startswith("origin/") and api_call.endswith("get/"):
            http_method = requests_mock.head

        http_method(f"{API_URL}/{api_call}", text=data)

    return requests_mock


@pytest.fixture
def fuse_mntdir(web_api_mock):
    with TemporaryDirectory(suffix=".swh-fuse-test") as tmpdir:
        mountpoint = Path(tmpdir)
        config = {
            "cache": {
                "metadata": {"in-memory": True},
                "blob": {"in-memory": True},
                "direntry": {"maxram": "10%"},
            },
            "web-api": {"url": API_URL, "auth-token": None},
            "json-indent": None,
        }

        def mount():
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(fuse.main([], mountpoint, config))
            finally:
                if loop.is_running():
                    loop.stop()
                loop.close()

        mount_thread = threading.Thread(target=mount)
        mount_thread.start()

        for i in range(30):
            try:
                root = os.listdir(tmpdir)
                if root:
                    break
            except FileNotFoundError:
                pass
            time.sleep(0.1)
        else:
            raise FileNotFoundError(f"Could not mount FUSE in {tmpdir}")

        try:
            yield mountpoint
        finally:
            CliRunner().invoke(cli.umount, [tmpdir])
