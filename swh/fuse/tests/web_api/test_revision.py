import json
import os
import time

import dateutil.parser

from swh.fuse.fs.artifact import RevisionHistoryShardByDate, RevisionHistoryShardByPage
from swh.model.hashutil import hash_to_hex
from swh.model.swhids import CoreSWHID

from .api_url import GRAPH_API_REQUEST
from .common import (
    check_dir_name_entries,
    get_data_from_graph_archive,
    get_data_from_web_archive,
)
from .data.config import REV_SMALL_HISTORY, ROOT_DIR, ROOT_REV


def test_access_meta(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / ROOT_REV / "meta.json"
    expected = json.dumps(get_data_from_web_archive(ROOT_REV))
    assert file_path.read_text().strip() == expected.strip()


def test_list_root(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / ROOT_REV / "root"
    check_dir_name_entries(dir_path, ROOT_DIR)


def test_list_parents(fuse_mntdir):
    rev_meta = get_data_from_web_archive(ROOT_REV)
    dir_path = fuse_mntdir / "archive" / ROOT_REV / "parents"
    for i, parent in enumerate(rev_meta["parents"]):
        parent_path = dir_path / str(i + 1)
        parent_swhid = f"swh:1:rev:{parent['id']}"
        assert parent_path.is_symlink()
        assert os.readlink(parent_path) == f"../../../archive/{parent_swhid}"


def test_list_parent(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / ROOT_REV / "parent"
    assert file_path.is_symlink()
    assert os.readlink(file_path) == "parents/1/"


def wait_check_no_status(dir_path):
    """
    Wait max 2 seconds to populate folders that have a ``.status`` flag,
    like ``by-date/``, and assert the file is gone.
    """
    for i in range(20):
        entries = os.listdir(dir_path)
        if entries and ".status" not in entries:
            break
        time.sleep(0.1)
    assert not (dir_path / ".status").exists()


def test_list_history(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / REV_SMALL_HISTORY / "history"
    assert os.listdir(dir_path) == ["by-date", "by-hash", "by-page"]

    history_meta = get_data_from_graph_archive(
        REV_SMALL_HISTORY, GRAPH_API_REQUEST.HISTORY
    )
    history = history_meta.strip()
    # Only keep second node in the edge because first node is redundant
    # information or the root node (hence not an ancestor)
    expected = set(
        map(CoreSWHID.from_string, [edge.split(" ")[1] for edge in history.split("\n")])
    )

    dir_by_hash = dir_path / "by-hash"
    for swhid in expected:
        depth1 = hash_to_hex(swhid.object_id)[:2]
        depth2 = str(swhid)
        assert (dir_by_hash / depth1).exists()
        assert depth2 in (os.listdir(dir_by_hash / depth1))

    dir_by_page = dir_path / "by-page"
    for idx, swhid in enumerate(expected):
        page_number = idx // RevisionHistoryShardByPage.PAGE_SIZE
        depth1 = RevisionHistoryShardByPage.PAGE_FMT.format(page_number=page_number)
        depth2 = str(swhid)
        assert (dir_by_page / depth1).exists()
        assert depth2 in (os.listdir(dir_by_page / depth1))

    dir_by_date = dir_path / "by-date"
    wait_check_no_status(dir_by_date)

    for swhid in expected:
        meta = get_data_from_web_archive(str(swhid))
        date = dateutil.parser.parse(meta["date"])
        depth1 = RevisionHistoryShardByDate.DATE_FMT.format(
            year=date.year, month=date.month, day=date.day
        )
        depth2 = str(swhid)
        assert (dir_by_date / depth1).exists()
        assert depth2 in (os.listdir(dir_by_date / depth1))
