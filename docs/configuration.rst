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

The following sub-sections and fields can be used within the `swh > fuse`
stanza:

- ``cache``:

  - ``metadata``: where to store the metadata cache, must have either a
    ``in-memory`` boolean entry or a ``path`` string entry (with the
    corresponding disk path)
  - ``blob``: where to store the blob cache, same entries as the ``metadata``
    cache

- ``web-api``:

  - ``url``: archive API URL
  - ``auth-token``: authentication token used with the API URL

If no configuration is given, default values are:

- ``cache``: all cache files are stored in ``$XDG_CACHE_HOME/swh/fuse/`` (or
  ``~/.cache/swh/fuse`` if ``XDG_CACHE_HOME`` is not set)
- ``web-api``: default URL is <https://archive.softwareheritage.org/api/1/>,
  with no authentication token


Example
-------

Here is a full ``~/.config/swh/global.yml`` example, showcasing different cache
storage strategies (in-memory for metadata and on-disk for blob), using the
default Web API service:

.. code:: yaml

    swh:
      fuse:
        cache:
          metadata:
            in-memory: true
          blob:
            path: "/path/to/cache/blob.sqlite"
        web-api:
          url: "https://archive.softwareheritage.org/api/1/"
          auth-token: null


Logging
-------

The default logging level is set to ``INFO`` and can be configured through the
:ref:`shared command line interface <swh-core-cli>` via the ``-l/--log-level``
flag.

.. code:: bash

    $ swh --log-level swh.fuse:DEBUG fs mount swhfs/
