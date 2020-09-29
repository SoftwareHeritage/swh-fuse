# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from pathlib import Path
import sqlite3
from typing import Any, List, Optional

from swh.model.identifiers import CONTENT, SWHID, parse_swhid
from swh.web.client.client import typify


class Cache:
    """ Cache all information retrieved from the Software Heritage API to
    minimize API calls. """

    def __init__(self, cache_dir: Path):
        if str(cache_dir) == ":memory:":
            self.conn = sqlite3.connect(":memory:")
        else:
            cache_path = Path(cache_dir, "cache.sqlite")
            cache_path.parents[0].mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(cache_path)

        self.cursor = self.conn.cursor()
        with self.conn:
            self.conn.execute(
                "create table if not exists metadata_cache (swhid, metadata)"
            )
            self.conn.execute("create table if not exists blob_cache (swhid, blob)")

    def get_metadata(self, swhid: SWHID) -> Any:
        """ Return previously cached JSON metadata associated with a SWHID """

        self.cursor.execute(
            "select metadata from metadata_cache where swhid=?", (str(swhid),)
        )
        cache = self.cursor.fetchone()
        if cache:
            metadata = json.loads(cache[0])
            return typify(metadata, swhid.object_type)
        else:
            return None

    def put_metadata(self, swhid: SWHID, metadata: Any) -> None:
        """ Cache JSON metadata associated with a SWHID """

        with self.conn:
            self.conn.execute(
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

    def get_metadata_swhids(self) -> List[SWHID]:
        """ Return a list of SWHID of all previously cached entry """

        self.cursor.execute("select swhid from metadata_cache")
        swhids = self.cursor.fetchall()
        swhids = [parse_swhid(x[0]) for x in swhids]
        return swhids

    def get_blob(self, swhid: SWHID) -> Optional[str]:
        """ Return previously cached blob bytes associated with a content SWHID """

        if swhid.object_type != CONTENT:
            raise AttributeError("Cannot retrieve blob from non-content object type")

        self.cursor.execute("select blob from blob_cache where swhid=?", (str(swhid),))
        cache = self.cursor.fetchone()
        if cache:
            blob = cache[0]
            return blob
        else:
            return None

    def put_blob(self, swhid: SWHID, blob: str) -> None:
        """ Cache blob bytes associated with a content SWHID """

        with self.conn:
            self.conn.execute(
                "insert into blob_cache values (?, ?)", (str(swhid), blob)
            )
