# Software Heritage Filesystem (SwhFS) --- Design notes

The [Software Heritage](https://www.softwareheritage.org/)
{ref}`data model <data-model>` is
a [Direct Acyclic Graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph)
(DAG) with nodes of different types that correspond to source code artifacts
such as directories, commits, etc. Using
this [FUSE](https://en.wikipedia.org/wiki/Filesystem_in_Userspace) module
(*SwhFS* for short) you can locally mount, and then navigate as a
filesystem, parts of the archive identified by
{ref}`Software Heritage identifiers <persistent-identifiers>` (SWHIDs).

To retrieve information about the source code artifacts, SwhFS interacts over
the network with the Software Heritage archive via its
{ref}`Web API <swh-web-api-urls>`.


## Architecture

SwhFS in context ([C4](https://en.wikipedia.org/wiki/C4_model) context
diagram):

```{image} images/arch-context.svg
:align: center
```

Main components of SwhFS (C4 container diagram):

```{image} images/arch-container.svg
:align: center
```


## Command-line interface

    $ swh fs mount <DIR> [SWHID]...

will mount the Software Heritage archive at the local `<DIR>`, the *SwhFS mount
point*. From there, the user will be able to lazily load and navigate the
archive using SWHID at entry points.

If one or more SWHIDs are also specified, the corresponding objects will be pre-
fetched from the archive at mount-time and available at `<DIR>/archive/<SWHID>`.

For more details see the {ref}`CLI documentation <swh-fuse-cli>`.


## Mount point

The SwhFS mount point contain:

- `archive/`: initially empty, this directory is lazily populated with one entry
  per accessed SWHID, having actual SWHIDs as names (possibly sharded into
  `xy/../SWHID` paths to avoid overcrowding `archive/`).

- `meta/`: initially empty, this directory contains one `<SWHID>.json` file for
  each `<SWHID>` entry under `archive/`. The JSON file contain all available
  meta information about the given SWHID, as returned by the Software Heritage
  Web API for that object. Note that, in case of pagination (e.g., snapshot
  objects with many branches) the JSON file will contain a complete version with
  all pages merged together.

- `origin/`: initially empty, this directory is lazily populated with one entry
  per accessed origin URL, having encoded URL as names. The URL encoding is done
  using the percent-encoding mechanism described in
  [RFC 3986](https://tools.ietf.org/html/rfc3986.html).


## File system representation

SWHID are represented differently on the file-system depending on the associated
node types in the Software Heritage graph. Details are given below, for each
node type.


### `cnt` nodes (blobs)

Content leaves (AKA blobs) are represented on disks as regular files, containing
the corresponding bytes, as archived.

Note that permissions are associated to blobs only in the context of
directories. Hence, when accessing blobs from the top-level `archive/`
directory, the permissions of the `archive/SWHID` file will be arbitrary and not
meaningful (e.g., `0x644`).


### `dir` nodes (directories)

Directory nodes are represented as directories on the file-system, containing
one entry for each entry of the archived directory. Entry names and other
metadata, including permissions, will correspond to the archived entry metadata.

Note that SwhFS is mounted read-only, no matter what the permissions say. So it
is possible that, in the context of a directory, a file is presented as
writable, whereas actually writing to it will fail with `EPERM`.


### `rev` nodes (commits)

Revision (AKA commit) nodes are represented on the file-system as directories
with the following entries:

- `root`: source tree at the time of the commit, as a symlink pointing into
  `archive/`, to a SWHID of type `dir`
- `parents/` (note the plural): a virtual directory containing entries named
  `1`, `2`, `3`, etc., one for each parent commit. Each of these entry is a
  symlink pointing into `archive/`, to the SWHID file for the given parent
  commit
- `parent` (note the singular): present if and only if the current commit has at
  least one parent commit (which is the most common case). When present it is a
  symlink pointing into `parents/1/`
- `history`: a virtual directory listing all its revision ancestors, sorted in
  reverse topological order. The history can be listed through `by-date/`,
  `by-hash/` or `by-page/` with each its own sharding policy.
- `meta.json`: metadata for the current node, as a symlink pointing to the
  relevant `meta/<SWHID>.json` file


### `rel` nodes (releases)

Release nodes are represented on the file-system as directories with the
following entries:

- `target`: target node, as a symlink to `archive/<SWHID>`
- `target_type`: regular file containing the type of the target SWHID
- `root`: present if and only if the release points to something that
  (transitively) resolves to a directory. When present it is a symlink pointing
  into `archive/` to the SWHID of the given directory
- `meta.json`: metadata for the current node, as a symlink pointing to the
  relevant `meta/<SWHID>.json` file


### `snp` nodes (snapshots)

Snapshot nodes are represented on the file-system as recursive directories
following the branch names structure. For example, a branch named
``refs/tags/v1.0`` will be represented as a ``refs`` directory containing a
``tags`` directory containing a ``v1.0`` symlink pointing to the branch
target SWHID.


### `ori` nodes (origins)

Origin nodes are represented on the file-system as directories with one entry
for each origin visit.

The visits directories are named after the visit date (`YYYY-MM-DD`, if multiple
visits occur the same day only the first one is kept).  Each visit directory
contains a `meta.json` with associated metadata for the origin node, and
potentially a `snapshot` symlink pointing to the visit's snapshot node.


## Caching

SwhFS retrieves both metadata and file contents from the Software Heritage
archive via the network. In order to obtain reasonable performances several
caches are used to minimize network transfer.

Caches are stored on disk in SQLite DB(s) located under
`$XDG_CACHE_HOME/swh/fuse/`.

```{todo}

- potential improvement: store blobs larger than a threshold on disk as files
rather than in SQLite, e.g., under `$XDG_CACHE_HOME/swh/fuse/objects/`

```

All caches are persistent (i.e., they survive the restart of the SwhFS process)
and global (i.e., they are shared by concurrent SwhFS processes).

We assume that no cache *invalidation* is necessary, due to intrinsic properties
of the Software Heritage archive, such as integrity verification and append-only
archive changes. To clean the caches one can just remove the corresponding files
from disk.


### Metadata cache

    Artifact id → JSON metadata

The metadata cache map each artifact to the complete metadata of the referenced
object. This is analogous to what is available in `meta/<SWHID>.json` file (and
generally used as data source for returning the content of those files).
Artifacts are identified using their SWHIDs, or in the case of origin visits,
using their URLs.

Cache location on-disk: `$XDG_CACHE_HOME/swh/fuse/metadata.sqlite`


### Blob cache

    cnt SWHID → bytes

The blob cache map SWHIDs of type `cnt` to the bytes of their archived content.

In general, each SWHID that has an entry in the blob cache also has a matching
entry in the metadata cache for other blob attributes (e.g., checksums, size,
etc.).

The blob cache entry for a given content object is populated, at the latest, the
first time the object is `open()`-d. It might be populated earlier on due to
prefetching, e.g., when a directory pointing to the given content is listed for
the first time.

Cache location on-disk: `$XDG_CACHE_HOME/swh/fuse/blob.sqlite`


### History cache

    rev SWHID → ancestor SWHIDs

The history cache map SWHIDs of type `rev` to a list of `rev` SWHIDs
corresponding to all its revision ancestors, sorted in reverse topological
order. As the parents cache, the history cache is lazily populated and can be
prefetched. To efficiently store the ancestor lists, the history cache
represents ancestors as graph edges (a pair of two SWHID nodes), meaning the
history cache is shared amongst all revisions parents.

Cache location on-disk: `$XDG_CACHE_HOME/swh/fuse/metadata.sqlite`


### Direntry cache

    dir inode → directory entries

The direntry cache map inode representing directories to the entries they
contain. Each entry comes with its name as well as file attributes (i.e., all
its needed to perform a detailed directory listing).

Additional attributes of each directory entry should be looked up on a entry by
entry basis, possibly hitting the metadata cache.

The direntry cache for a given dir is populated, at the latest, when the content
of the directory is listed. More aggressive prefetching might happen. For
instance, when first opening a dir a recursive listing of it can be retrieved
from the remote backend and used to recursively populate the direntry cache for
all (transitive) sub-directories.

Cache location: in-memory.
