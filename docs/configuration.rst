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

The following sub-sections and fields can be used within the ``swh > fuse``
stanza:

- ``cache``:

  - ``metadata``: where to store the metadata cache, must have either a
    ``in-memory`` boolean entry set to true or a ``path`` string entry (with the
    corresponding disk path).
  - ``blob``: where to store the blob cache, same entries as the ``metadata``
    cache.
  - ``direntry``: how much memory should be used by the direntry cache,
    specified using a ``maxram`` entry (either as a percentage of available RAM,
    or with disk storage unit suffixes: ``B``, ``KB``, ``MB``, ``GB``).

- ``web-api``:

  - ``url``: archive API URL
  - ``auth-token``: authentication token used with the API URL

- ``json-indent``: number of spaces used to print JSON metadata files (setting
  it to ``null`` disables indentation).

If no configuration is given, default values are:

- ``cache``: all cache files are stored in ``$XDG_CACHE_HOME/swh/fuse/`` (or
  ``~/.cache/swh/fuse`` if ``XDG_CACHE_HOME`` is not set). The direntry cache
  will use at most 10% of available RAM.
- ``web-api``: URL is https://archive.softwareheritage.org/api/1/, with no
  authentication token
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


Logging
-------

The default logging level is set to ``INFO`` and can be configured through the
:ref:`shared command line interface <swh-core-cli>` via the ``-l/--log-level``
flag.

.. code:: bash

    $ swh --log-level swh.fuse:DEBUG fs mount swhfs/
