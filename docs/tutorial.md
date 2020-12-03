# Software Heritage Filesystem (SwhFS) --- Tutorial


## Installation

The Software Heritage virtual filesystem (SwhFS) is available from PyPI
as [swh.fuse](https://pypi.org/project/swh.fuse/). It can be installed from
there using `pip`:

    $ pip install swh.fuse


## Setup and teardown

SwhFS is controlled by the `swh fs` command-line interface (CLI).

Like all filesystems, SwhFS must be "mounted" before use and "unmounted"
afterwards. Users should first mount the archive as a whole and then browse
archived objects looking up their SWHIDs below the `archive/` entry-point. To
mount the Software Heritage archive, use the `swh fs mount` command:

    $ mkdir swhfs
    $ swh fs mount swhfs/  # mount the archive

    $ ls -1F swhfs/  # list entry points
    archive/  # <- start browsing from here
    meta/

By default SwhFS daemonizes into background and logs to syslog; it can be kept
in foreground, logging to the console, by passing `-f/--foreground` to `mount`.

To unmount use `swh fs umount PATH`. Note that, since SwhFS is a *user-space*
filesystem, mounting and unmounting it are not privileged operations, any user
can do it.

The configuration file `~/.swh/config/global.yml` is read if present. Its main
use case is inserting a per-user authentication token for the SWH API, which
might be needed in case of heavy use to bypass the default API rate limit. See
the {ref}`configuration documentation <swh-fuse-config>` for details.


## Lazy loading

Once mounted, the archive can be navigated as if it were locally available
on-disk. Archived objects are referenced by
{ref}`Software Heritage identifiers <persistent-identifiers>` (SWHIDs).
They are loaded on-demand from the archive and populate lazily the `archive/`
directory below the SwhFS mount point.

SWHIDs for source code that is not locally available can be obtained in various
ways: searching on the [Software Heritage website][webui]; finding SWHID
references in [scientific papers][citeguide], [Wikidata][wikidataswhid], and
software bills of materials using the [SPDX standard][spdx]; deriving SWHIDs
from other version control system references (e.g., as SWHIDs version 1 are
compatible with Git, a Git commit identifier like
`9d76c0b163675505d1a901e5fe5249a2c55609bc` can be turned into a SWHID by simply
prefixing it with `swh:1:rev:` to obtain
`swh:1:rev:9d76c0b163675505d1a901e5fe5249a2c55609bc`).

[citeguide]: https://www.softwareheritage.org/save-and-reference-research-software
[spdx]: https://spdx.dev/
[swhid]: https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html
[webui]: https://archive.softwareheritage.org
[wikidataswhid]: https://www.wikidata.org/wiki/Property:P6138


## Source code files

Here is a SwhFS Hello World:

    $ cd swhfs/

    $ cat archive/swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2
    #include <stdio.h>

    int main(void) {
        printf("Hello, World!\n");
    }

Given the SWHID of a source code file, we can directly access it via the
filesystem.

Metadata about archived source code artifacts is also locally available. For
each entry under `archive/` there is a matching JSON file under `meta/`,
corresponding to what the [Software Heritage Web API][webapi] will return. For
example, here is what the Software Heritage archive knows about the above Hello
World implementation:

    $ jq meta/swh:1:cnt:c839dea9e8e6f0528b468214348fee8669b305b2.json
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


[webapi]: https://archive.softwareheritage.org/api/


## Source code trees

In addition to individual source code files, we can also browse entire source
code directories. Here is the historical Apollo 11 source code, where we can
find interesting comments about the antenna during landing:

    $ cd archive/swh:1:dir:1fee702c7e6d14395bbf5ac3598e73bcbf97b030

    $ ls | wc -l
    127

    $ grep -i antenna THE_LUNAR_LANDING.s | cut -f 5
    # IS THE LR ANTENNA IN POSITION 1 YET
    # BRANCH IF ANTENNA ALREADY IN POSITION 1

We can checkout the commit of a more modern code base, like jQuery, and count
its JavaScript lines of code (SLOC):

    $ cd archive/swh:1:rev:9d76c0b163675505d1a901e5fe5249a2c55609bc

    $ ls -F
    history/
    meta.json@
    parent@
    parents/
    root@

    $ find root/src/ -type f -name '*.js' | xargs cat | wc -l
    10136


## History browsing

`meta.json` files of revision objects contain complete commit metadata, e.g.:

    $ jq '.author.name, .date, .message' meta.json
    "Michal Golebiowski-Owczarek"
    "2020-03-02T23:02:42+01:00"
    "Data:Event:Manipulation: Prevent collisions with Object.prototype ..."

Commit history can be browsed commit-by-commit digging into directories
`parent(s)/` directories or, more efficiently, using the history summaries
located under `history/`:

    $ ls -f history/by-page/000/ | wc -l
    6469

    $ ls -f history/by-page/000/ | head -n 5
    swh:1:rev:358b769a00c3a09a8ec621b8dcb2d5e31b7da69a
    swh:1:rev:4a7fc8544e2020c75047456d11979e4e3a517fdf
    swh:1:rev:364476c3dc1231603ba61fc08068fa89fb095e1a
    swh:1:rev:721744a9fab5b597febea64e466272eabfdb9463
    swh:1:rev:4592595b478be979141ce35c693dbc6b65647173

The jQuery commit at hand is preceded by 6469 commits, which can be listed in
`git log` order via the `by-page` view. The `by-hash` and `by-date` views list
commits sharded by commit identifier and timestamp:

    $ ls history/by-hash/00/ | head -n 5
    swh:1:rev:00a9c2e5f4c855382435cec6b3908eb9bd5a53b7
    swh:1:rev:005040379d8b64aacbe54941d878efa6e86df1cc
    swh:1:rev:00cc67af23bf9cf2cdbaeaeee6ded76baf0292f0
    swh:1:rev:00575d4d8c7421c5119f181009374ff2e7736127
    swh:1:rev:0019a463bdcb81dc6ba3434505a45774ca27f363

    $ ls -F history/by-date/
    2006/
    2007/
    2008/
    ...
    2018/
    2019/
    2020/

    $ ls -f history/by-date/2020/03/16/
    swh:1:ref:90fed4b453a5becdb7f173d9e3c1492390a1441f

    $ jq .date history/by-date/2020/03/16/*/meta.json
    "2020-03-16T21:49:29+01:00"

Note that to populate the `by-date` view metadata about all commits in the
history are needed. To avoid blocking on that, metadata are retrieved
asynchronously, populating the view incrementally. The hidden `by-date/.status`
file provides a progress report and is removed upon completion.


## Repository snapshots and branches

Snapshot objects keep track of where each branch and release (or "tag") pointed
at archival time. Here is an example using
the [Unix history repository](https://github.com/dspinellis/unix-history-repo),
which uses historical Unix releases as branch names:

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

We can check that two of the available branches correspond to historical Bell
Labs UNIX releases. And We can dig into the `fortune` implementation of
[UNIX/32V](https://en.wikipedia.org/wiki/UNIX/32V) instantly, without having to
clone a 1.6  GiB repository first.
