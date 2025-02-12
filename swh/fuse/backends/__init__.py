# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
FUSE backends
-------------

These classes are abstraction layers to the archive's graph and object storage.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from swh.model.swhids import CoreSWHID


class FuseBackend(ABC):
    """
    Methods required by the FUSE logic.
    Those methods must return dicts compliant with the Web API, to ease their use and
    caching in the :ref:`swh.fuse.fuse.Fuse` class.
    """

    @abstractmethod
    async def get_metadata(self, swhid: CoreSWHID) -> Dict|List:
        """
        Entries in the returned `dict` depend on the `swhid` type.

        For `cnt`, return a dict containing at least `'length': [int]`
        TODO: support also `status: [str:visible|...]` ?

        For `dir`, return a list of entries like
        ```
        {
            "name": "dir item name",
            "target": "target swhid",
            "perms": "permissions [int]",
            "length": "file size, if target is a cnt [int]",
        }

        For `rev`, return a dict containing at least `directory` (SWHID) and
        `parents` (list of objects containing at list `id` (SWHID))

        For `rel`, return a dict containing at least `target` (SWHID)

        For `snp`, return a dict where each key is a branch name,
        each value is a dict containing at least `target`, `target_type`.
        ```
        """

    @abstractmethod
    async def get_blob(self, swhid: CoreSWHID) -> bytes:
        """
        Fetch the content of a `cnt` object.
        """

    @abstractmethod
    async def get_history(self, swhid: CoreSWHID) -> List[Tuple[str, str]]:
        """
        Return a list of tuples `(swhid, revision swhid)`
        """

    @abstractmethod
    async def get_visits(self, url_encoded: str) -> List[Dict[str, Any]]:
        """
        Return a list of objects

        Each object should contain fields `date` (ISO), `origin` (str),
        `snapshot` (SWHID) and ... anything we cant because the object
        will by in the `meta.json` file.
        """
