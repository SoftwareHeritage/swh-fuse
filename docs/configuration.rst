.. _swh-fuse-config:


Configuration
=============

The configuration for the Software Heritage Filesystem resides in the
``swh > fuse`` section of the shared `YAML <https://yaml.org/>`_ configuration
file used by all Software Heritage tools, located by default at
``~/.config/swh/global.yml``.

The configuration file location is subject to the `XDG Base Directory
<https://wiki.archlinux.org/index.php/XDG_Base_Directory>`_ specification as
well as explicitly overridden on the :ref:`command line <swh-fuse-cli>` via the
``-C/--config-file`` flag.

You can choose how `swh-fuse` will fetch content from the archive.
The fastest way relies on a :ref:`compressed graph <swh-graph>`
and an :ref:`objstorage <swh-objstorage>` close to your server.
To choose this method, define the following block:

- ``graph``:
  - ``grpc-url``: URL to the graph's :ref:`gRPC server <swh-graph-grpc-api>`.
  - ``objstorage``: an usual `swh-objstorage` configuration block.
    When using a local instance, you should include these two entries:
    - ``cls: remote``
    - ``url: http://127.0.0.1:15003``
  - ``hashes-path``: path to ORC files providing complete hashes by SWHID.

Otherwise, the simplest (but slow) method is to query the SWH public API.
You can configure this method as follows:

- ``web-api``:
  - ``url``: archive API URL
  - ``auth-token``: authentication token used with the API URL

`swh-fuse` will also search for the following options:

- ``cache``:

  - ``metadata``: where to store the metadata cache, must have either a
    ``in-memory`` boolean entry set to true or a ``path`` string entry (with the
    corresponding disk path).
  - ``blob``: where to store the blob cache, same entries as the ``metadata``
    cache.
  - ``direntry``: how much memory should be used by the direntry cache,
    specified using a ``maxram`` entry (either as a percentage of available RAM,
    or with disk storage unit suffixes: ``B``, ``KB``, ``MB``, ``GB``).

- ``json-indent``: number of spaces used to print JSON metadata files (setting
  it to ``null`` disables indentation).

If no configuration is given, default values are:

- ``cache``: all cache files are stored in ``$XDG_CACHE_HOME/swh/fuse/`` (or
  ``~/.cache/swh/fuse`` if ``XDG_CACHE_HOME`` is not set). The direntry cache
  will use at most 10% of available RAM.
- ``web-api``: URL is :swh_web:`api/1/`, with no authentication token
- ``json-indent``: 2 spaces.


Example
-------

Here is a full ``~/.config/swh/global.yml`` example, showcasing different cache
storage strategies (in-memory for metadata, on-disk for blob, 20% RAM for
direntry), using the default Web API service:

.. code:: yaml

    swh:
      fuse:
        cache:
          metadata:
            in-memory: true
          blob:
            path: "/path/to/cache/blob.sqlite"
          direntry:
            maxram: 20%
        web-api:
          url: "https://archive.softwareheritage.org/api/1/"
          auth-token: eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJhMTMxYTQ1My1hM2IyLTQwMTUtO...


TODO: graph/storage example

Logging
-------

The default logging level is set to ``INFO`` and can be configured through the
:ref:`shared command line interface <swh-core-cli>` via the ``-l/--log-level``
flag.

.. code:: bash

    $ swh --log-level swh.fuse:DEBUG fs mount swhfs/
