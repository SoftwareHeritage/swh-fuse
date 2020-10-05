# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import errno
import itertools
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List

import pyfuse3
import pyfuse3_asyncio
import requests

from swh.fuse.cache import FuseCache
from swh.fuse.fs.entry import FuseEntry
from swh.fuse.fs.mountpoint import Root
from swh.model.identifiers import CONTENT, SWHID
from swh.web.client.client import WebAPIClient


class Fuse(pyfuse3.Operations):
    """ Software Heritage Filesystem in Userspace (FUSE). Locally mount parts of
    the archive and navigate it as a virtual file system. """

    def __init__(
        self, root_path: Path, cache: FuseCache, conf: Dict[str, Any],
    ):
        super(Fuse, self).__init__()

        self._next_inode: int = pyfuse3.ROOT_INODE
        self._next_fd: int = 0
        self._inode2entry: Dict[int, FuseEntry] = {}

        self.root = Root(fuse=self)

        self._inode2fd: Dict[int, int] = {}
        self._fd2inode: Dict[int, int] = {}
        self._inode2path: Dict[int, Path] = {self.root.inode: root_path}

        self.time_ns: int = time.time_ns()  # start time, used as timestamp
        self.gid = os.getgid()
        self.uid = os.getuid()

        self.web_api = WebAPIClient(
            conf["web-api"]["url"], conf["web-api"]["auth-token"]
        )
        self.cache = cache

    def shutdown(self) -> None:
        pass

    def _alloc_inode(self, entry: FuseEntry) -> int:
        """ Return a unique inode integer for a given entry """

        inode = self._next_inode
        self._next_inode += 1
        self._inode2entry[inode] = entry

        # TODO add inode recycling with invocation to invalidate_inode when
        # the dicts get too big

        return inode

    def _alloc_fd(self, inode: int) -> int:
        """ Return a unique file descriptor integer for a given inode """

        try:
            return self._inode2fd[inode]
        except KeyError:
            fd = self._next_fd
            self._next_fd += 1
            self._inode2fd[inode] = fd
            self._fd2inode[fd] = inode
            return fd

    def inode2entry(self, inode: int) -> FuseEntry:
        """ Return the entry matching a given inode """

        try:
            return self._inode2entry[inode]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

    def inode2path(self, inode: int) -> Path:
        """ Return the path matching a given inode """

        try:
            return self._inode2path[inode]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

    def get_metadata(self, swhid: SWHID) -> Any:
        """ Retrieve metadata for a given SWHID using Software Heritage API """

        # TODO: swh-graph API
        cache = self.cache.metadata[swhid]
        if cache:
            return cache

        try:
            metadata = self.web_api.get(swhid)
            self.cache.metadata[swhid] = metadata
            return metadata
        except requests.HTTPError:
            logging.error(f"Unknown SWHID: '{swhid}'")

    def get_blob(self, swhid: SWHID) -> str:
        """ Retrieve the blob bytes for a given content SWHID using Software
        Heritage API """

        if swhid.object_type != CONTENT:
            raise pyfuse3.FUSEError(errno.EINVAL)

        cache = self.cache.blob[swhid]
        if cache:
            return cache

        resp = list(self.web_api.content_raw(swhid))
        blob = "".join(map(bytes.decode, resp))
        self.cache.blob[swhid] = blob
        return blob

    def get_attrs(self, entry: FuseEntry) -> pyfuse3.EntryAttributes:
        """ Return entry attributes """

        attrs = pyfuse3.EntryAttributes()
        attrs.st_size = 0
        attrs.st_atime_ns = self.time_ns
        attrs.st_ctime_ns = self.time_ns
        attrs.st_mtime_ns = self.time_ns
        attrs.st_gid = self.gid
        attrs.st_uid = self.uid
        attrs.st_ino = entry.inode
        attrs.st_mode = entry.mode
        attrs.st_size = len(entry)
        return attrs

    async def getattr(
        self, inode: int, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.EntryAttributes:
        """ Get attributes for a given inode """

        entry = self.inode2entry(inode)
        return self.get_attrs(entry)

    async def opendir(self, inode: int, _ctx: pyfuse3.RequestContext) -> int:
        """ Open a directory referred by a given inode """

        # Re-use inode as directory handle
        return inode

    async def readdir(
        self, inode: int, offset: int, token: pyfuse3.ReaddirToken
    ) -> None:
        """ Read entries in an open directory """

        direntry = self.inode2entry(inode)
        path = self.inode2path(inode)

        # TODO: add cache on direntry list?
        next_id = offset + 1
        for entry in itertools.islice(direntry, offset, None):
            name = os.fsencode(entry.name)
            attrs = self.get_attrs(entry)
            if not pyfuse3.readdir_reply(token, name, attrs, next_id):
                break

            next_id += 1
            self._inode2entry[attrs.st_ino] = entry
            self._inode2path[attrs.st_ino] = Path(path, entry.name)

    async def open(
        self, inode: int, _flags: int, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.FileInfo:
        """ Open an inode and return a unique file descriptor """

        fd = self._alloc_fd(inode)
        return pyfuse3.FileInfo(fh=fd, keep_cache=True)

    async def read(self, fd: int, offset: int, length: int) -> bytes:
        """ Read `length` bytes from file descriptor `fd` at position `offset` """

        try:
            inode = self._fd2inode[fd]
            entry = self.inode2entry(inode)
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

        data = str(entry)
        return data.encode()[offset : offset + length]

    async def lookup(
        self, parent_inode: int, name: str, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.EntryAttributes:
        """ Look up a directory entry by name and get its attributes """

        name = os.fsdecode(name)
        path = Path(self.inode2path(parent_inode), name)
        parent_entry = self.inode2entry(parent_inode)

        for entry in parent_entry:
            if name == entry.name:
                attr = self.get_attrs(entry)
                self._inode2path[attr.st_ino] = path
                return attr

        logging.error(f"Unknown name during lookup: '{name}'")
        raise pyfuse3.FUSEError(errno.ENOENT)


def main(swhids: List[SWHID], root_path: Path, conf: Dict[str, Any]) -> None:
    """ swh-fuse CLI entry-point """

    # Use pyfuse3 asyncio layer to match the rest of Software Heritage codebase
    pyfuse3_asyncio.enable()

    with FuseCache(conf["cache"]) as cache:
        fs = Fuse(root_path, cache, conf)

        # Initially populate the cache
        for swhid in swhids:
            fs.get_metadata(swhid)

        fuse_options = set(pyfuse3.default_options)
        fuse_options.add("fsname=swhfs")
        fuse_options.add("debug")
        pyfuse3.init(fs, root_path, fuse_options)

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(pyfuse3.main())
            fs.shutdown()
        finally:
            pyfuse3.close(unmount=True)
            loop.close()
