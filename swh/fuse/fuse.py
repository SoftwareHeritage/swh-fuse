# Copyright (C) 2020-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import errno
import logging
import os
from pathlib import Path
from shutil import rmtree, which
from subprocess import run
from tempfile import mkdtemp
from threading import Thread
import time
from typing import Any, Dict, List

import pyfuse3
import pyfuse3.asyncio

from swh.fuse import LOGGER_NAME
from swh.fuse.backends import ContentBackend, GraphBackend
from swh.fuse.cache import FuseCache
from swh.fuse.cli import load_config
from swh.fuse.fs.entry import FuseDirEntry, FuseEntry, FuseFileEntry, FuseSymlinkEntry
from swh.fuse.fs.mountpoint import Root
from swh.model.swhids import CoreSWHID, ObjectType


class Fuse(pyfuse3.Operations):
    """
    Software Heritage Filesystem in Userspace (FUSE).

    Locally mount parts of the archive and navigate it as a virtual file system.

    This class ties together ``pyfuse3`` and the configured cache and back-end.
    """

    def __init__(
        self,
        cache: FuseCache,
        conf: Dict[str, Any],
        graph_backend: GraphBackend,
        obj_backend: ContentBackend,
    ):
        super(Fuse, self).__init__()

        self._next_inode: pyfuse3.InodeT = pyfuse3.ROOT_INODE
        self._inode2entry: Dict[pyfuse3.InodeT, FuseEntry] = {}

        self.root = Root(fuse=self)
        self.conf = conf
        self.logger = logging.getLogger(LOGGER_NAME)

        self.time_ns: int = time.time_ns()  # start time, used as timestamp
        self.gid = os.getgid()
        self.uid = os.getuid()

        self.graph_backend = graph_backend
        self.obj_backend = obj_backend
        self.cache = cache

    def shutdown(self) -> None:
        self.graph_backend.shutdown()
        self.obj_backend.shutdown()

    def _alloc_inode(self, entry: FuseEntry) -> int:
        """Return a unique inode integer for a given entry"""

        inode = self._next_inode
        self._next_inode = pyfuse3.InodeT(inode + 1)
        self._inode2entry[inode] = entry

        return inode

    def _remove_inode(self, inode: pyfuse3.InodeT) -> None:
        try:
            del self._inode2entry[inode]
        except KeyError:
            pass

        try:
            pyfuse3.invalidate_inode(inode)
        except FileNotFoundError:
            pass

    def inode2entry(self, inode: pyfuse3.InodeT) -> FuseEntry:
        """Return the entry matching a given inode"""

        try:
            return self._inode2entry[inode]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

    async def get_metadata(self, swhid: CoreSWHID) -> Any:
        """Retrieve metadata for a given SWHID using Software Heritage API"""

        cache = await self.cache.metadata.get(swhid)
        if cache is not None:
            return cache

        metadata = await self.graph_backend.get_metadata(swhid)
        await self.cache.metadata.set(swhid, metadata)
        # Retrieve it from cache so it is correctly typed
        return await self.cache.metadata.get(swhid)

    async def get_blob(self, swhid: CoreSWHID) -> bytes:
        """Retrieve the blob bytes for a given content SWHID using Software
        Heritage API"""

        if swhid.object_type != ObjectType.CONTENT:
            raise pyfuse3.FUSEError(errno.EINVAL)

        cache = await self.cache.blob.get(swhid)
        if cache is not None:
            self.logger.debug("Found blob %s in cache", swhid)
            return cache

        blob = await self.obj_backend.get_blob(swhid)
        await self.cache.blob.set(swhid, blob)
        return blob

    async def get_history(self, swhid: CoreSWHID) -> List[CoreSWHID]:
        """Retrieve a revision's history using Software Heritage Graph API"""

        if swhid.object_type != ObjectType.REVISION:
            raise pyfuse3.FUSEError(errno.EINVAL)

        cache = await self.cache.history.get(swhid)
        if cache is not None:
            self.logger.debug(
                "Found history of %s in cache (%d ancestors)", swhid, len(cache)
            )
            return cache

        history = await self.graph_backend.get_history(swhid)
        await self.cache.history.set(history)
        # Retrieve it from cache so it is correctly typed
        res = await self.cache.history.get(swhid)
        return res

    async def get_visits(self, url_encoded: str) -> List[Dict[str, Any]]:
        """Retrieve origin visits given an encoded-URL using Software Heritage API"""

        cache = await self.cache.metadata.get_visits(url_encoded)
        if cache is not None:
            self.logger.debug(
                "Found %d visits for origin '%s' in cache",
                len(cache),
                url_encoded,
            )
            return cache

        visits = await self.graph_backend.get_visits(url_encoded)
        await self.cache.metadata.set_visits(url_encoded, visits)
        # Retrieve it from cache so it is correctly typed
        res = await self.cache.metadata.get_visits(url_encoded)
        return res

    async def get_attrs(self, entry: FuseEntry) -> pyfuse3.EntryAttributes:
        """Return entry attributes"""

        attrs = pyfuse3.EntryAttributes()
        attrs.st_size = 0
        attrs.st_atime_ns = self.time_ns
        attrs.st_ctime_ns = self.time_ns
        attrs.st_mtime_ns = self.time_ns
        attrs.st_gid = self.gid
        attrs.st_uid = self.uid
        attrs.st_ino = pyfuse3.InodeT(entry.inode)
        attrs.st_mode = pyfuse3.ModeT(entry.mode)
        attrs.st_size = await entry.size()
        return attrs

    async def getattr(
        self, inode: pyfuse3.InodeT, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.EntryAttributes:
        """Get attributes for a given inode"""

        entry = self.inode2entry(inode)
        return await self.get_attrs(entry)

    async def opendir(
        self, inode: pyfuse3.InodeT, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.FileHandleT:
        """Open a directory referred by a given inode"""

        # Reuse inode as directory handle
        self.logger.debug("opendir(inode=%d)", inode)
        return pyfuse3.FileHandleT(inode)

    async def readdir(
        self, fh: pyfuse3.FileHandleT, offset: int, token: pyfuse3.ReaddirToken
    ) -> None:
        """Read entries in an open directory"""

        # opendir() uses inode as directory handle
        inode = pyfuse3.InodeT(fh)
        direntry = self.inode2entry(inode)
        self.logger.debug(
            "readdir(dirname=%s, fh=%d, offset=%d)", direntry.name, fh, offset
        )
        assert isinstance(direntry, FuseDirEntry)

        next_id = offset + 1
        try:
            async for entry in direntry.get_entries(offset):
                name = pyfuse3.FileNameT(os.fsencode(entry.name))
                attrs = await self.get_attrs(entry)
                if not pyfuse3.readdir_reply(token, name, attrs, next_id):
                    break

                next_id += 1
                self._inode2entry[attrs.st_ino] = entry
        except Exception as err:
            self.logger.exception("Cannot readdir: %s", err)
            raise pyfuse3.FUSEError(errno.ENOENT)

    async def open(
        self, inode: pyfuse3.InodeT, _flags: int, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.FileInfo:
        """Open an inode and return a unique file handle"""

        # Reuse inode as file handle
        self.logger.debug("open(inode=%d)", inode)
        entry = self.inode2entry(inode)
        return pyfuse3.FileInfo(fh=pyfuse3.FileHandleT(inode), **entry.file_info_attrs)

    async def read(self, fh: pyfuse3.FileHandleT, offset: int, length: int) -> bytes:
        """Read `length` bytes from file handle `fh` at position `offset`"""

        # open() uses inode as file handle
        inode = pyfuse3.InodeT(fh)

        entry = self.inode2entry(inode)
        self.logger.debug(
            "read(name=%s, fh=%d, offset=%d, length=%d)", entry.name, fh, offset, length
        )
        assert isinstance(entry, FuseFileEntry)

        try:
            data = await entry.get_content()
            return data[offset : offset + length]
        except Exception as err:
            self.logger.exception("Cannot read: %s", err)
            raise pyfuse3.FUSEError(errno.ENOENT)

    async def lookup(
        self,
        parent_inode: pyfuse3.InodeT,
        name: pyfuse3.FileNameT,
        _ctx: pyfuse3.RequestContext,
    ) -> pyfuse3.EntryAttributes:
        """Look up a directory entry by name and get its attributes"""

        decoded_name = os.fsdecode(name)
        parent_entry = self.inode2entry(parent_inode)
        self.logger.debug(
            "lookup(parent_name=%s, parent_inode=%d, name=%s)",
            parent_entry.name,
            parent_inode,
            decoded_name,
        )
        assert isinstance(parent_entry, FuseDirEntry)

        try:
            if parent_entry.validate_entry(decoded_name):
                lookup_entry = await parent_entry.lookup(decoded_name)
                if lookup_entry:
                    return await self.get_attrs(lookup_entry)
        except Exception as err:
            self.logger.exception("Cannot lookup: %s", err)

        raise pyfuse3.FUSEError(errno.ENOENT)

    async def readlink(
        self, inode: pyfuse3.InodeT, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.FileNameT:
        entry = self.inode2entry(inode)
        self.logger.debug("readlink(name=%s, inode=%d)", entry.name, inode)
        assert isinstance(entry, FuseSymlinkEntry)
        return pyfuse3.FileNameT(os.fsencode(entry.get_target()))

    async def unlink(
        self,
        parent_inode: pyfuse3.InodeT,
        name: pyfuse3.FileNameT,
        _ctx: pyfuse3.RequestContext,
    ) -> None:
        """Remove a file"""

        decoded_name = os.fsdecode(name)
        parent_entry = self.inode2entry(parent_inode)
        self.logger.debug(
            "unlink(parent_name=%s, parent_inode=%d, name=%s)",
            parent_entry.name,
            parent_inode,
            decoded_name,
        )

        try:
            await parent_entry.unlink(decoded_name)
        except Exception as err:
            self.logger.exception("Cannot unlink: %s", err)
            raise pyfuse3.FUSEError(errno.ENOENT)

    async def getxattr(
        self,
        inode: pyfuse3.InodeT,
        name: pyfuse3.XAttrNameT,
        _ctx: pyfuse3.RequestContext,
    ) -> bytes:
        """
        This allows someone to get the extend attribute "user.swhid" on entities that
        have one (this is mostly useful when traversing source trees).
        The attribute value is a SWHID string.
        """
        if name == b"user.swhid":
            entry = self.inode2entry(inode)
            try:
                return str(entry.swhid).encode()  # type: ignore
            except AttributeError:
                pass
        raise pyfuse3.FUSEError(errno.ENOSYS)


def graph_backend_factory(conf: Dict[str, Any]) -> GraphBackend:
    if "graph" in conf:
        from swh.fuse.backends.compressed import CompressedGraphBackend

        return CompressedGraphBackend(conf)
    else:
        from swh.fuse.backends.web_api import WebApiBackend

        return WebApiBackend(conf)


def obj_backend_factory(conf: Dict[str, Any]) -> ContentBackend:
    if "content" in conf and conf["content"]:
        from swh.fuse.backends.objstorage import ObjStorageBackend

        return ObjStorageBackend(conf)
    else:
        from swh.fuse.backends.web_api import WebApiBackend

        return WebApiBackend(conf)


class SwhFsTmpMount:
    """
    This context manager will mount the Software Heritage archive on a temporary
    folder, in a separate thread running its own asyncio event loop. It returns a
    `Path <https://docs.python.org/3/library/pathlib.html>`_ object pointing to the
    mountpoint, that will be deleted when exiting the context.
    Note that the main thread will likely
    wait a bit before entering the context, until the mountpoint appears.

    Example:

    ::

        with SwhFsTmpMount() as mountpoint:
            swhid = "swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2"
            hello_world_path = mountpoint / "archive" / swhid
            print(open(hello_world_path).read())

    SwhFS will be configured as if launched via the `swh fs mount` command,
    so please set the ``SWH_CONFIG_FILE`` environment variable pointing to the relevant
    configuration file. The ``config`` parameter is intended for unit tests.

    See also :ref:`swh-fuse-parallelization`.
    """

    def __init__(self, config=None):
        if config is None:
            self.config = load_config()
        else:
            self.config = config
        self.mountpoint = Path(mkdtemp())
        self.loop = asyncio.get_event_loop_policy().get_event_loop()
        self.swhfuse = self.loop.create_task(main([], self.mountpoint, self.config))
        self.thread = Thread(target=self.loop.run_until_complete, args=(self.swhfuse,))

    def __enter__(self) -> Path:
        self.thread.start()
        for i in range(30000):
            if (self.mountpoint / "archive").exists():
                break
            else:
                time.sleep(0.01)
        else:
            raise RuntimeError("Mountpoint failed to appear after 5 minutes, aborting.")
        return self.mountpoint

    def __exit__(self, exc_type, exc_value, traceback):
        if (self.mountpoint / "archive").exists():
            run([which("fusermount3"), "-u", str(self.mountpoint)])
        rmtree(self.mountpoint, ignore_errors=True)
        return False


async def main(
    swhids: List[CoreSWHID],
    root_path: Path,
    conf: Dict[str, Any],
    content_backend: ContentBackend | None = None,
) -> None:
    """``swh-fuse`` CLI entry-point"""

    # Use pyfuse3 asyncio layer to match the rest of Software Heritage codebase
    pyfuse3.asyncio.enable()

    async with FuseCache(conf["cache"]) as cache:
        if content_backend is None:
            content_backend = obj_backend_factory(conf)
        fs = Fuse(cache, conf, graph_backend_factory(conf), content_backend)

        # Initially populate the cache
        for swhid in swhids:
            try:
                await fs.get_metadata(swhid)
            except Exception as err:
                fs.logger.exception("Cannot prefetch object %s: %s", swhid, err)

        fuse_options = set(pyfuse3.default_options)
        fuse_options.add("fsname=swhfs")

        try:
            pyfuse3.init(fs, str(root_path), fuse_options)
            await pyfuse3.main()
        except Exception as err:
            fs.logger.error("Error running FUSE: %s", err)
        finally:
            fs.shutdown()
            pyfuse3.close(unmount=True)
