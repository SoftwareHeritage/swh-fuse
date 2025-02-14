# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Fixtures for the GraphBackend-ed swh-fuse
-----------------------------------------

Those rely on the test graph in `swh-graph`.
Data expected in the test graph is provided here as fixtures and will have to be kept
in sync with swh/graph/tests/grpc/test_getnode.py
"""

import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
from typing import Generator
from urllib.parse import quote_plus

from click.testing import CliRunner
import pytest

from swh.fuse import fuse
import swh.fuse.cli as cli
from swh.graph.pytest_plugin import *  # noqa ; provides the graph_grpc_server fixture


@pytest.fixture(scope="module")
def objstorage() -> dict:
    """
    TODO spawn a real objstorage ? or maybe implement a "cls: mock" ?
    """
    return {"cls": "remote", "url": "http://127.0.0.1:15003"}


@pytest.fixture(scope="module")
def hashes_path() -> str:
    """
    TODO maybe this should be in swh.graph along the test graph
    """
    return os.path.join(os.path.dirname(__file__), "hashes.orc")


@pytest.fixture(scope="module")
def fuse_graph_mountpoint(
    hashes_path, objstorage, graph_grpc_server
) -> Generator[Path, None, None]:
    with TemporaryDirectory(suffix=".swh-fuse-test") as tmpdir:
        mountpoint = Path(tmpdir)
        config = {
            "graph": {
                "grpc-url": graph_grpc_server,
                "objstorage": objstorage,
                "hashes-path": hashes_path,
            },
            "cache": {
                "metadata": {"in-memory": True},
                "blob": {"in-memory": True},
                "direntry": {"maxram": "10%"},
            },
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


@pytest.fixture()
def example_origin() -> str:
    "Adapted from swh.graph.tests.test_http_client.TEST_ORIGIN_ID"
    return quote_plus("https://example.com/swh/graph")


@pytest.fixture()
def example_snapshot() -> str:
    return "swh:1:snp:0000000000000000000000000000000000000020"


@pytest.fixture()
def example_revision() -> str:
    return "swh:1:rev:0000000000000000000000000000000000000009"


@pytest.fixture()
def example_release() -> str:
    return "swh:1:rel:0000000000000000000000000000000000000010"


@pytest.fixture()
def example_directory() -> str:
    return "swh:1:dir:0000000000000000000000000000000000000008"
