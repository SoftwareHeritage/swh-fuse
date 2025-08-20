.. _swh-fuse-parallelization:


Advice for parallelization
==========================


SwhFS is designed to provide access to the complete archive:
users may use it to scan large portions of the archive,
if not the entire archive.
This requires parallelization.
SwhFS has been tested up to 10000 concurrent processes,
which was not trivial due to the FUSE architecture, to SwhFS being implemented in Python,
or to system constraints sometimes enforced by HPC infrastructures.
This section collects advice and tips for large deployments.

.. note::

    If you do not need to read files' contents at all, we advise you instead use
    the :ref:`compressed graph <swh-graph>` directly.

.. _swh-fuse-unshare:

Use local and fast data sources
-------------------------------

The most important thing for large scans is to use local and fast data sources
as most as possible. At the time of writing this documentation, this means:

* a :ref:`compressed graph <swh-graph>`,
* a :ref:`digestmap <swh-digestmap>`,
* a local :ref:`objstorage <swh-objstorage>`,
  or at worst its HTTP implementation pointing to S3 (see our
  :ref:`configuration examples <swh-fuse-config-teaser-graph-s3>`).

This may change over time: contact us on our
`development channels <https://www.softwareheritage.org/community/developers/>`_
to validate your architecture before launching major operations.

One mountpoint per user process with SwhFsTmpMount
--------------------------------------------------

Code scanners usually crawl each repository or source tree one by one.
This can be parallelized by launching as many instances as CPUs available,
where each instance picking in a list of directory SWHIDs to be analyzed.
However, all instances should not access the ``archive/`` folder of the same mountpoint:
due to the FUSE architecture, and SwhFS being implemented in Python,
SwhFS might become a bottleneck even when running just a dozen instances.
We instead advise you create one mountpoint per running instance of your scanner.

This can be simplified by using the :class:`swh.fuse.fuse.SwhFsTmpMount` context manager
from your batch manager, which is especially useful to dispatch work from a Python script.
In that case, be careful to also disable on-disk
caching entirely, using the ``in-memory`` and ``bypass`` settings.

How to shortcut Python startup times
------------------------------------

When creating many mountpoints you should avoid calling ``swh fs mount`` repeatedly,
because each call would start a new Python process, that has to import the many
libraries we need. This can take a few seconds per process.
Instead you can create a main Python process
that forks to subprocesses thanks to a
`ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor>`_.

.. warning::

    Importing ``swh.fuse`` does not trigger all necessary Python imports:
    the remaining ones are imported only at mounting time,
    depending on the configuration (this avoids importing all supported data
    sources' dependencies).
    Therefore, when using a ``ProcessPoolExecutor``,
    take care to mount once before creating the pool.

    SwhFS sources include an example batch manager relying on ``ProcessPoolExecutor`` and
    ``SwhFsTmpMount``, whose worker processes avoid Python startups entirely:
    `examples/parallel_processing.py <https://gitlab.softwareheritage.org/swh/devel/swh-fuse/-/blob/d82bf52/examples/parallel_processor.py>`_.


Workaround missing permissions
------------------------------

Some Linux environments may not grant you an admin access, no allow you to mount FUSE
filesystems, even if you can install ``libfuse`` and ``fusermount3``.
In that case, we advise you gain super-powers by running your batch manager program
in a Linux namespace with the appropriate options of
`unshare <https://manpages.debian.org/testing/util-linux/unshare.1.en.html>`_
(from the ``util-linux`` package):

::

    unshare --pid --kill-child --user --map-root-user --mount ./parallel_processor.py


See also
--------

The complete report on testing SwhFS over 10000 mountpoints and more is included in SwhFS' sources, in
`benchmark/README.md <https://gitlab.softwareheritage.org/swh/devel/swh-fuse/-/blob/3d2762ba/benchmark/README.md>`_.
