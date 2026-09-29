# Copyright (C) 2025-2026  The Software Heritage developers
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
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
from typing import Generator
from urllib.parse import quote_plus

from click.testing import CliRunner
import pytest

from swh.fuse import LOGGER_NAME, fuse
from swh.fuse.backends.objstorage import ObjStorageBackend
import swh.fuse.cli as cli
from swh.graph.pytest_plugin import *  # noqa ; this provides the graph_grpc_server fixture
from swh.model.model import Content
from swh.mosaic import IdxDescription, MosaicCreator


@pytest.fixture(scope="module")
def fuse_graph_mountpoint(
    graph_grpc_server, example_content: Content
) -> Generator[Path, None, None]:
    with TemporaryDirectory(suffix=".swh-fuse-test") as tmpdir:
        mosaic_path = Path(tmpdir) / "test.mosaic"
        with MosaicCreator(mosaic_path, [IdxDescription.SHA1GITFMPHGO]) as creator:
            assert example_content.data is not None  # make mypy happy
            creator.add([example_content.sha1_git], example_content.data)
        content_backend = ObjStorageBackend(
            {"content": {"objstorage": {"cls": "mosaic", "path": mosaic_path}}}
        )

        mountpoint = Path(tmpdir) / "mount"
        mountpoint.mkdir()
        config = {
            "graph": {
                "grpc-url": graph_grpc_server,
            },
            "cache": {
                "metadata": {"in-memory": True},
                "blob": {"bypass": True},
                "direntry": {"maxram": "10%"},
            },
            "json-indent": None,
        }

        def mount():
            loop = asyncio.new_event_loop()
            logging.getLogger(LOGGER_NAME).setLevel(logging.DEBUG)
            try:
                loop.run_until_complete(
                    fuse.main([], mountpoint, config, content_backend)
                )
            finally:
                if loop.is_running():
                    loop.stop()
                loop.close()

        mount_thread = threading.Thread(target=mount)
        mount_thread.start()

        for i in range(30):
            try:
                root = os.listdir(mountpoint)
                if root:
                    break
            except FileNotFoundError:
                pass
            time.sleep(0.1)
        else:
            raise FileNotFoundError(f"Could not mount FUSE in {mountpoint}")

        try:
            yield mountpoint
        finally:
            CliRunner().invoke(cli.umount, [str(mountpoint)])


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


@pytest.fixture()
def example_content_swhid() -> str:
    return "swh:1:cnt:0000000000000000000000000000000000000001"


@pytest.fixture(scope="module")
def example_content() -> Content:
    h = bytes.fromhex("0000000000000000000000000000000000000001")
    return Content(
        sha1_git=h,
        blake2s256=h,
        sha256=h,
        sha1=h,
        data=b"Hello world",
        length=11,
    )
