# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import errno
import functools
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List
import urllib.parse

import pyfuse3
import pyfuse3_asyncio
import requests

from swh.fuse import LOGGER_NAME
from swh.fuse.cache import FuseCache
from swh.fuse.fs.entry import FuseDirEntry, FuseEntry, FuseFileEntry, FuseSymlinkEntry
from swh.fuse.fs.mountpoint import Root
from swh.model.identifiers import CONTENT, REVISION, SWHID
from swh.web.client.client import WebAPIClient


class Fuse(pyfuse3.Operations):
    """ Software Heritage Filesystem in Userspace (FUSE). Locally mount parts of
    the archive and navigate it as a virtual file system. """

    def __init__(
        self, root_path: Path, cache: FuseCache, conf: Dict[str, Any],
    ):
        super(Fuse, self).__init__()

        self._next_inode: int = pyfuse3.ROOT_INODE
        self._inode2entry: Dict[int, FuseEntry] = {}

        self.root = Root(fuse=self)
        self.conf = conf
        self.logger = logging.getLogger(LOGGER_NAME)

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

    def inode2entry(self, inode: int) -> FuseEntry:
        """ Return the entry matching a given inode """

        try:
            return self._inode2entry[inode]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

    async def get_metadata(self, swhid: SWHID) -> Any:
        """ Retrieve metadata for a given SWHID using Software Heritage API """

        cache = await self.cache.metadata.get(swhid)
        if cache:
            return cache

        try:
            typify = False  # Get the raw JSON from the API
            # TODO: async web API
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(None, self.web_api.get, swhid, typify)
            await self.cache.metadata.set(swhid, metadata)
            # Retrieve it from cache so it is correctly typed
            return await self.cache.metadata.get(swhid)
        except requests.HTTPError as err:
            self.logger.error("Cannot fetch metadata for object %s: %s", swhid, err)
            raise

    async def get_blob(self, swhid: SWHID) -> bytes:
        """ Retrieve the blob bytes for a given content SWHID using Software
        Heritage API """

        if swhid.object_type != CONTENT:
            raise pyfuse3.FUSEError(errno.EINVAL)

        # Make sure the metadata cache is also populated with the given SWHID
        await self.get_metadata(swhid)

        cache = await self.cache.blob.get(swhid)
        if cache:
            self.logger.debug("Found blob %s in cache", swhid)
            return cache

        try:
            self.logger.debug("Retrieving blob %s via web API...", swhid)
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, self.web_api.content_raw, swhid)
            blob = b"".join(list(resp))
            await self.cache.blob.set(swhid, blob)
            return blob
        except requests.HTTPError as err:
            self.logger.error("Cannot fetch blob for object %s: %s", swhid, err)
            raise

    async def get_history(self, swhid: SWHID) -> List[SWHID]:
        """ Retrieve a revision's history using Software Heritage Graph API """

        if swhid.object_type != REVISION:
            raise pyfuse3.FUSEError(errno.EINVAL)

        cache = await self.cache.history.get(swhid)
        if cache:
            self.logger.debug(
                "Found history of %s in cache (%d ancestors)", swhid, len(cache)
            )
            return cache

        try:
            # Use the swh-graph API to retrieve the full history very fast
            self.logger.debug("Retrieving history of %s via graph API...", swhid)
            call = f"graph/visit/edges/{swhid}?edges=rev:rev"
            loop = asyncio.get_event_loop()
            history = await loop.run_in_executor(None, self.web_api._call, call)
            await self.cache.history.set(history.text)
            # Retrieve it from cache so it is correctly typed
            res = await self.cache.history.get(swhid)
            return res
        except requests.HTTPError as err:
            self.logger.error("Cannot fetch history for object %s: %s", swhid, err)
            # Ignore exception since swh-graph does not necessarily contain the
            # most recent artifacts from the archive. Computing the full history
            # from the Web API is too computationally intensive so simply return
            # an empty list.
            return []

    async def get_visits(self, url_encoded: str) -> List[Dict[str, Any]]:
        """ Retrieve origin visits given an encoded-URL using Software Heritage API """

        cache = await self.cache.metadata.get_visits(url_encoded)
        if cache:
            self.logger.debug(
                "Found %d visits for origin '%s' in cache", len(cache), url_encoded,
            )
            return cache

        try:
            self.logger.debug(
                "Retrieving visits for origin '%s' via web API...", url_encoded
            )
            typify = False  # Get the raw JSON from the API
            loop = asyncio.get_event_loop()
            # Web API only takes non-encoded URL
            url = urllib.parse.unquote_plus(url_encoded)

            origin_exists = await loop.run_in_executor(
                None, self.web_api.origin_exists, url
            )
            if not origin_exists:
                raise ValueError("origin does not exist")

            visits_it = await loop.run_in_executor(
                None, functools.partial(self.web_api.visits, url, typify=typify)
            )
            visits = list(visits_it)
            await self.cache.metadata.set_visits(url_encoded, visits)
            # Retrieve it from cache so it is correctly typed
            res = await self.cache.metadata.get_visits(url_encoded)
            return res
        except (ValueError, requests.HTTPError) as err:
            self.logger.error(
                "Cannot fetch visits for origin '%s': %s", url_encoded, err
            )
            raise

    async def get_attrs(self, entry: FuseEntry) -> pyfuse3.EntryAttributes:
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
        attrs.st_size = await entry.size()
        return attrs

    async def getattr(
        self, inode: int, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.EntryAttributes:
        """ Get attributes for a given inode """

        entry = self.inode2entry(inode)
        return await self.get_attrs(entry)

    async def opendir(self, inode: int, _ctx: pyfuse3.RequestContext) -> int:
        """ Open a directory referred by a given inode """

        # Re-use inode as directory handle
        self.logger.debug("opendir(inode=%d)", inode)
        return inode

    async def readdir(self, fh: int, offset: int, token: pyfuse3.ReaddirToken) -> None:
        """ Read entries in an open directory """

        # opendir() uses inode as directory handle
        inode = fh
        direntry = self.inode2entry(inode)
        self.logger.debug(
            "readdir(dirname=%s, fh=%d, offset=%d)", direntry.name, fh, offset
        )
        assert isinstance(direntry, FuseDirEntry)

        next_id = offset + 1
        try:
            async for entry in direntry.get_entries(offset):
                name = os.fsencode(entry.name)
                attrs = await self.get_attrs(entry)
                if not pyfuse3.readdir_reply(token, name, attrs, next_id):
                    break

                next_id += 1
                self._inode2entry[attrs.st_ino] = entry
        except Exception as err:
            self.logger.exception("Cannot readdir: %s", err)
            raise pyfuse3.FUSEError(errno.ENOENT)

    async def open(
        self, inode: int, _flags: int, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.FileInfo:
        """ Open an inode and return a unique file handle """

        # Re-use inode as file handle
        self.logger.debug("open(inode=%d)", inode)
        return pyfuse3.FileInfo(fh=inode, keep_cache=True)

    async def read(self, fh: int, offset: int, length: int) -> bytes:
        """ Read `length` bytes from file handle `fh` at position `offset` """

        # open() uses inode as file handle
        inode = fh

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
        self, parent_inode: int, name: str, _ctx: pyfuse3.RequestContext
    ) -> pyfuse3.EntryAttributes:
        """ Look up a directory entry by name and get its attributes """

        name = os.fsdecode(name)
        parent_entry = self.inode2entry(parent_inode)
        self.logger.debug(
            "lookup(parent_name=%s, parent_inode=%d, name=%s)",
            parent_entry.name,
            parent_inode,
            name,
        )
        assert isinstance(parent_entry, FuseDirEntry)

        try:
            lookup_entry = await parent_entry.lookup(name)
            if lookup_entry:
                return await self.get_attrs(lookup_entry)
        except Exception as err:
            self.logger.exception("Cannot lookup: %s", err)

        raise pyfuse3.FUSEError(errno.ENOENT)

    async def readlink(self, inode: int, _ctx: pyfuse3.RequestContext) -> bytes:
        entry = self.inode2entry(inode)
        self.logger.debug("readlink(name=%s, inode=%d)", entry.name, inode)
        assert isinstance(entry, FuseSymlinkEntry)
        return os.fsencode(entry.get_target())


async def main(swhids: List[SWHID], root_path: Path, conf: Dict[str, Any]) -> None:
    """ swh-fuse CLI entry-point """

    # Use pyfuse3 asyncio layer to match the rest of Software Heritage codebase
    pyfuse3_asyncio.enable()

    async with FuseCache(conf["cache"]) as cache:
        fs = Fuse(root_path, cache, conf)

        # Initially populate the cache
        for swhid in swhids:
            try:
                await fs.get_metadata(swhid)
            except Exception as err:
                fs.logger.exception("Cannot prefetch object %s: %s", swhid, err)

        fuse_options = set(pyfuse3.default_options)
        fuse_options.add("fsname=swhfs")

        try:
            pyfuse3.init(fs, root_path, fuse_options)
            await pyfuse3.main()
        except Exception as err:
            fs.logger.error("Error running FUSE: %s", err)
        finally:
            fs.shutdown()
            pyfuse3.close(unmount=True)
