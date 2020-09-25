# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from pathlib import Path
import sqlite3

from swh.model.identifiers import CONTENT, SWHID, parse_swhid
from swh.web.client.client import typify


class Cache:
    def __init__(self, cache_dir):
        if cache_dir == ":memory:":
            self.conn = sqlite3.connect(":memory:")
        else:
            cache_path = Path(cache_dir, "cache.sqlite")
            cache_path.parents[0].mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(cache_path)

        self.db = self.conn.cursor()
        self.db.execute("create table if not exists metadata_cache (swhid, metadata)")
        self.db.execute("create table if not exists blob_cache (swhid, blob)")
        self.conn.commit()

    def get_metadata(self, swhid: SWHID):
        self.db.execute(
            "select metadata from metadata_cache where swhid=?", (str(swhid),)
        )
        cache = self.db.fetchone()
        if cache:
            metadata = json.loads(cache[0])
            return typify(metadata, swhid.object_type)

    def put_metadata(self, swhid: SWHID, metadata):
        self.db.execute(
            "insert into metadata_cache values (?, ?)",
            (
                str(swhid),
                json.dumps(
                    metadata,
                    # Converts the typified JSON to plain str version
                    default=lambda x: x.object_id
                    if isinstance(x, SWHID)
                    else x.__dict__,
                ),
            ),
        )
        self.conn.commit()

    def get_metadata_swhids(self):
        self.db.execute("select swhid from metadata_cache")
        swhids = self.db.fetchall()
        swhids = [parse_swhid(x[0]) for x in swhids]
        return swhids

    def get_blob(self, swhid: SWHID):
        if swhid.object_type != CONTENT:
            raise AttributeError("Cannot retrieve blob from non-content object type")

        self.db.execute("select blob from blob_cache where swhid=?", (str(swhid),))
        cache = self.db.fetchone()
        if cache:
            blob = cache[0]
            return blob

    def put_blob(self, swhid: SWHID, blob):
        self.db.execute("insert into blob_cache values (?, ?)", (str(swhid), blob))
        self.conn.commit()
