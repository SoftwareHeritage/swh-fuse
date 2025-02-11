# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import os
from pathlib import Path
import subprocess
import tempfile
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
    # fmt: off
    with (
        tempfile.TemporaryDirectory(suffix=".swh-fuse-test") as tmpdir,
        tempfile.NamedTemporaryFile(suffix=".swh-fuse-test.yml") as tmpfile
    ):
        # fmt: on

        config = {
            "cache": {
                "metadata": {"in-memory": True},
                "blob": {"in-memory": True},
            },
            "web-api": {"url": API_URL, "auth-token": None},
            "json-indent": None,
        }
        config_path = Path(tmpfile.name)
        config_path.write_text(yaml.dump(config))

        # Run FUSE in foreground mode but in a separate process, so it does not
        # block execution and remains easy to kill during teardown
        fuse = subprocess.Popen(
            [
                "swh",
                "--log-level",
                "swh.fuse:DEBUG",
                "fs",
                "--config-file",
                tmpfile.name,
                "mount",
                tmpdir,
                "--foreground",
            ],
        )

        try:
            # Wait max 5 seconds for the FUSE to correctly mount
            for i in range(50):
                try:
                    root = os.listdir(tmpdir)
                    if root:
                        break
                except FileNotFoundError:
                    pass
                time.sleep(0.1)
            else:
                raise FileNotFoundError(f"Could not mount FUSE in {tmpdir}")

            yield Path(tmpdir)

            CliRunner().invoke(cli.umount, [tmpdir])
            fuse.wait(3)
        finally:
            fuse.poll()
            if fuse.returncode is None:
                fuse.kill()
