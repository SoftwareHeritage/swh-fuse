Software Heritage Filesystem (SwhFS) — Tutorial
===============================================

Installation
------------

The Software Heritage virtual filesystem (SwhFS) is available from PyPI as `swh.fuse
<https://pypi.org/project/swh.fuse/>`_.
It requires ``libfuse3``, that can be installed on a Debian-like system with::

   $ apt-get install fuse3 libfuse3-dev python3-dev build-essential pkg-config

Then SwhFS itself can be installed using ``pip`` -
you'll probably want to do this in `a virtual environment <https://docs.python.org/3/library/venv.html>`_.

::

   $ pip install swh.fuse

Setup and teardown
------------------

SwhFS is controlled by the ``swh fs`` command-line interface (CLI).

Like all filesystems, SwhFS must be “mounted” before use and “unmounted” afterwards.
Users should first mount the archive as a whole and then browse archived objects looking
up their SWHIDs below the ``archive/`` entry-point. To mount the Software Heritage
archive, use the ``swh fs mount`` command:

::

   $ mkdir ~/swhfs
   $ swh fs mount ~/swhfs  # mount the archive

   $ ls -1F ~/swhfs  # list entry points
   archive/  # <- start browsing from here
   cache/
   origin/
   README

To unmount use ``swh fs umount ~/swhfs``.
Note that ``sudo`` is not needed,
however on some systems you might need specific authorizations.
See :ref:`swh-fuse-unshare`.

By default SwhFS daemonizes into background and logs to syslog; it can be kept in
foreground, logging to the console, by passing the ``-f/`` (``--foreground``) option to ``mount``.
In that case, hit ``Ctrl+C`` to stop the process and unmount.


Lazy loading
------------

Once mounted, the archive can be navigated as if it were locally available on-disk.
Archived objects are referenced by
:ref:`Software Heritage identifiers <persistent-identifiers>` (SWHIDs).
They are loaded on-demand in the ``archive/`` sub-directory.

SWHIDs for source code that is not locally available can be obtained in various ways:
searching on the :swh_web:`Software Heritage website </>`; finding SWHID references in
`scientific papers
<https://www.softwareheritage.org/save-and-reference-research-software>`_, `Wikidata
<https://www.wikidata.org/wiki/Property:P6138>`_, and software bills of materials using
the `SPDX standard <https://spdx.dev/>`_; deriving SWHIDs from other version control
system references (e.g., as SWHIDs version 1 are compatible with Git, a Git commit
identifier like ``9d76c0b163675505d1a901e5fe5249a2c55609bc`` can be turned into a SWHID
by simply prefixing it with ``swh:1:rev:`` to obtain
``swh:1:rev:9d76c0b163675505d1a901e5fe5249a2c55609bc``).

Source code files
-----------------

Here is a SwhFS Hello World:

::

   $ cd swhfs/

   $ cat archive/swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2
   #include <stdio.h>

   int main(void) {
       printf("Hello, World!\n");
   }

Given the SWHID of a source code file, we can directly access it via the filesystem.

Metadata about archived source code artifacts is also locally available. For each entry
``archive/<SWHID>`` there is a matching JSON file ``archive/<SWHID>.json``,
corresponding to what the :swh_web:`Software Heritage Web API <api/>` will return.
This file is not listed by ``ls``, but created on-demand.

For
example, here is what the Software Heritage archive knows about the above Hello World
implementation:

::

   $ cat archive/swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2.json
   {
     "length": 67,
     "status": "visible",
     "checksums": {
       "sha256": "06dfb5d936f50b3cb80152aa053724e4a18417c35f745b66ab9571c25afd0f79",
       "sha1": "459ee8545e5ba6cb819ba41e6ea2f0011cedd728",
       "blake2s256": "87e6ab9c92681e9a022a8f4679dcd9d9b841fe4146edcbc15329fc66d8c82b4f",
       "sha1_git": "c839dea9e8e6f0528b468214348fee8669b305b2"
     },
     "data_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:c839dea9e8e6f0528b468214348fee8669b305b2/raw/",
     "filetype_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:c839dea9e8e6f0528b468214348fee8669b305b2/filetype/",
     "language_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:c839dea9e8e6f0528b468214348fee8669b305b2/language/",
     "license_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:c839dea9e8e6f0528b468214348fee8669b305b2/license/"
   }


Source code trees
-----------------

We can also browse entire source code directories.
Here is the historical Apollo 11 source code, where we can find interesting
comments about the antenna during landing:

::

   $ cd archive/swh:1:dir:1fee702c7e6d14395bbf5ac3598e73bcbf97b030

   $ ls | head
   AGC_BLOCK_TWO_SELF-CHECK.s
   AGC_BLOCK_TWO_SELF_CHECK.s
   AGS_INITIALIZATION.s
   ALARM_AND_ABORT.s
   ANGLFIND.s
   AOSTASK_AND_AOSJOB.s
   AOTMARK.s
   ASCENT_GUIDANCE.s
   ASSEMBLY_AND_OPERATION_INFORMATION.s
   ATTITUDE_MANEUVER_ROUTINE.s

   $ grep -i antenna THE_LUNAR_LANDING.s | cut -f 5
   # IS THE LR ANTENNA IN POSITION 1 YET
   # BRANCH IF ANTENNA ALREADY IN POSITION 1


When traversing a tree, you can get each directory and file's SWHID in an extended attribute called ``user.swhid``:

::

   $ getfattr -n user.swhid archive/swh:1:dir:1fee702c7e6d14395bbf5ac3598e73bcbf97b030/THE_LUNAR_LANDING.s
   # file: archive/swh:1:dir:1fee702c7e6d14395bbf5ac3598e73bcbf97b030/THE_LUNAR_LANDING.s
   user.swhid="swh:1:cnt:775f08d911f2c19f1498f1a994a263dbf5adf9e1"

   $ getfattr -n user.swhid archive/swh:1:rev:1976b1d33ec7c21f1d4009d9153edce2d0c5d801/root
   # file: archive/swh:1:rev:1976b1d33ec7c21f1d4009d9153edce2d0c5d801/root
   user.swhid="swh:1:dir:3736f2228bc788f8ade496d0e8fe496cef77d029"

In Python, read this attribute using the ``xattr`` package::

   import xattr
   from swh.model.swhids import CoreSWHID, ObjectType

   path = "mountpoint/archive/swh:1:dir:1fee702c7e6d14395bbf5ac3598e73bcbf97b030/THE_LUNAR_LANDING.s"
   swhid = CoreSWHID.from_string(xattr.getxattr(path, "user.swhid").decode())
   print(f"{path} is {swhid}")

   path = "mountpoint/archive/swh:1:rev:1976b1d33ec7c21f1d4009d9153edce2d0c5d801/root"
   swhid = CoreSWHID.from_string(xattr.getxattr(path, "user.swhid").decode())
   print(f"{path} is {swhid}")


Revisions
---------

SwhFS presents revisions and their whole meta-data:

::

   $ cd archive/swh:1:rev:3b1b2e77d73af48ff9fdb704b52f143b8968ff63

   $ ls -1
   history/
   meta.json@
   parent@
   parents/
   root@

   $ ls -1 root
   books
   casts
   _config.yml
   courses
   docs
   favicon.ico
   _includes
   LICENSE
   more
   README.md
   scripts


``meta.json`` contains complete commit metadata, e.g.:

::

   $ jq '.author.name, .date, .message' meta.json
   "Pradeep lal gowtham chand Gaduthuri"
   "2025-09-17T18:26:59+05:30"
   "Reorganize Algorithms and Data Structures sections in ...


The ``root`` folder is a symbolic link to the directory that will let you browse the
source tree matching that revision.


Commit history can be browsed commit-by-commit by digging into ``parent(s)/``
directories or, more efficiently, using history summaries located under
``history/``:

.. ::

..    $ ls -f history/by-page/000/ | wc -l


..    $ ls -f history/by-page/000/ | head -n 5
..    swh:1:rev:358b769a00c3a09a8ec621b8dcb2d5e31b7da69a
..    swh:1:rev:4a7fc8544e2020c75047456d11979e4e3a517fdf
..    swh:1:rev:364476c3dc1231603ba61fc08068fa89fb095e1a
..    swh:1:rev:721744a9fab5b597febea64e466272eabfdb9463
..    swh:1:rev:4592595b478be979141ce35c693dbc6b65647173

.. The jQuery commit at hand is preceded by 6469 commits, which can be listed in ``git
.. log`` order via the ``by-page`` view. The ``by-hash`` and ``by-date`` views list commits
.. sharded by commit identifier and timestamp:

.. ::

..    $ ls history/by-hash/00/ | head -n 5
..    swh:1:rev:00a9c2e5f4c855382435cec6b3908eb9bd5a53b7
..    swh:1:rev:005040379d8b64aacbe54941d878efa6e86df1cc
..    swh:1:rev:00cc67af23bf9cf2cdbaeaeee6ded76baf0292f0
..    swh:1:rev:00575d4d8c7421c5119f181009374ff2e7736127
..    swh:1:rev:0019a463bdcb81dc6ba3434505a45774ca27f363

..    $ ls -1F history/by-date/
..    2006/
..    2007/
..    2008/
..    ...
..    2018/
..    2019/
..    2020/

..    $ ls -f history/by-date/2020/03/16/
..    swh:1:ref:90fed4b453a5becdb7f173d9e3c1492390a1441f

..    $ jq .date history/by-date/2020/03/16/*/meta.json
..    "2020-03-16T21:49:29+01:00"


.. warning::

   Due to resource constraints, some back-ends may not show a complete history and you
   might have to recurse in older revisions's ``history`` folder if you want to reach
   the oldest revision. This is especially the case with the default configuration,
   that relies on the Web API.

   If you need to perform thorough studies of revisions history, we advise you
   directly query a compressed graph instead.


Repository snapshots and branches
---------------------------------

Snapshot objects keep track of where each branch and release (or “tag”) pointed at
archival time. Here is an example using the `Unix history repository
<https://github.com/dspinellis/unix-history-repo>`_, which uses historical Unix releases
as branch names:

::

   $ cd archive/swh:1:snp:2ca5d6eff8f04a671c0d5b13646cede522c64b7d

   $ ls -f refs/heads/ | wc -l
   40

   $ ls -f refs/heads/ | grep Bell
   Bell-32V-Snapshot-Development
   Bell-Release
   $ cd refs/heads/Bell-Release
   $ jq .message,.date meta.json
   "Bell 32V release\nSnapshot of the completed development branch\n\nSynthesized-from: 32v\n"
   "1979-05-02T23:26:55-05:00"

   $ grep core root/usr/src/games/fortune.c
           printf("Memory fault -- core dumped\n");

We can check that two of the available branches correspond to historical Bell Labs UNIX
releases. And we can dig into the ``fortune`` implementation of `UNIX/32V
<https://en.wikipedia.org/wiki/UNIX/32V>`_ instantly, without having to clone a 1.6  GiB
repository first.

Origin search
-------------

Origins can be accessed via the ``origin/`` top-level directory using their **encoded** URL.
SwhFS expects the percent-encoding mechanism described in `RFC 3986 <https://tools.ietf.org/html/rfc3986.html>`_.
In Python, use `urllib.parse.quote_plus <https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote_plus>`_.

::

   $ cd origin/https%3A%2F%2Fgithub.com%2Ftorvalds%2Flinux
   $ ls # this might take some time...
   2015-07-09/  2016-09-14/  2017-09-12/  2018-03-08/  2018-09-06/  ...

Each directory corresponds to a visit, containing metadata and a symlink to the visit’s
snapshot:

::

   $ ls -l origin/https%3A%2F%2Fgithub.com%2Ftorvalds%2Flinux/2020-09-21/
   total 0
   -r--r--r-- 1 haltode haltode 470 Dec 28 12:12 meta.json
   lr--r--r-- 1 haltode haltode  67 Dec 28 12:12 snapshot -> ../../../archive/swh:1:snp:c7beb2432b7e93c4cf6ab09cd194c7c1998df2f9/

In order to find origin URLs, we can use the ``web search`` CLI:

::

   $ swh web search python --limit 5
   https://github.com/neon670/python.dev   https://archive.softwareheritage.org/api/1/origin/https://github.com/neon670/python.dev/visits/
   https://github.com/aur-archive/python-werkzeug  https://archive.softwareheritage.org/api/1/origin/https://github.com/aur-archive/python-werkzeug/visits/
   https://github.com/jsagon/jtradutor-web-python  https://archive.softwareheritage.org/api/1/origin/https://github.com/jsagon/jtradutor-web-python/visits/
   https://github.com/zjmwqx/ipythonCode   https://archive.softwareheritage.org/api/1/origin/https://github.com/zjmwqx/ipythonCode/visits/
   https://github.com/knutab/Python-BSM    https://archive.softwareheritage.org/api/1/origin/https://github.com/knutab/Python-BSM/visits/

The ``search`` tool is also useful to escape URL:

::

   $ swh web search "torvalds linux" --limit 1 --url-encode | cut -f1
   https%3A%2F%2Fgithub.com%2Ftorvalds%2Flinux


Going faster with local data
----------------------------

The default configuration uses Software Heritage's public Web API.
Although easier to set up, this is slow and rate-limited.
For example, you would have to wait one hour to count Markdown lines
in this revision of Git::

   $ cd archive/swh:1:rev:1a8a4971cc6c179c4dd711f4a7f5d7178f4b3ab7

   $ find root/ -type f -name '*.md' | xargs cat | wc -l
   1300

But there are only 11 Markdown files in this repository.
Thanks to its cache, SwhFS is slow only on first access.
But this means that the default configuration is usable only for repeated accesses
to a small subset of the archive.

You can speed up SwhFS significantly by using local data:

* a :ref:`compressed graph <swh-graph>`, available via its gRPC server. It will provide
  the repositories' structure, that SwhFS turns into folders and meta-data files.
* an :ref:`object storage <swh-objstorage>` that will provide files contents.
* a :ref:`digestmap <swh-digestmap>`, because the graph identifies contents by SWHIDs
  whereas most of our object stores identify contents by ``sha1`` or ``sha256`` (as of
  2025). The digestmap will help SwhFS to match identifiers.

Instructions below will guide you through the installation of these programs and the
download of sample data. This requires 550GB of storage available.

.. warning::

   The compressed graph is faster, also because it shows the raw data. This raw data may
   differ from the WebAPI when traversing the archive by
   origin or revisions. For example, the graph does not provide
   ``origin/YYYY-MM-DD/HEAD``, nor hides missing references (this may happen with
   git submodules).

First, we need to install SwhFS with the ``hpc`` optional dependency::

   $ pip install swh.fuse[hpc]

Install the graph (cf. :ref:`swh-graph's instructions <swh-graph-quickstart>` for more options)::

   $ apt install cargo openssl-dev protobuf-compiler
   $ RUSTFLAGS="-C target-cpu=native" cargo install --locked --git https://gitlab.softwareheritage.org/swh/devel/swh-graph.git swh-graph-grpc-server

Now we need to download data:

* the :ref:`2025-05-18-popular-1k <graph-dataset-2025-05-18-popular-1k>` compressed graph,
* its corresponding digestmap,
* and a `SquashFS <https://www.kernel.org/doc/html/v6.15/filesystems/squashfs.html>`_ file
  that contains and compresses files referenced from that graph.

Those can be downloaded from S3, so we also install ``awscli``:

::

   $ pip install awscli
   $ mkdir -p swhdata/2025-05-18-popular-1k/compressed swhdata/2025-05-18-popular-1k/digestmap swhdata/objstore
   $ aws s3 cp --no-sign-request --recursive s3://softwareheritage/graph/2025-05-18-popular-1k/compressed/ swhdata/2025-05-18-popular-1k/compressed/
   $ aws s3 cp --no-sign-request --recursive s3://softwareheritage/derived_datasets/2025-05-18-popular-1k/digestmap/ swhdata/2025-05-18-popular-1k/digestmap/
   $ aws s3 cp --no-sign-request s3://softwareheritage/content_shards/2025-05-18-popular-1k/2025-05-18-popular-1k-contents-Max100Kb-pathsliced-02-05.sqfs swhdata/

.. note::

   Origins included in that teaser graph are listed in the graph's parent folder, in
   `origins.txt <https://softwareheritage.s3.amazonaws.com/graph/2025-05-18-popular-1k/origins.txt>`_.


The SquashFS file has been created for the purpose of this tutorial. To keep it in a
tractable size range, it does not contain files bigger than 100kb (uncompressed).
This filtering removes only 8% of files while cutting the container's size by 4. As we'll see
below, we can still connect to the Internet to fetch missing files on the fly.
It contains objects organized in files and folders as does the ``pathslicing``
objstorage class, that we will use as a reader (cf. :py:class:`swh.objstorage.backends.pathslicing.PathSlicer`).

We have to mount the SquashFS first:

::

   sudo mount -t squashfs -o loop swhdata/2025-05-18-popular-1k-contents-Max100Kb-pathsliced-02-05.sqfs swhdata/objstore/

Then we start the graph's gRPC server, in another terminal.
We only load the "forward" graph because SwhFS always follow edges in their forward direction.

::

   RUST_LOG=WARN swh-graph-grpc-serve --direction=forward  ~/swhdata/2025-05-18-popular-1k/compressed/graph


Configure SwhFS to use these services and data by
editing ``$HOME/.config/swh/global.yml`` as follows,
replacing ``HOME`` with your own ``$HOME`` folder:

::

   swh:
      fuse:
         cache:
            metadata:
               in-memory: true
            blob:
               bypass: true
            direntry:
               maxram: "10%"
         graph:
            grpc-url: localhost:50091
         content:
            storage:
               cls: digestmap
               path: "HOME/swhdata/2025-05-18-popular-1k/digestmap/"
            objstorage:
               cls: multiplexer
               readonly: true
               objstorages:
                  - cls: pathslicing
                    root: HOME/swhdata/objstore/
                    slicing: 0:2/0:5
                    compression: none
                  - cls: http
                    url: https://softwareheritage.s3.amazonaws.com/content/
                    compression: gzip
                    retry:
                    total: 3
                    backoff_factor: 0.2
                    status_forcelist:
                        - 404
                        - 500


.. note::

  This configuration minimizes caching and makes it non-persistent, as we will almost
  always use local data.


Finally, we can mount SwhFS:

::

   swh fs mount ~/swhfs


Looking back at our example, with this configuration counting Markdown lines in Git
now only takes a second on a laptop. This allows you to run more I/O-hungry tasks,
like ``grep`` in a bigger repository like the Rust source, in 3 minutes:

::

   ~/swhfs $ /usr/bin/time grep -rl panic archive/swh:1:dir:c1cededa300478e23f6065a9fe8df8a3c14563ca | wc -l
   grep: ./tests/ui/associated-type-bounds/name-same-as-generic-type-issue-128249.stderr: No such file or directory
   grep: ./tests/ui/generic-associated-types/gat-trait-path-missing-lifetime.rs: No such file or directory
   grep: ./tests/ui/async-await/in-trait/generics-mismatch.rs: No such file or directory
   grep: ./tests/ui/type-alias-impl-trait/generic-not-strictly-equal.basic.stderr: No such file or directory
   grep: ./tests/ui/type-alias-impl-trait/nested-tait-inference2.next.stderr: No such file or directory
   grep: ./tests/ui/consts/const-eval/panic-never-type.stderr: No such file or directory
   grep: ./tests/ui/lint/unaligned_references.rs: No such file or directory
   grep: ./tests/rustdoc-ui/intra-doc/.gitattributes: No such file or directory
   grep: ./tests/run-make/raw-dylib-c/rmake.rs: No such file or directory
   grep: ./tests/run-make/cross-lang-lto-upstream-rlibs/rmake.rs: No such file or directory
   grep: ./tests/run-make/zero-extend-abi-param-passing/rmake.rs: No such file or directory
   grep: ./src/librustdoc/html/render/sorted_template/tests.rs: No such file or directory
   grep: ./src/doc/rustc-dev-guide/src/building/compiler-documenting.md: No such file or directory
   grep: ./library/test/src/types.rs: No such file or directory
   Command exited with non-zero status 2
   0.31user 1.27system 3:13.14elapsed 0%CPU (0avgtext+0avgdata 4260maxresident)
   32inputs+40outputs (0major+1207minor)pagefaults 0swaps
   3523

Note that a few files are missing: they are missing from both the SquashFS and S3.
Those cases are very rare, but should be expected when scanning repositories thoroughly.
This will hopefully be fixed in future releases.
