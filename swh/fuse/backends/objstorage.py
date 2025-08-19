# Copyright (C) 2025 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import typing

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

    See :ref:`Configuring files' download <swh-fuse-config-file-download>`.
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

        self.statsd = Statsd()
        self.storage_tracker = TimedContextManagerDecorator(
            self.statsd, "swhfuse_waiting_storage"
        )
        self.objstorage_tracker = TimedContextManagerDecorator(
            self.statsd, "swhfuse_waiting_objstorage"
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
        self.statsd.increment("swhfuse_get_blob")
        hashes = None
        try:
            with self.storage_tracker:
                found = self.storage.content_get([swhid.object_id], algo="sha1_git")
                if found and found[0]:
                    hashes = objid_from_dict(found[0].hashes())
            if hashes:
                if self.objstorage is None:
                    self.logger.debug("downloading %s from storage", hashes)
                    with self.storage_tracker:
                        content = self.storage.content_get_data(hashes)
                        if content:
                            return content
                    raise ValueError(f"SWH-storage cannot get object {hashes}")
                # else let's reach the "try objstorage" block
            else:
                raise ValueError(f"SWH-storage cannot find object {swhid}")
        except BaseException as e:
            self.statsd.increment("swhfuse_blob_not_in_storage")
            self.logger.error("Failed to fetch %s from storage: %s", swhid, e)
            raise

        try:
            self.logger.debug("downloading %s from objstorage", hashes)
            with self.objstorage_tracker:
                return self.objstorage.get(hashes)
            raise ValueError(f"SWH-objstorage cannot find object {hashes}")

        except BaseException as e:
            self.statsd.increment("swhfuse_blob_not_in_objstorage")
            self.logger.error("Failed to fetch %s from objstorage: %s", swhid, e)
            raise
