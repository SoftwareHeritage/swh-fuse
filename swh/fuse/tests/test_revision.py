import json
import os

from swh.fuse.tests.api_url import GRAPH_API_REQUEST
from swh.fuse.tests.common import (
    check_dir_name_entries,
    get_data_from_graph_archive,
    get_data_from_web_archive,
)
from swh.fuse.tests.data.config import REV_SMALL_HISTORY, ROOT_DIR, ROOT_REV
from swh.model.identifiers import parse_swhid


def test_access_meta(fuse_mntdir):
    file_path = fuse_mntdir / "archive" / ROOT_REV / "meta.json"
    expected = json.dumps(get_data_from_web_archive(ROOT_REV))
    assert file_path.read_text() == expected


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


def test_list_history(fuse_mntdir):
    dir_path = fuse_mntdir / "archive" / REV_SMALL_HISTORY / "history/by-hash"
    history_meta = get_data_from_graph_archive(
        REV_SMALL_HISTORY, GRAPH_API_REQUEST.HISTORY
    )
    history = history_meta.strip()
    # Only keep second node in the edge because first node is redundant
    # information or the root node (hence not an ancestor)
    expected = set([edge.split(" ")[1] for edge in history.split("\n")])

    for swhid in expected:
        swhid = parse_swhid(swhid)
        depth1 = swhid.object_id[:2]
        depth2 = str(swhid)
        assert (dir_path / depth1).exists()
        assert depth2 in (os.listdir(dir_path / depth1))
