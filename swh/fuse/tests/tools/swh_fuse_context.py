# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core.config import merge_configs
from swh.fuse.cli import DEFAULT_CONFIG
from swh.fuse.fuse import SwhFsTmpMount


def test_swh_fuse_context():
    config = merge_configs(
        DEFAULT_CONFIG,
        {
            "cache": {
                "metadata": {"in-memory": True},
                "blob": {"bypass": True},
                "direntry": {"maxram": "10%"},
            },
        },
    )
    with SwhFsTmpMount(config=config) as mountpoint:
        cache = mountpoint / "cache"
        assert cache.is_dir()
        subfolders = list(cache.glob("*"))
        assert subfolders == [cache / "origin"]
    assert not mountpoint.is_dir()
