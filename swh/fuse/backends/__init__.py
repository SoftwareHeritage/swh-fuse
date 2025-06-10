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


class GraphBackend(ABC):
    """
    Methods required by the FUSE logic to create its folders layout.
    Those methods must return dicts compliant with the Web API, to ease their use and
    caching in the :py:class:`swh.fuse.fuse.Fuse` class.
    Fields listed in method specifications below are the minimal required fields.
    At worst, set them to ``None`` (because this is better supported by
    ``swh-web-client``'s ``typify_json``).
    Additional fields will be included in the various `meta.json` files proposed
    by this virtual file system.
    """

    @abstractmethod
    async def get_metadata(self, swhid: CoreSWHID) -> Dict | List:
        """
        Entries in the returned ``dict`` depend on the ``swhid`` type.

        For ``cnt``, return a dict containing at least ``length`` (int).

        For ``dir``, return a list of entries like

        .. code:: python

            {
                "dir_id": "dir's hash",
                "name": "dir item name",
                "type": "str=dir|file|rev",  # yes, `file`...
                "target": "target hash",
                "perms": "permissions [int]",
                # if target is a cnt:
                "length": "file size [int]",
            }

        For ``rev``, return a dict containing at least ``directory`` (SWHID),
        ``parents`` (list of objects containing at least ``id`` (hash)),
        ``date`` (str, isoformat), ``committer_date`` (str, isoformat),
        ``id`` (object's hash).

        For ``rel``, return a dict containing at least ``target`` (SWHID),
        ``target_type``,  ``date`` (str, isoformat), ``id`` (object's hash).

        For ``snp``, return a dict where each key is a branch name,
        each value is a dict containing at least ``target`` (hash),
        ``target_type`` (content, directory, revision, release, snapshot or alias).
        """

    @abstractmethod
    async def get_history(self, swhid: CoreSWHID) -> List[Tuple[str, str]]:
        """
        Return a list of tuples ``(swhid, revision swhid)``
        """

    @abstractmethod
    async def get_visits(self, url_encoded: str) -> List[Dict[str, Any]]:
        """
        Return a list of objects

        Each object should contain fields ``date`` (ISO), ``origin`` (str),
        ``snapshot`` (SWHID's hash as str)
        """

    def shutdown(self) -> None:
        """
        Called when the FUSE object is destroyed.
        """


class ContentBackend(ABC):
    """
    Methods required by the FUSE logic to provide files' contents.
    """

    @abstractmethod
    async def get_blob(self, swhid: CoreSWHID) -> bytes:
        """
        Fetch the content of a ``cnt`` object.
        """

    def shutdown(self) -> None:
        """
        Called when the FUSE object is destroyed.
        """
