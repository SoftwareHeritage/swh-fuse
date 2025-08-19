.. _swh-fuse-config:


Configuration
=============

The configuration for the Software Heritage Filesystem resides in the
``swh > fuse`` section of the shared `YAML <https://yaml.org/>`_ configuration
file used by all Software Heritage tools, located by default at
``~/.config/swh/global.yml`` (following the `XDG Base Directory
<https://specifications.freedesktop.org/basedir-spec/latest/>`_ specification).
You can override this path on the :ref:`command line <swh-fuse-cli>` via the
``-C/--config-file`` flag.

You can choose how ``swh-fuse`` will fetch content from the archive.
The default and simplest way is to query the SWH public API.
This method can be configured with the following block:

- ``web-api``:

  - ``url``: archive API URL (:swh_web:`api/1/`)
  - ``auth-token``: (optional, but recommended) authentication token used with the API URL


``swh-fuse`` will also search for the following fields:

- ``cache``: a section that can contain:

  - ``metadata``: a dict configuring where to store the metadata cache.
    It can either contain an ``in-memory`` boolean entry, set to ``true``, or a
    ``path`` string entry, pointing to the file.
  - ``blob``: a dict configuring where to store the blob cache, with the same entries as ``metadata``.
    If the dict contains a ``bypass`` entry set to ``true``, this cache will be disabled entirely -
    this can be useful in the HPC setting (see below).
  - ``direntry``: how much memory should be used by the direntry cache,
    specified using a ``maxram`` entry (either as a percentage of available RAM,
    or with disk storage unit suffixes: ``B``, ``KB``, ``MB``, ``GB``).

- ``json-indent``: number of spaces used to print JSON metadata files.
  Setting it to ``null`` disables indentation.

Example
-------

Here is a full ``~/.config/swh/global.yml`` equivalent to the default configuration:

.. code:: yaml

    swh:
      fuse:
        cache:
          metadata:
            path: "/home/user/.cache/swh/fuse/metadata.sqlite"
          blob:
            path: "/home/user/.cache/swh/fuse/blob.sqlite"
          direntry:
            maxram: "10%"
        web-api:
          url: "https://archive.softwareheritage.org/api/1/"
          auth-token: "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2..."
        json-indent: 2

Logging
-------

The default logging level is set to ``INFO`` and can be configured with the
``SWH_LOG_LEVEL`` environment variable, or through the
:ref:`shared command line interface <swh-core-cli>` via the ``-l/--log-level``
flag.

.. code:: bash

    $ swh --log-level swh.fuse:DEBUG fs mount swhfs/ -f


.. _swh-fuse-config-graph:

Faster file system traversal with a local compressed graph
----------------------------------------------------------

In order to traverse the folder hierarchy much faster,
connect to a :ref:`compressed graph <swh-graph>`
via its :ref:`gRPC API <swh-graph-grpc-api>`.
To do so, install with the ``hpc`` dependency group::

    $ pip install swh-fuse[hpc]

Then, this can be enabled with the following configuration section:

- ``graph``:

  - ``grpc-url``: URL to the graph's :ref:`gRPC server <swh-graph-grpc-api>`.

If that server instance will only be used for ``swh-fuse``,
since version 6.7.2 of ``swh-graph``
you can use the ``--direction=forward`` option when starting the gRPC server
and you do not need any ``graph*transposed*`` files.

.. note::

  If you don't need to read revision and releases information (that we usually put in
  ``meta.json``),
  then you also do not need to download/store the whole compressed graph.
  The following files are enough, halving the required storage:

  * graph.ef
  * graph.graph
  * graph-labelled.ef
  * graph-labelled.labeloffsets
  * graph-labelled.labels
  * graph-labelled.properties
  * graph.labels.fcl.bytearray
  * graph.labels.fcl.pointers
  * graph.labels.fcl.properties
  * graph.node2swhid.bin
  * graph.node2type.bin
  * graph.properties
  * graph.property.content.is_skipped.bits
  * graph.property.content.length.bin
  * graph.pthash
  * graph.pthash.order

.. _swh-fuse-config-teaser-graph-webapi:

Sample configuration: teaser graph + WebAPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the following configuration,
``swh-fuse`` will connect to a local graph gRPC API when creating its folders structure.
Files' content will be downloaded from our Web API.
This also switches to a volatile ``metadata`` cache,
because it can be provided quickly by the graph.

.. code:: yaml

    swh:
      fuse:
        cache:
          metadata:
            in-memory: true
          blob:
            path: "/path/to/cache/blob.sqlite"
        graph:
          grpc-url: localhost:50091
        web-api:
          auth-token: "yhbGcOiJI1z1NiIsInR5CIgOiAiSlduIiWia2..."


.. note::

  The way we encode symbolic links requires an access to the contents storage
  (cf. :py:func:`swh.model.git_objects.directory_git_object`),
  so in that setting source tree traversals can still cause accesses to the Web API.

.. _swh-fuse-config-file-download:

Configuring files' content download
-----------------------------------

What follows requires the ``hpc`` dependency group::

    $ pip install swh-fuse[hpc]

You can configure how ``swh-fuse`` will download files' content with the following section:

- ``content``:

  - ``storage``: an usual :ref:`storage <swh-storage>` configuration, like:

    - ``cls: remote``
    - ``url: http://localhost:8080``

  - ``objstorage``: an usual :ref:`objstorage <swh-objstorage>` configuration, like:

    - ``cls: remote``
    - ``url: http://localhost:8080``

``objstorage`` is optional,
as the ``storage`` service may be able to provide files' contents,
but this will probably be slower.

When ``objstorage`` is provided,
``storage`` will be called only to match SWHIDs with contents' hashes set:
you'll probably want to set ``cls: digestmap``.
That class is provided by the package :ref:`swh.digestmap <swh-digestmap>`,
installed along the HPC dependency group.
It has been developed for that case and will be the fastest back-end.

.. _swh-fuse-config-teaser-graph-s3:

Sample configuration: teaser graph + S3
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the following configuration,
``swh-fuse`` will connect to a local graph gRPC API when creating its folders structure.
Files' contents will be downloaded from our S3 mirror
(cf. :py:mod:`swh.objstorage.backends.http`:)
but cached locally to speed up repeated access to the same files.
This can be useful to test on your own machine,
using a :ref:`teaser dataset <swh-export-list>`
and its corresponding :ref:`digestmap <swh-digestmap>`.
To ensure the digestmap implementation is available,
invoke ``pip install swh-digestmap``.

.. code:: yaml

    swh:
      fuse:
        cache:
          metadata:
            in-memory: true
          blob:
            path: "/path/to/cache/blob.sqlite"
        graph:
          grpc-url: localhost:50091
        content:
          storage:
            cls: digestmap
            path: /home/user/graphs/digestmap-folder
          objstorage:
            cls: http
            url: https://softwareheritage.s3.amazonaws.com/content/
            compression: gzip
            retry:
              total: 3
              backoff_factor: 0.2
              status_forcelist:
                - 404
                - 500

.. _swh-fuse-config-hpc:

Sample configuration: Large-scale access on a dedicated HPC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you plan to use ``swh-fuse`` on a dedicated cluster containing an archive replica
(as in the `CodeCommons <https://codecommons.org/>`_ project),
you can connect ``swh-fuse`` to a compressed graph and also to local
:ref:`storage <swh-storage>` and :ref:`objstorage <swh-objstorage>`
instances as follows.
In that case we can disable the cache entirely,
to save memory on the mounting system.

.. code:: yaml

    swh:
      fuse:
        cache:
          metadata:
            in-memory: true
          blob:
            bypass: true
        graph:
          grpc-url: swh-graph-grpc.local:50091
        content:
          storage:
            cls: remote
            path: http://storage.local
            enable_requests_retry: true
          objstorage:
            cls: remote
            url: http://objstorage.local
            enable_requests_retry: true


Monitoring
----------

When using a compressed graph or content back-ends,
``swh-fuse`` sends `statsd <https://github.com/statsd/statsd>`_ metrics
to ``localhost:8125`` by default.
This can be changed from `environment variables <https://statsd.readthedocs.io/en/stable/configure.html#from-the-environment>`_,
in particular ``STATSD_HOST`` and ``STATSD_PORT``.

Expect the following metrics:

* ``swhfuse_waiting_graph`` a timer measuring how long we are waiting for the graph backend
* ``swhfuse_waiting_storage`` a timer measuring how long we are waiting for the storage backend
* ``swhfuse_waiting_objstorage`` a timer measuring how long we are waiting for the objstorage (contents) backend
* ``swhfuse_get_blob`` a counter of calls to storage/objstorage
* ``swhfuse_blob_not_in_storage`` a counter of failed calls to storage (including objects not found)
* ``swhfuse_blob_not_in_objstorage`` a counter of failed calls to objstorage (including objects not found)
