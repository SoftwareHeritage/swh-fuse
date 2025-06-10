# Copyright (C) 2025 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import typing

from swh.core.api import RemoteException
from swh.core.statsd import Statsd, TimedContextManagerDecorator
from swh.fuse import LOGGER_NAME
from swh.model.swhids import CoreSWHID
from swh.objstorage.factory import get_objstorage
from swh.objstorage.interface import objid_from_dict
from swh.storage import get_storage

if typing.TYPE_CHECKING:
    from swh.objstorage.interface import ObjStorageInterface
    from swh.storage.interface import StorageInterface

from . import ContentBackend


class ObjStorageBackend(ContentBackend):
    """
    This content backend relies on an ``swh-storage`` service,
    and maybe an ``swh-objstorage`` directly.

    See :ref:`Configuring files' download`.
    """

    def __init__(self, conf: dict):
        self.logger = logging.getLogger(LOGGER_NAME)

        try:
            self.storage: StorageInterface = get_storage(**conf["content"]["storage"])
        except KeyError:
            raise ValueError(
                "`content` configuration block should contain at least a `storage` object"
            )

        try:
            self.objstorage: ObjStorageInterface | None = get_objstorage(
                **conf["content"]["objstorage"]
            )
        except KeyError:
            self.objstorage = None

        self.storage_tracker = TimedContextManagerDecorator(
            Statsd(), "storage_response_time"
        )
        self.objstorage_tracker = TimedContextManagerDecorator(
            Statsd(), "objstorage_response_time"
        )

    def shutdown(self) -> None:
        self.logger.info(
            "Spent %f ms waiting for storage",
            self.storage_tracker.total_elapsed,
        )
        self.logger.info(
            "Spent %f ms waiting for objstorage backend",
            self.objstorage_tracker.total_elapsed,
        )

    async def get_blob(self, swhid: CoreSWHID) -> bytes:
        """
        Fetch the content of a ``cnt`` object.
        """
        hashes = None
        with self.storage_tracker:
            found = self.storage.content_get([swhid.object_id], algo="sha1_git")
            if found and found[0]:
                hashes = objid_from_dict(found[0].hashes())
        if hashes:
            self.logger.debug(f"downloading {hashes} from objstorage")
            try:
                if self.objstorage is not None:
                    with self.objstorage_tracker:
                        return self.objstorage.get(hashes)
                else:
                    with self.storage_tracker:
                        content = self.storage.content_get_data(hashes)
                        if content:
                            return content
                raise ValueError(f"SWH-storage Cannot find object {swhid}")
            except RemoteException as e:
                if e.response:
                    self.logger.error(
                        f"Failed to fetch {hashes} from objstorage: {e.response.text}"
                    )
                raise e
        else:
            raise ValueError(f"SWH-storage Cannot find object {swhid}")
