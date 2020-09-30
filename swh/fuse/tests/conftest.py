# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from multiprocessing import Process
from os import listdir
from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time

from click.testing import CliRunner
import pytest
import yaml

from swh.fuse import cli

from .api_data import API_URL, MOCK_ARCHIVE, ROOT_SWHID


@pytest.fixture
def web_api_mock(requests_mock):
    for api_call, data in MOCK_ARCHIVE.items():
        requests_mock.get(f"{API_URL}/{api_call}", text=data)
    return requests_mock


@pytest.fixture
def fuse_mntdir(web_api_mock):
    tmpdir = TemporaryDirectory(suffix=".swh-fuse-test")
    tmpfile = NamedTemporaryFile(suffix=".swh-fuse-test.yml")

    config = {
        "cache": {"metadata": {"in-memory": True}, "blob": {"in-memory": True}},
        "web-api": {"url": API_URL, "auth-token": None},
    }

    # Run FUSE in foreground mode but in a separate process, so it does not
    # block execution and remains easy to kill during teardown
    def fuse_process(tmpdir, tmpfile):
        with tmpdir as mntdir, tmpfile as config_path:
            config_path = Path(config_path.name)
            config_path.write_text(yaml.dump(config))
            CliRunner().invoke(
                cli.mount,
                args=[mntdir, ROOT_SWHID, "--foreground", "--config-file", config_path],
            )

    fuse = Process(target=fuse_process, args=[tmpdir, tmpfile])
    fuse.start()
    # Wait max 3 seconds for the FUSE to correctly mount
    for i in range(30):
        try:
            root = listdir(tmpdir.name)
            if root:
                break
        except FileNotFoundError:
            pass
        time.sleep(0.1)
    else:
        raise FileNotFoundError(f"Could not mount FUSE in {tmpdir.name}")

    yield tmpdir.name

    subprocess.run(["fusermount", "-u", tmpdir.name], check=True)
