import os
from pathlib import Path

import dateutil.parser

from swh.fuse.fs.artifact import Origin
from swh.fuse.tests.common import get_origin_data_from_web_archive
from swh.fuse.tests.data.config import ORIGIN_URL, ORIGIN_URL_ENCODED


def test_list_visits(fuse_mntdir):
    visits_dir = fuse_mntdir / "origin" / ORIGIN_URL_ENCODED
    visits_meta = get_origin_data_from_web_archive(ORIGIN_URL)
    for visit in visits_meta:
        date = dateutil.parser.parse(visit["date"])
        name = Origin.DATE_FMT.format(year=date.year, month=date.month, day=date.day)
        assert name in os.listdir(visits_dir)

        dirname = visits_dir / name
        assert Path(dirname / "meta.json").is_file()
        if "snapshot" in os.listdir(dirname):
            assert Path(dirname / "snapshot").is_symlink()
