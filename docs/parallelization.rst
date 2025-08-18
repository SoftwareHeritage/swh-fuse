.. _swh-fuse-parallelization:


Advices for parallelization
===========================


SwhFS is designed to provide access to the complete archive:
users may use it to scan large portions of the archive,
if not the entire archive.
This requires parallelization.
SwhFS has been tested up to 10000 concurrent processes,
which was not trivial due to the FUSE architecture, to SwhFS being implemented in Python,
or to system constraints sometimes enforced by HPC infrastructures.
This section collects advices and tips for large deployments.

.. note::

    If you do not need to read files' contents at all, we advise you instead use
    the :ref:`compressed graph <swh-graph>` directly.

.. _swh-fuse-unshare:

Use local/fast data sources
---------------------------

The most important thing for such deployments is to use local and fast data sources
as most as possible. At the time of writing this documentation, this means:

 * :ref:`compressed graph <swh-graph>`,
 * a :ref:`digestmap <swh-digestmap>`,
 * a local :ref:`objstorage <swh-objstorage>`,
   or at worst the HTTP class pointing to S3 (see our
   :ref:`configuration examples <swh-fuse-config-teaser-graph-s3>).

This may change over time: contact us on our
`development channels <https://www.softwareheritage.org/community/developers/>`_
to validate your architecture before launching major operations.

One mountpoint per user process with SwhFsTmpMount
--------------------------------------------------

Large-scale scans usually rely on programs that crawl each repository or source tree one by one.
This can be parallelized by launching as many instances as CPUs available,
each instance picking in a list of directory SWHIDs to be analyzed.
However, all instances should not access the ``archive/`` folder of the same mountpoint:
due to the FUSE architecture, and SwhFS being implemented in Python,
when running even a dozen instances SwhFS might become a bottleneck.
We instead advise you create one mountpoint per running instance of your scanner.

This can be simplified by using the :class:`swh.fuse.fuse.SwhFsTmpMount` context manager
from your batch manager, which is especially useful to dispatch work from a Python script.
In that case, be careful to also disable on-disk
caching entirely, using the ``in-memory`` and ``bypass`` settings.

How to shortcut Python startup times
------------------------------------

When creating many mountpoints one should avoid calling ``swh fs mount`` repeatedly,
because each call would start a Python process and import the many libraries we need.
In that case one might instead use a main Python process
that forks to subprocesses thanks to a
`ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor>`_.

.. warning::

    Importing ``swh.fuse`` does not trigger enough Python imports.
    To avoid importing all supported data sources' dependencies,
    SwhFS imports necessary dependencies only at mounting time,
    depending on the configuration.
    Therefore, when using a ``ProcessPoolExecutor``,
    take care to mount once before launching.

    SwhFS sources include an example batch manager relying on ``ProcessPoolExecutor`` and
    ``SwhFsTmpMount``, whose worker processes avoid Python startups entirely:
    `examples/parallel_processing.py <https://gitlab.softwareheritage.org/swh/devel/swh-fuse/-/blob/master/examples/parallel_processor.py>`_.


Workaround missing permissions
------------------------------

Some Linux environments (including many HPC premises) may not allow you to mount FUSE
filesystems, even if you can install ``libfuse`` and ``fusermount3``.
In that case, we advise you gain super-powers by running your batch manager program
in a Linux namespace with the appropriate options of unshare (from the ``util-linux`` package):

::

    unshare --pid --kill-child --user --map-root-user --mount ./parallel_processor.py


See also
--------

The complete report on testing SwhFS over 10000 mountpoints and more is in the repository too, in
`benchmark/README.md <https://gitlab.softwareheritage.org/swh/devel/swh-fuse/-/blob/master/benchmark/README.md>`_.
