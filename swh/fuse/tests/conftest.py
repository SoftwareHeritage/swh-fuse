# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from multiprocessing import Process
import os
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time

from click.testing import CliRunner
import pytest
import yaml

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
    tmpdir = TemporaryDirectory(suffix=".swh-fuse-test")

    config = {
        "cache": {"metadata": {"in-memory": True}, "blob": {"in-memory": True},},
        "web-api": {"url": API_URL, "auth-token": None},
        "json-indent": None,
    }

    # Run FUSE in foreground mode but in a separate process, so it does not
    # block execution and remains easy to kill during teardown
    def fuse_process(mntdir: Path):
        with NamedTemporaryFile(suffix=".swh-fuse-test.yml") as tmpfile:
            config_path = Path(tmpfile.name)
            config_path.write_text(yaml.dump(config))
            CliRunner().invoke(
                cli.fuse,
                args=[
                    "--config-file",
                    str(config_path),
                    "mount",
                    str(mntdir),
                    "--foreground",
                ],
            )

    fuse = Process(target=fuse_process, args=[Path(tmpdir.name)])
    fuse.start()
    # Wait max 3 seconds for the FUSE to correctly mount
    for i in range(30):
        try:
            root = os.listdir(tmpdir.name)
            if root:
                break
        except FileNotFoundError:
            pass
        time.sleep(0.1)
    else:
        raise FileNotFoundError(f"Could not mount FUSE in {tmpdir.name}")

    yield Path(tmpdir.name)

    CliRunner().invoke(cli.umount, [tmpdir.name])
    fuse.join()
