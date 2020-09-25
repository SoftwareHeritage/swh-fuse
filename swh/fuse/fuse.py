# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import asyncio
import errno
import itertools
import os
from pathlib import Path
import time
from typing import Dict

import pyfuse3
import pyfuse3_asyncio
import requests

from swh.fuse.cache import Cache
from swh.fuse.fs.artifact import Content, Directory
from swh.fuse.fs.entry import (
    ARCHIVE_ENTRY,
    META_ENTRY,
    ROOT_ENTRY,
    ArtifactEntry,
    EntryMode,
    VirtualEntry,
)
from swh.fuse.fs.mountpoint import Archive, Meta, Root
from swh.model.identifiers import CONTENT, DIRECTORY, SWHID, parse_swhid
from swh.web.client.client import WebAPIClient

# Use pyfuse3 asyncio layer to match the rest of Software Heritage codebase
pyfuse3_asyncio.enable()


class Fuse(pyfuse3.Operations):
    def __init__(
        self, root_swhid: SWHID, root_path: Path, cache_dir: Path, api_url: str
    ):
        super(Fuse, self).__init__()

        # TODO check if root_swhid actually exists in the graph

        root_inode = pyfuse3.ROOT_INODE
        self._inode2entry: Dict[int, VirtualEntry] = {root_inode: ROOT_ENTRY}
        self._entry2inode: Dict[VirtualEntry, int] = {ROOT_ENTRY: root_inode}
        self._entry2fd: Dict[VirtualEntry, int] = {}
        self._fd2entry: Dict[int, VirtualEntry] = {}
        self._inode2path: Dict[int, Path] = {root_inode: root_path}

        self._next_inode: int = root_inode + 1
        self._next_fd: int = 0

        self.time_ns: int = time.time_ns()  # start time, used as timestamp
        self.gid = os.getgid()
        self.uid = os.getuid()

        self.web_api = WebAPIClient(api_url)
        self.cache = Cache(cache_dir)

        # Initially populate the cache
        self.get_metadata(root_swhid)

    def _alloc_inode(self, entry: VirtualEntry) -> int:
        try:
            return self._entry2inode[entry]
        except KeyError:
            inode = self._next_inode
            self._next_inode += 1
            self._entry2inode[entry] = inode
            self._inode2entry[inode] = entry

            # TODO add inode recycling with invocation to invalidate_inode when
            # the dicts get too big

            return inode

    def _alloc_fd(self, entry: VirtualEntry) -> int:
        try:
            return self._entry2fd[entry]
        except KeyError:
            fd = self._next_fd
            self._next_fd += 1
            self._entry2fd[entry] = fd
            self._fd2entry[fd] = entry
            return fd

    def inode2entry(self, inode: int) -> VirtualEntry:
        try:
            return self._inode2entry[inode]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

    def entry2inode(self, entry: VirtualEntry) -> int:
        try:
            return self._entry2inode[entry]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

    def inode2path(self, inode: int) -> Path:
        try:
            return self._inode2path[inode]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

    def get_metadata(self, swhid: SWHID):
        # TODO: swh-graph API
        cache = self.cache.get_metadata(swhid)
        if cache:
            return cache

        metadata = self.web_api.get(swhid)
        self.cache.put_metadata(swhid, metadata)
        return metadata

    def get_blob(self, swhid: SWHID):
        if swhid.object_type != CONTENT:
            return None

        cache = self.cache.get_blob(swhid)
        if cache:
            return cache

        metadata = self.get_metadata(swhid)
        blob = requests.get(metadata["data_url"]).text
        self.cache.put_blob(swhid, blob)
        return blob

    def get_direntries(self, entry: VirtualEntry):
        if isinstance(entry, ArtifactEntry):
            if entry.swhid.object_type == CONTENT:
                raise pyfuse3.FUSEError(errno.ENOTDIR)

            metadata = self.get_metadata(entry.swhid)
            if entry.swhid.object_type == CONTENT:
                return Content(metadata)
            if entry.swhid.object_type == DIRECTORY:
                return Directory(metadata)
            # TODO: add other objects
        else:
            if entry == ROOT_ENTRY:
                return Root()
            elif entry == ARCHIVE_ENTRY:
                return Archive(self.cache)
            elif entry == META_ENTRY:
                return Meta(self.cache)
            # TODO: error handling

    def get_attrs(self, entry: VirtualEntry, prefetch=None) -> pyfuse3.EntryAttributes:
        attrs = pyfuse3.EntryAttributes()
        attrs.st_size = 0
        attrs.st_atime_ns = self.time_ns
        attrs.st_ctime_ns = self.time_ns
        attrs.st_mtime_ns = self.time_ns
        attrs.st_gid = self.gid
        attrs.st_uid = self.uid
        attrs.st_ino = self._alloc_inode(entry)

        if isinstance(entry, ArtifactEntry):
            metadata = prefetch or self.get_metadata(entry.swhid)
            if entry.swhid.object_type == CONTENT:
                attrs.st_mode = int(EntryMode.RDONLY_FILE)
                # Only the directory API prefetch stores the permissions
                if prefetch:
                    attrs.st_mode = metadata["perms"]
                attrs.st_size = metadata["length"]
            else:
                attrs.st_mode = int(EntryMode.RDONLY_DIR)
        else:
            attrs.st_mode = int(entry.mode)
            if entry.name.endswith(".json"):
                filename = Path(entry.name).stem
                swhid = parse_swhid(filename)
                metadata = self.get_metadata(swhid)
                attrs.st_size = len(str(metadata))

        return attrs

    async def getattr(self, inode, ctx):
        entry = self.inode2entry(inode)
        return self.get_attrs(entry)

    async def opendir(self, inode, ctx):
        # Re-use inode as directory handle
        return inode

    async def readdir(self, inode, offset, token):
        direntry = self.inode2entry(inode)
        path = self.inode2path(inode)

        # TODO: add cache on direntry list?
        entries = self.get_direntries(direntry)
        current_id = offset
        for entry in itertools.islice(entries, offset, None):
            # The directory API has extra info we can use to set attributes
            # without additional SWH API call
            prefetch = None
            if isinstance(entries, Directory):
                prefetch = entries.json[current_id]

            attrs = self.get_attrs(entry, prefetch)
            next_id = current_id + 1
            if not pyfuse3.readdir_reply(
                token, os.fsencode(entry.name), attrs, next_id
            ):
                break

            current_id = next_id
            self._inode2entry[attrs.st_ino] = entry
            self._inode2path[attrs.st_ino] = Path(path, entry.name)

    async def open(self, inode, flags, ctx):
        entry = self.inode2entry(inode)
        fd = self._alloc_fd(entry)
        return pyfuse3.FileInfo(fh=fd, keep_cache=True)

    async def read(self, fd, offset, length):
        try:
            entry = self._fd2entry[fd]
        except KeyError:
            raise pyfuse3.FUSEError(errno.ENOENT)

        if isinstance(entry, ArtifactEntry):
            blob = self.get_blob(entry.swhid)
            return blob.encode()
        else:
            if entry.name.endswith(".json"):
                filename = Path(entry.name).stem
                swhid = parse_swhid(filename)
                metadata = self.get_metadata(swhid)
                return str(metadata).encode()
            else:
                # TODO: error handling?
                pass

    async def lookup(self, parent_inode, name, ctx):
        name = os.fsdecode(name)
        path = Path(self.inode2path(parent_inode), name)

        parent_entry = self.inode2entry(parent_inode)
        if isinstance(parent_entry, ArtifactEntry):
            metadata = self.get_metadata(parent_entry.swhid)
            for entry in metadata:
                if entry["name"] == name:
                    swhid = entry["target"]
                    attr = self.get_attrs(ArtifactEntry(name, swhid))
                    self._inode2path[attr.st_ino] = path
                    return attr

        # TODO: error handling (name not found)
        return pyfuse3.EntryAttributes()


def main(root_swhid: SWHID, root_path: Path, cache_dir: Path, api_url: str) -> None:
    fs = Fuse(root_swhid, root_path, cache_dir, api_url)

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
