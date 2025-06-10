# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
from functools import partial
import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import unquote_plus

from requests import HTTPError

from swh.fuse import LOGGER_NAME
from swh.fuse.backends import ContentBackend, GraphBackend
from swh.model.swhids import CoreSWHID
from swh.web.client.client import WebAPIClient


class WebApiBackend(GraphBackend, ContentBackend):
    """
    A Backend querying everything via Software Heritage's public API.

    This is simpler to configure and deploy, but expect long response times.
    """

    def __init__(self, conf: Dict):
        """
        Only needs the ``web-api`` key of ``conf``, searching for ``url`` and maybe
        ``auth-token`` keys.
        """
        self.web_api = WebAPIClient(
            conf["web-api"]["url"], conf["web-api"]["auth-token"]
        )
        self.logger = logging.getLogger(LOGGER_NAME)

    async def get_metadata(self, swhid: CoreSWHID) -> Dict | List:
        try:
            self.logger.debug(f"Fetching metadata via Web API for {swhid}")
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(None, self.web_api.get, swhid, False)
            return metadata
        except HTTPError as err:
            self.logger.error("Cannot fetch metadata for object %s: %s", swhid, err)
            raise

    async def get_blob(self, swhid) -> bytes:
        try:
            self.logger.debug("Retrieving blob %s via web API...", swhid)
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, self.web_api.content_raw, swhid)
            blob = b"".join(list(resp))
            return blob
        except HTTPError as err:
            self.logger.error("Cannot fetch blob for object %s: %s", swhid, err)
            raise

    async def get_history(self, swhid: CoreSWHID) -> List[Tuple[str, str]]:
        try:
            # Use the swh-graph API to retrieve the full history very fast
            self.logger.debug("Retrieving history of %s via graph API...", swhid)
            call = f"graph/visit/edges/{swhid}?edges=rev:rev"
            loop = asyncio.get_event_loop()
            request = await loop.run_in_executor(None, self.web_api._call, call)
            history = request.text.strip()
            if history:
                edges = []
                for edge in history.split("\n"):
                    split = edge.split(" ")
                    if len(split) == 2:
                        edges.append((split[0], split[1]))
                return edges
            else:
                return []
        except HTTPError as err:
            self.logger.error("Cannot fetch history for object %s: %s", swhid, err)
            # Ignore exception since swh-graph does not necessarily contain the
            # most recent artifacts from the archive. Computing the full history
            # from the Web API is too computationally intensive so simply return
            # an empty list.
            return []

    async def get_visits(self, url_encoded: str) -> List[Dict[str, Any]]:
        try:
            self.logger.debug(
                "Retrieving visits for origin '%s' via web API...", url_encoded
            )
            loop = asyncio.get_event_loop()
            # Web API only takes non-encoded URL
            url = unquote_plus(url_encoded)

            origin_exists = await loop.run_in_executor(
                None, self.web_api.origin_exists, url
            )
            if not origin_exists:
                raise ValueError("origin does not exist")

            visits_it = await loop.run_in_executor(
                None, partial(self.web_api.visits, url, typify=False)
            )
            visits = list(visits_it)
            return visits
        except (ValueError, HTTPError) as err:
            self.logger.error(
                "Cannot fetch visits for origin '%s': %s", url_encoded, err
            )
            raise
