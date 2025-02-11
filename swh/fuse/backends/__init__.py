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
    async def get_metadata(self, swhid: CoreSWHID) -> dict:
        """
        Entries in the returned `dict` depend on the `swhid` type.

        TODO detail per type
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

        TODO which fields ?
        """
